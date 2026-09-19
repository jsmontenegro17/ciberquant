from dataclasses import asdict
from decimal import Decimal
from types import SimpleNamespace
from sqlalchemy import select, func, update
from fastapi import HTTPException
from ..models import Strategy, StrategyVersion, Candle, BacktestRun, BacktestTrade, ValidationRun, ValidationSegment, now
from ..strategies.repository import owned, audit
from ..strategies.schemas import VersionCreate
from ..strategies.dsl import digest
from ..features.engine import FeatureCandle, compute
from ..features.serialization import serialize
from ..market_data.repository import dataset_conditions, candle_data
from ..market_data.normalization import stored_utc
from ..market_data.timeframe import duration
from ..config import settings
from ..backtesting.engine import simulate_rows
from .schemas import ValidationCreate
from .protocol import split, definitions, bootstrap, verdict, monthly, historical_state


def version_definition(session, vid, uid, require_testing=False):
    version = session.get(StrategyVersion, vid)
    if version is None:
        raise HTTPException(404, "Resource not found")
    strategy = owned(session, Strategy, version.strategy_id, uid)
    if require_testing and strategy.status != "TESTING":
        raise HTTPException(422, "Validation requires strategy lifecycle TESTING")
    definition = VersionCreate(**{k: getattr(version, k) for k in VersionCreate.model_fields})
    if digest(definition.snapshot()) != version.definition_sha256:
        raise HTTPException(409, "Strategy definition integrity mismatch")
    return version, strategy, definition


def warnings(session, run):
    prior = [
        r
        for r in session.scalars(
            select(ValidationRun).where(ValidationRun.user_id == run.user_id, ValidationRun.strategy_version_id == run.strategy_version_id)
        )
        if r.id != run.id and r.dataset == run.dataset
    ]
    revealed = [r for r in prior if r.test_revealed_at is not None]
    overlapping = [
        r for r in revealed if stored_utc(r.test_start) < stored_utc(run.test_end) and stored_utc(run.test_start) < stored_utc(r.test_end)
    ]
    return dict(
        prior_validation_count=len(prior),
        prior_revealed_holdout_count=len(revealed),
        overlapping_holdout_count=len(overlapping),
        replay_count=sum(r.config_sha256 == run.config_sha256 for r in prior),
    )


def state(session, vid):
    runs = list(session.scalars(select(ValidationRun).where(ValidationRun.strategy_version_id == vid)))
    latest = max(runs, key=lambda r: r.id) if runs else None
    return dict(validation_state=historical_state(runs), latest_validation_attempt=latest.verdict if latest else None)


def plan(session, uid, request):
    version, strategy, definition = version_definition(session, request.strategy_version_id, uid, True)
    conditions = dataset_conditions(request.dataset)
    maximum = session.scalar(select(func.max(Candle.id)).where(*conditions)) or 0
    ceiling = maximum if request.as_of_candle_id is None else request.as_of_candle_id
    if ceiling > maximum:
        raise HTTPException(422, "as_of_candle_id exceeds dataset maximum")
    source = [*conditions, Candle.id <= ceiling, Candle.open_time < request.overall_end]
    if session.scalar(select(func.count()).select_from(Candle).where(*source)) > settings.backtest_max_source_candles:
        raise HTTPException(422, "BACKTEST_MAX_SOURCE_CANDLES exceeded; no approximation")
    # Boundary planning reads timestamps only, not test OHLC or derived values.
    candles = [
        SimpleNamespace(open_time=stored_utc(o), close_time=stored_utc(c))
        for o, c in session.execute(
            select(Candle.open_time, Candle.close_time).where(*source, Candle.open_time >= request.overall_start).order_by(Candle.open_time)
        )
    ]
    try:
        parts = split(candles, request.overall_start, request.overall_end)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    frozen = request.model_copy(update={"as_of_candle_id": ceiling}).model_dump(mode="json")
    frozen.update(
        definition_sha256=version.definition_sha256,
        entry_model="NEXT_CANDLE_OPEN",
        protocol=definitions(),
        boundaries=serialize([dict(segment_type=k, fold_number=f, signal_start=a, signal_end=b) for k, f, a, b in parts]),
    )
    return version, strategy, definition, parts, frozen


def rows_for(session, run, definition, end):
    from ..market_data.normalization import Dataset

    source = [*dataset_conditions(Dataset(**run.dataset)), Candle.id <= run.as_of_candle_id, Candle.open_time < end]
    if session.scalar(select(func.count()).select_from(Candle).where(*source)) > settings.backtest_max_source_candles:
        raise ValueError("BACKTEST_MAX_SOURCE_CANDLES exceeded")
    candles = (
        FeatureCandle(**asdict(candle_data(c)), candle_id=c.id)
        for c in session.scalars(select(Candle).where(*source).order_by(Candle.open_time).execution_options(yield_per=1000))
    )
    return list(compute(candles, definition.indicator_specs))


def child(session, run, segment, rows, definition, version, strategy):
    request = ValidationCreate(**{k: run.config_snapshot[k] for k in ValidationCreate.model_fields})
    config = request.child(stored_utc(segment.signal_start), stored_utc(segment.signal_end), run.as_of_candle_id)
    result = simulate_rows(
        rows,
        definition,
        config,
        lambda: duration(config.dataset.timeframe),
        settings.backtest_max_source_candles,
        settings.backtest_max_trades,
    )
    frozen = config.model_dump(mode="json")
    frozen.update(
        entry_model="NEXT_CANDLE_OPEN",
        backtest_engine_version=run.backtest_engine_version,
        feature_engine_version=run.feature_engine_version,
        strategy_dsl_version=run.strategy_dsl_version,
        definition_sha256=run.definition_sha256,
        calculation_anchor=rows[0]["open_time"].isoformat() if rows else None,
    )
    backtest = BacktestRun(
        user_id=run.user_id,
        strategy_version_id=version.id,
        purpose="VALIDATION",
        status="COMPLETED",
        backtest_engine_version=run.backtest_engine_version,
        feature_engine_version=run.feature_engine_version,
        strategy_dsl_version=run.strategy_dsl_version,
        dataset=run.dataset,
        as_of_candle_id=run.as_of_candle_id,
        signal_start=config.signal_start,
        signal_end=config.signal_end,
        payout_percent=run.payout_percent,
        expiry_bars=run.expiry_bars,
        entry_model=run.entry_model,
        overlap_policy=run.overlap_policy,
        strategy_snapshot={
            **definition.snapshot(),
            "definition_sha256": run.definition_sha256,
            "name": strategy.name,
            "version": version.version,
        },
        config_snapshot=frozen,
        config_sha256=digest(frozen),
        metrics=serialize(result["metrics"]),
        equity_curve=serialize(result["equity_curve"]),
        completed_at=now(),
    )
    session.add(backtest)
    session.flush()
    for t in result["trades"]:
        session.add(BacktestTrade(backtest_run_id=backtest.id, **{**t, "signal_context": serialize(t["signal_context"])}))
    segment.backtest_run_id = backtest.id
    return result


def fail(session, rid, exc):
    session.rollback()
    run = session.get(ValidationRun, rid)
    run.status, run.completed_at = "FAILED", now()
    run.error_summary = str(exc)[:500] if isinstance(exc, ValueError) else "Validation phase failed; partial phase evidence rolled back"
    audit(session, run.user_id, "VALIDATION_FAILED", "validation_run", rid)
    session.commit()
    return run


def create(session, uid, request):
    version, strategy, definition, parts, frozen = plan(session, uid, request)
    versions = {
        k: frozen["protocol"][k]
        for k in ("validation_engine_version", "feature_engine_version", "strategy_dsl_version", "backtest_engine_version")
    }
    ranges = {f"{kind.lower()}_{edge}": bound for kind, _, a, b in parts[:3] for edge, bound in (("start", a), ("end", b))}
    run = ValidationRun(
        user_id=uid,
        strategy_version_id=version.id,
        **versions,
        **ranges,
        overall_start=request.overall_start,
        overall_end=request.overall_end,
        definition_sha256=version.definition_sha256,
        dataset=request.dataset.model_dump(),
        as_of_candle_id=frozen["as_of_candle_id"],
        payout_percent=Decimal(request.payout_percent),
        expiry_bars=request.expiry_bars,
        overlap_policy=request.overlap_policy,
        config_snapshot=frozen,
        config_sha256=digest(frozen),
    )
    with session.no_autoflush:
        run.holdout_warnings = warnings(session, run)
    session.add(run)
    session.flush()
    rid = run.id
    for kind, fold, a, b in parts:
        session.add(ValidationSegment(validation_run_id=rid, segment_type=kind, fold_number=fold, signal_start=a, signal_end=b))
    audit(session, uid, "VALIDATION_STARTED", "validation_run", rid)
    session.commit()
    try:
        rows = rows_for(session, run, definition, stored_utc(run.test_start))
        development, folds, temporal = {}, [], {}
        segments = list(
            session.scalars(select(ValidationSegment).where(ValidationSegment.validation_run_id == rid).order_by(ValidationSegment.id))
        )
        for segment in segments:
            if segment.segment_type == "TEST":
                continue
            result = child(session, run, segment, rows, definition, version, strategy)
            if segment.segment_type == "WALK_FORWARD":
                folds.append(
                    dict(
                        fold_number=segment.fold_number,
                        **serialize(result["metrics"]),
                        evaluable=result["metrics"]["resolved_trades"] >= 20,
                    )
                )
            else:
                development[segment.segment_type] = serialize(result["metrics"])
                if segment.segment_type == "VALIDATION":
                    temporal["VALIDATION"] = serialize(monthly(result["trades"], run.payout_percent))
        run.development_summary, run.walk_forward_summary, run.temporal_stability = development, folds, temporal
        run.status = "SEALED"
        audit(session, uid, "VALIDATION_DEVELOPMENT_COMPLETED", "validation_run", rid)
        session.commit()
    except Exception as exc:
        return fail(session, rid, exc)
    return run


def reveal(session, uid, rid):
    run = owned(session, ValidationRun, rid, uid)
    # Serialize claims for the same immutable version; CAS also protects SQLite and duplicate requests.
    session.execute(select(StrategyVersion.id).where(StrategyVersion.id == run.strategy_version_id).with_for_update())
    session.refresh(run)
    if run.status != "SEALED":
        raise HTTPException(409, "Only SEALED tests can be revealed once")
    changed = session.execute(
        update(ValidationRun)
        .where(ValidationRun.id == rid, ValidationRun.status == "SEALED")
        .values(status="RUNNING_TEST", test_revealed_at=now(), holdout_warnings=warnings(session, run))
        .execution_options(synchronize_session=False)
    )
    if changed.rowcount != 1:
        session.rollback()
        raise HTTPException(409, "Test reveal already claimed")
    audit(session, uid, "VALIDATION_TEST_REVEALED", "validation_run", rid)
    session.commit()
    session.refresh(run)
    try:
        version, strategy, definition = version_definition(session, run.strategy_version_id, uid)
        if digest(run.config_snapshot) != run.config_sha256 or version.definition_sha256 != run.definition_sha256:
            raise ValueError("Frozen validation integrity mismatch")
        rows = rows_for(session, run, definition, stored_utc(run.test_end))
        segment = session.scalar(
            select(ValidationSegment).where(ValidationSegment.validation_run_id == rid, ValidationSegment.segment_type == "TEST")
        )
        result = child(session, run, segment, rows, definition, version, strategy)
        boot = bootstrap(result["trades"], run.config_sha256)
        run.verdict, run.gates = verdict(run.development_summary["VALIDATION"], run.walk_forward_summary, result["metrics"], boot)
        run.test_summary, run.bootstrap_summary = serialize(result["metrics"]), serialize(boot)
        run.temporal_stability = {**run.temporal_stability, "TEST": serialize(monthly(result["trades"], run.payout_percent))}
        run.status, run.completed_at = "COMPLETED", now()
        audit(session, uid, "VALIDATION_COMPLETED", "validation_run", rid)
        session.commit()
    except Exception as exc:
        return fail(session, rid, exc)
    return run
