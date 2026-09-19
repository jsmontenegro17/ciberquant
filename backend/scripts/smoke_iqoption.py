"""Explicit local PRACTICE-only IQ smoke. No secrets/raw profile/IDs in output.

Run from backend: python -m scripts.smoke_iqoption --product binary --seconds 150
Uses an isolated temporary SQLite scanner database, never the user's accounts/ledger.
"""

import argparse
import json
import time
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings
from app.db import Base
from app.models import User, Strategy, ScannerWatchlist, ScannerWatchItem, ScannerEvent, LedgerEntry, Candle
from app.strategies.schemas import VersionCreate
from app.strategies.repository import create_version
from app.strategies.dsl import digest
from app.live.iqoption import IQOptionReadOnlyProvider, UPSTREAM_SHA
from app.live.runtime import ScannerRuntime
from scripts.iq_diagnostics import HistoryTracker


def emit(value):
    print(json.dumps(value, default=str), flush=True)


def main(soak=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", choices=["turbo", "binary"], default=settings.iqoption_product)
    parser.add_argument("--seconds", type=int, default=420 if soak else 150)
    parser.add_argument("--regular-symbol", default=None, help="Explicit discovered open REGULAR symbol for reproducible diagnostics")
    parser.add_argument("--otc-symbol", default=None)
    args = parser.parse_args()
    if not 65 <= args.seconds <= (900 if soak else 300):
        raise SystemExit("Invalid bounded test duration")
    if not settings.enable_iqoption_experimental or settings.iqoption_balance != "PRACTICE":
        raise SystemExit("IQ smoke requires explicit flag and PRACTICE")
    provider = None
    runtime = None
    db_engine = None
    tracker = HistoryTracker()
    try:
        provider = IQOptionReadOnlyProvider(
            email=settings.iqoption_email.get_secret_value(),
            password=settings.iqoption_password.get_secret_value(),
            ssid=settings.iqoption_ssid.get_secret_value(),
            balance=settings.iqoption_balance,
            product=args.product,
            timeout=settings.iqoption_timeout_seconds,
            history_observer=tracker.observe,
        )
        emit(
            {
                "stage": "AUTH",
                "result": "PASS",
                "mode": "PRACTICE",
                "profile_verified": provider.status_metadata["profile_verified"],
                "upstream_sha": UPSTREAM_SHA,
                "product": args.product,
            }
        )
        states = provider.asset_status()
        datasets = provider.assets()
        selected = []
        emit(
            {
                "stage": "DISCOVERY",
                "REGULAR": sum(a["market_type"] == "REGULAR" for a in states),
                "OTC": sum(a["market_type"] == "OTC" for a in states),
                "open_REGULAR": sum(a["market_type"] == "REGULAR" and a["open"] for a in states),
                "open_OTC": sum(a["market_type"] == "OTC" and a["open"] for a in states),
            }
        )
        for market in ("REGULAR", "OTC"):
            candidates = [a for a in states if a["market_type"] == market and a["open"]]
            if not candidates:
                emit({"stage": "ASSET", "market_type": market, "result": "BLOCKED_EXTERNAL", "reason": "NO " + market + " CURRENTLY OPEN"})
                if market == "OTC":
                    return 2
                continue
            chosen = next((a for a in candidates if a["symbol"] in ("EURUSD", "EURUSD-OTC")), candidates[0])
            if market == "REGULAR" and args.regular_symbol:
                chosen = next((a for a in candidates if a["symbol"] == args.regular_symbol), None)
                if chosen is None:
                    raise ValueError("IQ_REQUESTED_REGULAR_NOT_OPEN")
            if market == "OTC" and args.otc_symbol:
                chosen = next((a for a in candidates if a["symbol"] == args.otc_symbol), None)
                if chosen is None:
                    raise ValueError("IQ_REQUESTED_OTC_NOT_OPEN")
            dataset = next(d for d in datasets if d.symbol == chosen["symbol"])
            rows = provider.recent_closed(dataset, 20)
            if len(rows) < 20:
                raise ValueError("IQ_SMOKE_INSUFFICIENT_CANDLES")
            # This smoke freezes its own explicit canonical origin. Production requires env origin.
            provider._origin = rows[0].open_time
            history = provider.bootstrap(dataset)
            selected.append(
                dict(
                    dataset=dataset,
                    last=history[-1].open_time,
                    forming=False,
                    closed=False,
                    seen={},
                    new_closes=set(),
                    gaps=0,
                    payouts=set(),
                    clock=None,
                )
            )
            emit(
                {
                    "stage": "HISTORY",
                    "dataset": dataset.model_dump(),
                    "count": len(history),
                    "canonical_origin": history[0].open_time,
                    "result": "PASS",
                }
            )
        otc = next(x for x in selected if x["dataset"].market_type == "OTC")
        with TemporaryDirectory(prefix="cq-iq-smoke-") as folder:
            db_engine = create_engine("sqlite:///" + str(Path(folder) / "smoke.db"), poolclass=NullPool)
            Base.metadata.create_all(db_engine)
            factory = sessionmaker(bind=db_engine)
            with factory() as session:
                user = User(name="Read-only smoke", email="smoke@invalid.local", password_hash="no-login")
                session.add(user)
                session.flush()
                strategy = Strategy(user_id=user.id, name="IQ real read-only smoke", status="TESTING")
                session.add(strategy)
                session.commit()
                definition = VersionCreate(
                    trade_direction="CALL",
                    indicator_specs=[{"type": "EMA", "period": 3}],
                    condition_tree={
                        "left": {"type": "FIELD", "field": "close", "bars_ago": 0},
                        "operator": "GT",
                        "right": {"type": "NUMBER", "value": "0"},
                    },
                )
                version = create_version(session, strategy.id, user.id, definition)
                watch = ScannerWatchlist(user_id=user.id, name="IQ smoke")
                session.add(watch)
                session.flush()
                dataset = otc["dataset"].model_dump()
                session.add(
                    ScannerWatchItem(
                        user_id=user.id,
                        watchlist_id=watch.id,
                        strategy_version_id=version.id,
                        provider="IQOPTION",
                        dataset=dataset,
                        subscription_key=digest(dict(provider="IQOPTION", dataset=dataset)),
                        research_mode=True,
                        research_payout=Decimal("84"),
                        research_expiry=1,
                    )
                )
                session.commit()
            runtime = ScannerRuntime(factory, lambda *args: provider, diagnostic_sink=tracker.runtime_conflict)
            reconnected = False
            observations = 0
            stale_observations = 0
            last_emitted = None
            # Runtime bootstraps once from the same frozen OTC origin, then evaluates actual new closes.
            start = time.monotonic()
            while time.monotonic() - start < args.seconds:
                tracker.label = {"caller": "SCANNER_RUNTIME"}
                runtime.cycle()
                with factory() as session:
                    current_item = session.scalar(select(ScannerWatchItem))
                    stale_observations += int(current_item.state == "STALE")
                    if soak and provider._closed:
                        code = (current_item.latest or {}).get("error", "PROVIDER_UNAVAILABLE")
                        raise ValueError("IQ_SOAK_" + code)
                    event = session.scalar(select(ScannerEvent).order_by(ScannerEvent.id.desc()))
                    if event and event.id != last_emitted:
                        last_emitted = event.id
                        otc["closed"] = True
                        emit(
                            {
                                "stage": "SCANNER",
                                "signal_time": event.signal_time,
                                "market_type": event.dataset["market_type"],
                                "state": event.state,
                                "mode": event.mode,
                                "payout": event.current_payout,
                                "payout_source": event.evidence["payout_source"],
                                "expiry_source": event.evidence["expiry_source"],
                                "feature_fields": list(event.evidence["features"]),
                                "result": "PASS",
                            }
                        )
                for item in selected:
                    tracker.label = {"caller": "SOAK_DIRECT_OBSERVER"}
                    frame = provider.poll(item["dataset"])
                    if item["clock"] is not None and frame.server_time < item["clock"]:
                        raise ValueError("IQ_SOAK_CLOCK_REGRESSION")
                    item["clock"] = frame.server_time
                    if frame.payout is not None:
                        item["payouts"].add(str(frame.payout))
                    item["forming"] |= frame.forming is not None
                    for candle in frame.closed:
                        key = candle.open_time
                        prices = (candle.open, candle.high, candle.low, candle.close)
                        if key in item["seen"] and item["seen"][key] != prices:
                            emit(
                                {
                                    "stage": "DATA_CONFLICT",
                                    "detection_layer": "SOAK_DIRECT_OBSERVER",
                                    "observations": tracker.snapshots(item["dataset"], key),
                                    "symbol": item["dataset"].symbol,
                                    "market_type": item["dataset"].market_type,
                                    "candle_open": key,
                                    "provider_clock": frame.server_time,
                                    "changed_fields": [
                                        name for name, a, b in zip(("open", "high", "low", "close"), item["seen"][key], prices) if a != b
                                    ],
                                    "orders_sent": 0,
                                }
                            )
                            raise ValueError("IQ_SOAK_DATA_CONFLICT")
                        if key not in item["seen"]:
                            if item["seen"] and (key - max(item["seen"])).total_seconds() != 60:
                                item["gaps"] += 1
                            item["seen"][key] = prices
                        if key > item["last"]:
                            item["new_closes"].add(key)
                    if any(c.open_time > item["last"] for c in frame.closed):
                        item["closed"] = True
                observations += 1
                if soak and not reconnected and all(x["closed"] for x in selected) and event is not None:
                    # Deliberately interrupt the real socket; never replay missed closes as LIVE.
                    origin = provider._origin
                    runtime.close()
                    provider.close()
                    tracker.generation += 1
                    tracker.label = {"caller": "SOAK_RECONNECT_BOOTSTRAP"}
                    provider = IQOptionReadOnlyProvider(
                        email=settings.iqoption_email.get_secret_value(),
                        password=settings.iqoption_password.get_secret_value(),
                        ssid=settings.iqoption_ssid.get_secret_value(),
                        balance=settings.iqoption_balance,
                        product=args.product,
                        timeout=settings.iqoption_timeout_seconds,
                        origin=origin,
                        history_observer=tracker.observe,
                    )
                    for item in selected:
                        provider.bootstrap(item["dataset"])
                    runtime = ScannerRuntime(factory, lambda *args: provider, diagnostic_sink=tracker.runtime_conflict)
                    runtime.recover_pending()
                    reconnected = True
                    emit({"stage": "CONTROLLED_RECONNECT", "result": "PASS", "mode": "PRACTICE", "orders_sent": 0})
                enough = all(len(x["new_closes"]) >= 3 for x in selected) and reconnected if soak else True
                if enough and all(x["forming"] and x["closed"] for x in selected) and event is not None:
                    break
                time.sleep(2)
            for item in selected:
                emit(
                    {
                        "stage": "REALTIME",
                        "symbol": item["dataset"].symbol,
                        "market_type": item["dataset"].market_type,
                        "forming": item["forming"],
                        "new_closed": item["closed"],
                        "result": "PASS" if item["forming"] and item["closed"] else "FAIL",
                    }
                )
            with factory() as session:
                evaluated = session.scalar(select(func.count()).select_from(ScannerEvent)) > 0
                assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0
            success = evaluated and all(x["forming"] and x["closed"] for x in selected)
            if soak:
                success = success and reconnected and all(len(x["new_closes"]) >= 3 and x["gaps"] == 0 for x in selected)
                with factory() as session:
                    counts = dict(session.execute(select(ScannerEvent.state, func.count()).group_by(ScannerEvent.state)).all())
                    duplicate_candles = session.scalar(select(func.count(Candle.id) - func.count(func.distinct(Candle.open_time))))
                    duplicate_events = session.scalar(
                        select(func.count(ScannerEvent.id) - func.count(func.distinct(ScannerEvent.signal_time)))
                    )
                    success = success and duplicate_candles == 0 and duplicate_events == 0
                emit(
                    {
                        "stage": "SOAK",
                        "observations": observations,
                        "reconnect": reconnected,
                        "scanner_counts": counts,
                        "duplicate_closed_count": duplicate_candles,
                        "duplicate_event_count": duplicate_events,
                        "stale_observations": stale_observations,
                        "datasets": [
                            dict(
                                symbol=x["dataset"].symbol,
                                market_type=x["dataset"].market_type,
                                closed_count=len(x["new_closes"]),
                                gaps=x["gaps"],
                                payout_snapshots=sorted(x["payouts"]),
                                last_provider_clock=x["clock"],
                            )
                            for x in selected
                        ],
                        "orders_sent": 0,
                        "result": "PASS" if success else "FAIL",
                    }
                )
            # Windows must release pooled SQLite handles before temporary-directory cleanup.
            runtime.close()
            runtime = None
            provider.close()
            db_engine.dispose()
            db_engine = None
            emit(
                {
                    "stage": "FINAL",
                    "date": datetime.now(timezone.utc),
                    "product": args.product,
                    "capabilities": provider.capabilities,
                    "orders_sent": 0,
                    "result": "PASS" if success else "FAIL",
                    "regular_tested": any(x["dataset"].market_type == "REGULAR" for x in selected),
                }
            )
            return 0 if success else 1
    except Exception as exc:
        # Never print traceback/remote error text, which can include authentication/profile data.
        code = str(exc) if re.fullmatch(r"IQ_[A-Z0-9_]{1,80}", str(exc)) else "IQ_SMOKE_FAILED"
        emit({"stage": "FINAL", "result": "FAIL", "error_type": type(exc).__name__, "error_code": code, "orders_sent": 0})
        return 1
    finally:
        tracker.report()
        if runtime:
            try:
                runtime.close()
            except Exception:
                pass
        if provider:
            try:
                provider.close()
            except Exception:
                pass
        if db_engine:
            db_engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
