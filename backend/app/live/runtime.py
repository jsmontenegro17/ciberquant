from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal, localcontext
from collections import defaultdict
from sqlalchemy import select
from ..models import ScannerWatchItem, ScannerWatchlist, ScannerEvent, ScannerOutcome, LiveSubscription, now
from ..features.serialization import serialize, CALC_CONTEXT
from ..strategies.schemas import VersionCreate
from ..strategies.dsl import evaluate, Truth
from ..strategies.repository import audit
from ..market_data.normalization import Dataset, identity, utc
from ..market_data.quality import validate_candle
from ..market_data.timeframe import duration
from ..config import settings
from .features import IncrementalFeatures
from .persistence import persist_closed
from .policy import compatibility
from .paper import PaperObservation
from .paper_config import resolve_paper_config
from . import LIVE_DATA_ENGINE_VERSION, SCANNER_ENGINE_VERSION


class Subscription:
    def __init__(self, provider, history, dataset):
        self.provider, self.history, self.dataset = provider, history, dataset
        self.features = {}
        self.paper = []

    def feature_state(self, version):
        if version.id not in self.features:
            definition = VersionCreate(**{k: getattr(version, k) for k in VersionCreate.model_fields})
            state = IncrementalFeatures(definition.indicator_specs)
            for candle in self.history:
                state.update(candle)
            self.features[version.id] = (state, definition)
        return self.features[version.id]


class ScannerRuntime:
    """One worker owner. Exceptions clear incremental state before reconnect/bootstrap."""

    def __init__(self, factory, provider_factory):
        self.factory, self.provider_factory = factory, provider_factory
        self.subscriptions, self.retry = {}, {}

    def recover_pending(self):
        with self.factory() as s:
            pending = s.scalars(
                select(ScannerEvent)
                .outerjoin(ScannerOutcome, ScannerOutcome.scanner_event_id == ScannerEvent.id)
                .where(ScannerEvent.state == "MATCH", ScannerOutcome.id.is_(None))
            )
            for e in pending:
                s.add(
                    ScannerOutcome(
                        scanner_event_id=e.id, result="UNAVAILABLE", evidence={"reason": "Worker restarted; no reconstructed live fills"}
                    )
                )
            s.commit()

    def close(self):
        for sub in self.subscriptions.values():
            sub.provider.close()
        self.subscriptions.clear()

    def abandon(self, sub):
        if sub is None:
            return
        with self.factory() as s:
            for paper in sub.paper:
                event = s.get(ScannerEvent, paper.event_id)
                existing = s.scalar(select(ScannerOutcome.id).where(ScannerOutcome.scanner_event_id == paper.event_id))
                if event is not None and existing is None:
                    s.add(
                        ScannerOutcome(
                            scanner_event_id=paper.event_id,
                            result="UNAVAILABLE",
                            evidence={"reason": "Subscription interrupted; no reconstructed live fill"},
                        )
                    )
            s.commit()

    def cycle(self, received_at=None):
        received_at = received_at or now()
        with self.factory() as s:
            grouped = defaultdict(list)
            for item in s.scalars(select(ScannerWatchItem).join(ScannerWatchlist).where(ScannerWatchlist.enabled.is_(True))):
                if item.enabled:
                    grouped[item.subscription_key].append(item.id)
                else:
                    item.state, item.updated_at = "PAUSED", received_at
                    item.latest = {"state": "PAUSED"}
            s.commit()
        for key in list(self.subscriptions):
            if key not in grouped:
                sub = self.subscriptions.pop(key)
                self.abandon(sub)
                sub.provider.close()
        for key, ids in grouped.items():
            attempt, retry_at, conflict = self.retry.get(key, (0, received_at, False))
            if conflict or received_at < retry_at:
                continue
            try:
                self.process(key, ids, received_at, attempt)
            except Exception as exc:
                sub = self.subscriptions.pop(key, None)
                if sub:
                    self.abandon(sub)
                    try:
                        sub.provider.close()
                    except Exception:
                        pass
                code = (
                    "DATA_CONFLICT"
                    if isinstance(exc, ValueError) and str(exc) == "DATA_CONFLICT"
                    else "INSUFFICIENT_HISTORY"
                    if isinstance(exc, ValueError)
                    else "PROVIDER_UNAVAILABLE"
                )
                attempt += 1
                self.retry[key] = (attempt, received_at + timedelta(seconds=min(60, 2 ** min(attempt, 6))), code == "DATA_CONFLICT")
                with self.factory() as s:
                    for item in s.scalars(select(ScannerWatchItem).where(ScannerWatchItem.id.in_(ids))):
                        item.state = "INSUFFICIENT_HISTORY" if code == "INSUFFICIENT_HISTORY" else "PROVIDER_DOWN"
                        item.latest = {"state": item.state, "error": code, "research_signal": "No order sent"}
                        item.updated_at = received_at
                    health = s.get(LiveSubscription, key)
                    if health:
                        if health.status != "DISCONNECTED":
                            audit(s, item.user_id, "PROVIDER_STATE_CHANGED", "live_subscription", None)
                        health.status, health.updated_at = "DISCONNECTED", received_at
                        health.health = {"error": code, "reconnect_count": attempt, "last_received": received_at.isoformat()}
                    s.commit()

    def process(self, key, ids, received_at, attempt):
        with self.factory() as s:
            items = list(s.scalars(select(ScannerWatchItem).where(ScannerWatchItem.id.in_(ids))))
            first = items[0]
            dataset = Dataset(**first.dataset)
            saved = s.get(LiveSubscription, key)
            if saved is None:
                saved = LiveSubscription(key=key, provider=first.provider, dataset=first.dataset, status="DISCONNECTED")
                s.add(saved)
                s.commit()
            sub = self.subscriptions.get(key)
            if sub is None:
                provider = self.provider_factory(s, first.provider, dataset)
                try:
                    history = provider.bootstrap(dataset)
                    if not history or len(history) > settings.feature_engine_max_source_candles:
                        raise ValueError("INSUFFICIENT_HISTORY")
                    logical = history[-1].close_time if first.provider == "REPLAY" else received_at
                    history = persist_closed(
                        s,
                        dataset,
                        history,
                        first.provider,
                        "REPLAY" if first.provider == "REPLAY" else "LIVE",
                        logical,
                        received_at,
                        "BOOTSTRAP",
                    )
                    # Strict chronology checked by frozen feature generator during bootstrap.
                    sub = Subscription(provider, history, dataset)
                    self.subscriptions[key] = sub
                except Exception:
                    provider.close()
                    raise
            active = []
            for item in items:
                version, policy = compatibility(s, item.user_id, item.strategy_version_id, dataset)
                if policy["lifecycle"] != "TESTING":
                    item.state, item.updated_at = "PAUSED", received_at
                    item.latest = serialize({**policy, "state": "PAUSED"})
                    continue
                if not item.research_mode and not policy["compatible"]:
                    item.state = (
                        "SUSPENDED_DEGRADED"
                        if "DEGRADED" in (policy["validation_state"], policy["dataset_validation_state"])
                        else "UNAVAILABLE"
                    )
                    item.latest = serialize({**policy, "state": item.state})
                    item.updated_at = received_at
                    continue
                state, definition = sub.feature_state(version)
                active.append((item, version, policy, state, definition))
            frame = sub.provider.poll(dataset)
            utc(frame.server_time)
            if frame.mode != ("REPLAY" if first.provider == "REPLAY" else "LIVE"):
                raise ValueError("INVALID_PROVIDER_MODE")
            if frame.forming is not None and (
                identity(frame.forming) != tuple(dataset.model_dump().values()) or validate_candle(frame.forming)
            ):
                raise ValueError("INVALID_FORMING_CANDLE")
            if frame.status != "CONNECTED":
                raise ConnectionError("Provider disconnected")
            if frame.payout is not None and (not frame.payout.is_finite() or not 0 < frame.payout <= 100):
                raise ValueError("Invalid provider payout")
            closed = persist_closed(s, dataset, list(frame.closed), first.provider, frame.mode, frame.server_time, received_at)
            last = sub.history[-1]
            new = [c for c in closed if c.open_time > last.open_time]
            # Never replay missed broker signals as LIVE: latest genuinely fresh close only.
            for c in new:
                if len(sub.history) >= settings.feature_engine_max_source_candles:
                    raise ValueError("Live canonical history cap exceeded")
                sub.history.append(c)
                for state, _ in sub.features.values():
                    state.update(c)
                pending = []
                for paper in sub.paper:
                    outcome = paper.update(c)
                    if outcome is None:
                        pending.append(paper)
                    else:
                        s.add(ScannerOutcome(scanner_event_id=paper.event_id, result=outcome["result"], evidence=serialize(outcome)))
                sub.paper = pending
            last = sub.history[-1]
            stale = frame.server_time - last.close_time > duration(dataset.timeframe) * settings.live_stale_factor
            delta = None if first.provider in ("MT5", "REPLAY") else (frame.server_time - received_at).total_seconds()
            health = dict(
                provider=first.provider,
                status="DEGRADED" if stale else "CONNECTED",
                last_closed_candle=last.close_time,
                server_time=frame.server_time,
                local_utc_time=received_at,
                last_received=received_at,
                clock_delta_seconds=delta,
                clock_source="REPLAY_LOGICAL" if frame.mode == "REPLAY" else "LOCAL_UTC_PROXY" if first.provider == "MT5" else "PROVIDER",
                clock_warning=delta is not None and abs(delta) > settings.live_clock_drift_seconds,
                reconnect_count=attempt,
                market_open=frame.market_open,
                mode=frame.mode,
                error=None,
            )
            health["provider_metadata"] = getattr(sub.provider, "status_metadata", None)
            if saved.status != health["status"]:
                audit(s, first.user_id, "PROVIDER_STATE_CHANGED", "live_subscription", None)
            saved.status, saved.health, saved.updated_at = health["status"], serialize(health), received_at
            saved.snapshot = serialize(
                dict(
                    last_closed=asdict(last),
                    forming=asdict(frame.forming) if frame.forming else None,
                    forming_state="FORMING" if frame.forming else None,
                    payout=frame.payout,
                    mode=frame.mode,
                )
            )
            for item, version, policy, state, definition in active:
                item.updated_at = received_at
                if stale or frame.market_open is False:
                    item.state = "STALE" if stale else "UNAVAILABLE"
                    item.latest = serialize({**policy, "state": item.state, "health": health, "mode": frame.mode})
                    continue
                if not new:
                    if item.latest is None:
                        item.state = "INSUFFICIENT_HISTORY"
                    continue
                row = state.rows[-1]
                truth, context = evaluate(definition.condition_tree, state.rows, row["close_time"])
                result = "MATCH" if truth == Truth.TRUE else "NO_MATCH" if truth == Truth.FALSE else "INSUFFICIENT_HISTORY"
                paper_config = resolve_paper_config(
                    research_mode=item.research_mode,
                    provider_payout=frame.payout,
                    validation_payout=policy["validation_payout"],
                    validation_expiry=policy["expiry_bars"],
                    research_payout=item.research_payout,
                    research_expiry=item.research_expiry,
                )
                payout, expiry = paper_config.payout, paper_config.expiry_bars
                with localcontext(CALC_CONTEXT):
                    breakeven = 100 / (1 + frame.payout / 100) if frame.payout else None
                evidence = serialize(
                    dict(
                        **{k: v for k, v in policy.items() if k != "expiry_bars"},
                        research_mode=item.research_mode,
                        mode=frame.mode,
                        state=result,
                        research_direction=version.trade_direction,
                        signal_time=last.close_time,
                        signal_open=last.open_time,
                        current_payout=frame.payout,
                        current_break_even=breakeven,
                        payout_warning=bool(
                            frame.payout is not None
                            and policy["validation_payout"] is not None
                            and frame.payout < policy["validation_payout"]
                        ),
                        payout_snapshot=payout,
                        payout_source=paper_config.payout_source,
                        payout_product=(health.get("provider_metadata") or {}).get("product"),
                        expiry_bars=expiry,
                        expiry_source=paper_config.expiry_source,
                        validation_expiry=policy["expiry_bars"],
                        research_payout=item.research_payout,
                        research_expiry=item.research_expiry,
                        expected_entry_model="NEXT_CANDLE_OPEN",
                        next_entry_boundary=last.open_time + duration(dataset.timeframe),
                        entry_price=None,
                        latency_ms=int((received_at - last.close_time).total_seconds() * 1000) if frame.mode == "LIVE" else None,
                        signal_context=context,
                        features=row["features"],
                        health=health,
                    )
                )
                item.state, item.latest = "ACTIVE", evidence
                exists = s.scalar(
                    select(ScannerEvent.id).where(
                        ScannerEvent.watch_item_id == item.id,
                        ScannerEvent.strategy_version_id == version.id,
                        ScannerEvent.signal_time == last.close_time,
                        ScannerEvent.state == result,
                    )
                )
                if exists is not None:
                    continue
                event = ScannerEvent(
                    user_id=item.user_id,
                    watch_item_id=item.id,
                    strategy_version_id=version.id,
                    dataset=item.dataset,
                    scanner_engine_version=SCANNER_ENGINE_VERSION,
                    feature_engine_version=version.feature_engine_version,
                    strategy_dsl_version=version.strategy_dsl_version,
                    live_data_engine_version=LIVE_DATA_ENGINE_VERSION,
                    signal_candle_id=last.candle_id,
                    signal_time=last.close_time,
                    state=result,
                    mode=frame.mode,
                    direction=version.trade_direction,
                    signal_context=serialize(context),
                    validation_state_snapshot=policy["validation_state"],
                    current_payout=frame.payout,
                    evidence=evidence,
                    provider_timestamp=frame.server_time,
                    received_at=received_at,
                )
                s.add(event)
                s.flush()
                if result == "MATCH":
                    audit(s, item.user_id, "SCANNER_MATCH", "scanner_event", event.id)
                    if payout is not None and expiry is not None:
                        sub.paper.append(
                            PaperObservation(event.id, last, version.trade_direction, expiry, payout, evidence["payout_source"])
                        )
                    else:
                        s.add(
                            ScannerOutcome(
                                scanner_event_id=event.id, result="UNAVAILABLE", evidence={"reason": "No paper payout/expiry assumption"}
                            )
                        )
            s.commit()
            self.retry[key] = (attempt, received_at, False)
