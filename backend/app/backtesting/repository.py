from dataclasses import asdict
from decimal import Decimal
from sqlalchemy import select, func
from fastapi import HTTPException
from ..models import Strategy, StrategyVersion, Candle, BacktestRun, BacktestTrade, now
from ..strategies.repository import owned, audit
from ..strategies.schemas import VersionCreate
from ..strategies.dsl import digest
from ..features.engine import FeatureCandle
from ..features.serialization import serialize
from ..market_data.repository import dataset_conditions, candle_data
from ..market_data.normalization import stored_utc
from ..config import settings
from . import BACKTEST_ENGINE_VERSION
from .engine import simulate


def run_backtest(session, user_id, request):
    version = session.get(StrategyVersion, request.strategy_version_id)
    if version is None:
        raise HTTPException(404, "Resource not found")
    strategy = owned(session, Strategy, version.strategy_id, user_id)
    if strategy.status == "DISABLED":
        raise HTTPException(422, "Disabled strategy cannot run")
    definition = VersionCreate(**{key: getattr(version, key) for key in VersionCreate.model_fields})
    snapshot = definition.snapshot()
    if digest(snapshot) != version.definition_sha256:
        raise HTTPException(409, "Strategy definition integrity mismatch")
    conditions = dataset_conditions(request.dataset)
    maximum = session.scalar(select(func.max(Candle.id)).where(*conditions)) or 0
    ceiling = maximum if request.as_of_candle_id is None else request.as_of_candle_id
    if ceiling > maximum:
        raise HTTPException(422, "as_of_candle_id exceeds dataset maximum")
    config = request.model_copy(update={"as_of_candle_id": ceiling})
    frozen = config.model_dump(mode="json")
    frozen.update(
        entry_model="NEXT_CANDLE_OPEN",
        backtest_engine_version=BACKTEST_ENGINE_VERSION,
        feature_engine_version=definition.feature_engine_version,
        strategy_dsl_version=definition.strategy_dsl_version,
        definition_sha256=version.definition_sha256,
    )
    anchor = session.scalar(select(func.min(Candle.open_time)).where(*conditions, Candle.id <= ceiling))
    frozen["calculation_anchor"] = stored_utc(anchor).isoformat() if anchor else None
    run = BacktestRun(
        user_id=user_id,
        strategy_version_id=version.id,
        status="RUNNING",
        backtest_engine_version=BACKTEST_ENGINE_VERSION,
        feature_engine_version=definition.feature_engine_version,
        strategy_dsl_version=definition.strategy_dsl_version,
        dataset=config.dataset.model_dump(),
        as_of_candle_id=ceiling,
        signal_start=config.signal_start,
        signal_end=config.signal_end,
        payout_percent=Decimal(config.payout_percent),
        expiry_bars=config.expiry_bars,
        entry_model="NEXT_CANDLE_OPEN",
        overlap_policy=config.overlap_policy,
        strategy_snapshot={**snapshot, "definition_sha256": version.definition_sha256, "name": strategy.name, "version": version.version},
        config_snapshot=frozen,
        config_sha256=digest(frozen),
    )
    session.add(run)
    session.flush()
    run_id = run.id
    audit(session, user_id, "BACKTEST_STARTED", "backtest_run", run_id)
    session.commit()
    try:
        source = [*conditions, Candle.id <= ceiling, Candle.open_time < config.signal_end]
        count = session.scalar(select(func.count()).select_from(Candle).where(*source))
        if count > settings.backtest_max_source_candles:
            raise ValueError("BACKTEST_MAX_SOURCE_CANDLES exceeded; exact origin calculation required")
        stmt = select(Candle).where(*source).order_by(Candle.open_time).limit(settings.backtest_max_source_candles + 1)
        candles = (FeatureCandle(**asdict(candle_data(c)), candle_id=c.id) for c in session.scalars(stmt.execution_options(yield_per=1000)))
        result = simulate(candles, definition, config, settings.backtest_max_source_candles, settings.backtest_max_trades)
        for t in result["trades"]:
            session.add(BacktestTrade(backtest_run_id=run_id, **{**t, "signal_context": serialize(t["signal_context"])}))
        run.metrics, run.equity_curve = serialize(result["metrics"]), serialize(result["equity_curve"])
        run.status, run.completed_at = "COMPLETED", now()
        audit(session, user_id, "BACKTEST_COMPLETED", "backtest_run", run_id)
        session.commit()
    except Exception as exc:
        session.rollback()
        run = session.get(BacktestRun, run_id)
        run.status, run.completed_at = "FAILED", now()
        run.error_summary = (
            str(exc)[:500] if isinstance(exc, ValueError) else "Backtest execution/persistence failed; no partial trade evidence committed"
        )
        audit(session, user_id, "BACKTEST_FAILED", "backtest_run", run_id)
        session.commit()
    return run
