"""Read-only projections over canonical evidence. No engine execution or financial writes."""

from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import defer
from .deps import current_user, db
from .research import record, page
from .scanner import item_view
from ..models import (
    Strategy,
    StrategyVersion,
    Candle,
    BacktestRun,
    ValidationRun,
    ValidationSegment,
    ScannerWatchItem,
    ScannerEvent,
    ScannerOutcome,
    LiveSubscription,
    LiveObservation,
    now,
)
from ..strategies.repository import owned
from ..market_data.normalization import Dataset, stored_utc
from ..market_data.repository import coverage
from ..config import settings

router = APIRouter(prefix="/workspace", tags=["workspace"])


def context(
    strategy_version_id: int = Query(gt=0),
    source: str = Query(min_length=1),
    broker: str = Query(min_length=1),
    symbol: str = Query(min_length=1),
    market_type: str = Query(pattern="^(REGULAR|OTC)$"),
    timeframe: str = Query(min_length=1),
):
    try:
        return strategy_version_id, Dataset(source=source, broker=broker, symbol=symbol, market_type=market_type, timeframe=timeframe)
    except ValueError:
        raise HTTPException(422, "Invalid dataset context") from None


def identity(model, dataset):
    return [model.dataset[k].as_string() == v for k, v in dataset.model_dump().items()]


def authorize(session, uid, ctx):
    vid, dataset = ctx
    version = session.get(StrategyVersion, vid)
    if version is None:
        raise HTTPException(404, "Resource not found")
    strategy = owned(session, Strategy, version.strategy_id, uid)
    return version, strategy, dataset


def scoped(model, uid, vid, dataset):
    return [model.user_id == uid, model.strategy_version_id == vid, *identity(model, dataset)]


def compact(run, direction=None):
    # Avoid loading equity curves/full frozen snapshots in summaries.
    keys = (
        "id",
        "strategy_version_id",
        "status",
        "dataset",
        "created_at",
        "completed_at",
        "feature_engine_version",
        "strategy_dsl_version",
        "backtest_engine_version",
        "payout_percent",
        "expiry_bars",
        "as_of_candle_id",
        "error_summary",
    )
    data = {k: getattr(run, k) for k in keys}
    data["trade_direction"] = direction
    if isinstance(run, BacktestRun):
        data.update(
            kind="MANUAL_BACKTEST",
            purpose=run.purpose,
            metrics=run.metrics,
            start=run.signal_start,
            end=run.signal_end,
            href=f"/backtests/{run.id}",
            payout_source="FIXED_BACKTEST_ASSUMPTION",
            expiry_source="BACKTEST_CONFIG",
        )
    else:
        data.update(
            kind="HISTORICAL_VALIDATION",
            verdict=run.verdict,
            metrics=run.test_summary,
            development_summary=run.development_summary,
            validation_engine_version=run.validation_engine_version,
            start=run.overall_start,
            end=run.overall_end,
            test_revealed_at=run.test_revealed_at,
            href=f"/validation/{run.id}",
            payout_source="VALIDATION_ASSUMPTION",
            expiry_source="VALIDATION_ASSUMPTION",
        )
    from ..features.serialization import serialize

    return serialize({k: stored_utc(v) if isinstance(v, datetime) else v for k, v in data.items()})


def light(model):
    q = select(model).options(defer(model.config_snapshot))
    if model is BacktestRun:
        q = q.options(defer(model.equity_curve), defer(model.strategy_snapshot))
    return q


def stage(name, status, href, evidence=None, date=None):
    summary = "No matching evidence"
    if evidence:
        if name == "DATA":
            summary = f"{evidence['candle_count']} closed candles"
        elif name == "FEATURES":
            summary = evidence["engine"]
        elif name == "STRATEGY":
            summary = f"StrategyVersion #{evidence['id']} · v{evidence['version']}"
        elif name == "BACKTEST":
            summary = f"Manual #{evidence['id']} · {evidence['status']} · resolved {(evidence.get('metrics') or {}).get('resolved_trades', 'unavailable')}"
        elif name == "VALIDATION":
            summary = f"Validation #{evidence['id']} · {evidence['status']} · {evidence['verdict']}"
        elif name == "SCANNER":
            summary = " / ".join(f"#{i['id']} {i['state']} {'RESEARCH' if i['research_mode'] else 'NORMAL'}" for i in evidence["items"])
        elif name == "PAPER":
            summary = f"Outcome #{evidence['id']} · {evidence['result']}"
    return dict(
        name=name,
        status=status,
        href=href,
        evidence=evidence,
        date=stored_utc(date) if isinstance(date, datetime) else date,
        summary=summary,
    )


@router.get("/overview")
def overview(ctx=Depends(context), user=Depends(current_user), session=Depends(db)):
    version, strategy, dataset = authorize(session, user.id, ctx)
    data = coverage(session, dataset)
    latest = {}
    for model, key in ((BacktestRun, "manual"), (ValidationRun, "validation")):
        conditions = scoped(model, user.id, version.id, dataset)
        if model is BacktestRun:
            conditions.append(model.purpose == "MANUAL")
        run = session.scalar(light(model).where(*conditions).order_by(model.id.desc()).limit(1))
        latest[key] = compact(run, version.trade_direction) if run else None
    items = list(
        session.scalars(
            select(ScannerWatchItem)
            .where(*scoped(ScannerWatchItem, user.id, version.id, dataset))
            .order_by(ScannerWatchItem.id.desc())
            .limit(20)
        )
    )
    subs = {
        s.key: s for s in session.scalars(select(LiveSubscription).where(LiveSubscription.key.in_([i.subscription_key for i in items])))
    }
    health = []
    for key, sub in subs.items():
        expired = now() - stored_utc(sub.updated_at) > timedelta(seconds=settings.live_heartbeat_seconds)
        health.append(
            dict(
                subscription_key=key,
                provider=sub.provider,
                status="STALE" if expired else sub.status,
                updated_at=stored_utc(sub.updated_at),
                health=sub.health,
                heartbeat_expired=expired,
            )
        )
    last = session.scalar(
        select(ScannerEvent).where(*scoped(ScannerEvent, user.id, version.id, dataset)).order_by(ScannerEvent.id.desc()).limit(1)
    )
    outcome = session.scalar(
        select(ScannerOutcome)
        .join(ScannerEvent)
        .where(*scoped(ScannerEvent, user.id, version.id, dataset))
        .order_by(ScannerOutcome.id.desc())
        .limit(1)
    )
    manual, validation = latest["manual"], latest["validation"]

    def run_stage(name, run, href):
        status = (
            "MISSING"
            if run is None
            else "FAILED"
            if run["status"] == "FAILED"
            else "RUNNING"
            if run["status"].startswith("RUNNING")
            else "READY"
        )
        return stage(name, status, run["href"] if run else href, run, run["created_at"] if run else None)

    pipeline = [
        stage("DATA", "READY" if data else "MISSING", "/market-data", data[0] if data else None, data[0]["last_candle"] if data else None),
        stage(
            "FEATURES",
            "READY" if last or manual and manual["status"] == "COMPLETED" else "UNAVAILABLE",
            "/features",
            dict(
                engine=version.feature_engine_version,
                specs=version.indicator_specs,
                note="Specs alone do not prove feature calculation; inspect linked run/event evidence.",
            ),
            date=last.signal_time if last else manual["completed_at"] if manual and manual["status"] == "COMPLETED" else None,
        ),
        stage(
            "STRATEGY",
            "INCOMPATIBLE" if strategy.status == "DISABLED" else "READY",
            f"/strategies/{strategy.id}",
            record(version),
            version.created_at,
        ),
        run_stage("BACKTEST", manual, f"/strategies/{strategy.id}"),
        run_stage("VALIDATION", validation, "/validation"),
        stage(
            "SCANNER",
            "MISSING"
            if not items
            else "STALE"
            if any(h["heartbeat_expired"] for h in health)
            else "READY"
            if any(i.state == "ACTIVE" for i in items)
            else "UNAVAILABLE",
            "/scanner",
            dict(items=[item_view(i) for i in items], limit=20, last_event_id=last.id if last else None),
            last.signal_time if last else None,
        ),
        stage(
            "PAPER",
            "READY" if outcome else "MISSING",
            f"/workspace/events/{outcome.scanner_event_id}" if outcome else "/scanner",
            record(outcome) if outcome else None,
            outcome.created_at if outcome else None,
        ),
    ]
    return dict(
        dataset=dataset,
        strategy=record(strategy),
        version=record(version),
        pipeline=pipeline,
        evidence=latest,
        provider_health=health,
        journal=dict(
            href="/journal", association="NONE", note="Manual account/session evidence is separate; no inferred strategy or scanner link."
        ),
        comparison_note="Descriptive evidence only. Fixed historical assumptions and observed LIVE/REPLAY paper samples are not pooled.",
    )


@router.get("/events")
def events(
    ctx=Depends(context),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    session=Depends(db),
):
    version, _, dataset = authorize(session, user.id, ctx)
    return page(
        session,
        ScannerEvent,
        scoped(ScannerEvent, user.id, version.id, dataset),
        ScannerEvent.id.desc(),
        limit,
        offset,
        lambda e: dict(
            id=e.id,
            state=e.state,
            mode=e.mode,
            signal_time=stored_utc(e.signal_time),
            dataset=e.dataset,
            href=f"/workspace/events/{e.id}",
            watch_item_id=e.watch_item_id,
        ),
    )


@router.get("/events/{event_id}")
def event_detail(event_id: int, user=Depends(current_user), session=Depends(db)):
    event = owned(session, ScannerEvent, event_id, user.id)
    outcome = session.scalar(select(ScannerOutcome).where(ScannerOutcome.scanner_event_id == event.id))
    candle = session.get(Candle, event.signal_candle_id)
    observations = list(
        session.scalars(
            select(LiveObservation).where(LiveObservation.candle_id == event.signal_candle_id).order_by(LiveObservation.id.desc()).limit(20)
        )
    )
    return dict(
        event=record(event),
        outcome=record(outcome) if outcome else None,
        candle_id=event.signal_candle_id,
        import_id=candle.import_id,
        live_provenance=[record(o) for o in observations],
        provenance_limit=20,
        strategy_href=f"/strategies/{session.get(StrategyVersion, event.strategy_version_id).strategy_id}",
    )


@router.get("/paper")
def paper(
    ctx=Depends(context),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    session=Depends(db),
):
    version, _, dataset = authorize(session, user.id, ctx)
    # Never pool LIVE with REPLAY or distinct payout/expiry/engine contracts.
    fields = [
        ScannerEvent.mode,
        ScannerEvent.direction,
        ScannerEvent.scanner_engine_version,
        ScannerEvent.live_data_engine_version,
        ScannerEvent.feature_engine_version,
        ScannerEvent.strategy_dsl_version,
    ]
    fields += [
        ScannerEvent.evidence[k].as_string().label(k)
        for k in ("payout_snapshot", "payout_source", "payout_product", "expiry_bars", "expiry_source")
    ]
    fields.append(ScannerOutcome.result)
    grouped = (
        select(
            *fields,
            func.count().label("count"),
            func.min(ScannerEvent.signal_time).label("first_signal"),
            func.max(ScannerEvent.signal_time).label("last_signal"),
        )
        .join(ScannerOutcome, ScannerOutcome.scanner_event_id == ScannerEvent.id)
        .where(*scoped(ScannerEvent, user.id, version.id, dataset))
        .group_by(*fields)
    )
    total = session.scalar(select(func.count()).select_from(grouped.subquery()))
    from ..features.serialization import serialize

    return dict(
        items=[
            serialize({k: stored_utc(v) if isinstance(v, datetime) else v for k, v in r._mapping.items()})
            for r in session.execute(grouped.order_by(*fields).limit(limit).offset(offset))
        ],
        total=total,
        limit=limit,
        offset=offset,
        dataset=dataset,
        strategy_version_id=version.id,
        note="Counts of persisted outcomes grouped by exact contract and result. Pending signals excluded; GAP/UNAVAILABLE are not losses. No pooled win rate.",
    )


@router.get("/history")
def history(
    kind: str = Query(pattern="^(manual|validation)$"),
    ctx=Depends(context),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    session=Depends(db),
):
    version, _, dataset = authorize(session, user.id, ctx)
    model = BacktestRun if kind == "manual" else ValidationRun
    where = scoped(model, user.id, version.id, dataset)
    if kind == "manual":
        where.append(model.purpose == "MANUAL")
    total = session.scalar(select(func.count()).select_from(model).where(*where))
    return dict(
        items=[
            compact(r, version.trade_direction)
            for r in session.scalars(light(model).where(*where).order_by(model.id.desc()).limit(limit).offset(offset))
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/comparison")
def comparison(backtest_id: int, validation_id: int, ctx=Depends(context), user=Depends(current_user), session=Depends(db)):
    version, _, dataset = authorize(session, user.id, ctx)
    a = owned(session, BacktestRun, backtest_id, user.id)
    b = owned(session, ValidationRun, validation_id, user.id)
    directions = dict(
        session.execute(
            select(StrategyVersion.id, StrategyVersion.trade_direction).where(
                StrategyVersion.id.in_([a.strategy_version_id, b.strategy_version_id])
            )
        ).all()
    )
    differences = []
    for label, run in (("manual", a), ("validation", b)):
        for k, value in dataset.model_dump().items():
            if run.dataset.get(k) != value:
                differences.append(f"{label}: dataset.{k}")
        if run.strategy_version_id != version.id:
            differences.append(f"{label}: StrategyVersion")
    for field in (
        "feature_engine_version",
        "strategy_dsl_version",
        "backtest_engine_version",
        "payout_percent",
        "expiry_bars",
        "overlap_policy",
    ):
        if getattr(a, field) != getattr(b, field):
            differences.append(field)
    if a.purpose != "MANUAL":
        differences.append("validation child is not a manual backtest")
    if directions[a.strategy_version_id] != directions[b.strategy_version_id]:
        differences.append("trade_direction")
    if a.status != "COMPLETED" or b.status != "COMPLETED":
        differences.append("incomplete evidence")
    segments = list(
        session.scalars(select(ValidationSegment).where(ValidationSegment.validation_run_id == b.id).order_by(ValidationSegment.id))
    )
    return dict(
        status="INCOMPATIBLE" if differences else "CONTEXT_ALIGNED_NOT_POOLED",
        differences=differences,
        manual=compact(a, directions[a.strategy_version_id]),
        validation=compact(b, directions[b.strategy_version_id]),
        validation_children=[record(s) for s in segments],
        note="Different date ranges and sample roles remain separate; validation TEST is not manual in-sample evidence. No ranking.",
    )
