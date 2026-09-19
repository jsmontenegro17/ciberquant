from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy import select, func, inspect
from sqlalchemy.exc import IntegrityError
from .deps import current_user, db
from ..models import Strategy, StrategyVersion, BacktestRun, BacktestTrade
from ..strategies.schemas import StrategyCreate, VersionCreate, StrategyStatus
from ..strategies.repository import owned, audit, create_version
from ..strategies.dsl import definitions, fields_for
from ..features.schemas import IndicatorSpec
from ..backtesting.schemas import RunCreate
from ..backtesting.repository import run_backtest
from ..backtesting import BACKTEST_ENGINE_VERSION
from ..features.serialization import serialize
from ..market_data.normalization import stored_utc
from datetime import datetime

router = APIRouter(tags=["research"])


def record(entity):
    values = {c.key: getattr(entity, c.key) for c in inspect(entity).mapper.column_attrs}
    return serialize({k: stored_utc(v) if isinstance(v, datetime) else v for k, v in values.items()})


def page(session, model, where, order, limit, offset, convert=record):
    total = session.scalar(select(func.count()).select_from(model).where(*where))
    return dict(
        items=[convert(x) for x in session.scalars(select(model).where(*where).order_by(order).limit(limit).offset(offset))],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/strategies/definitions")
def strategy_definitions(user=Depends(current_user)):
    return {**definitions(), "backtest_engine_version": BACKTEST_ENGINE_VERSION}


@router.post("/strategies")
def new_strategy(body: StrategyCreate, user=Depends(current_user), session=Depends(db)):
    strategy = Strategy(user_id=user.id, **body.model_dump())
    session.add(strategy)
    session.flush()
    audit(session, user.id, "STRATEGY_CREATED", "strategy", strategy.id)
    session.commit()
    return record(strategy)


@router.post("/strategies/fields")
def strategy_fields(specs: list[IndicatorSpec] = Body(max_length=12), user=Depends(current_user)):
    return fields_for(specs)


@router.get("/strategies")
def strategies(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    def convert(s):
        latest = session.scalar(
            select(StrategyVersion).where(StrategyVersion.strategy_id == s.id).order_by(StrategyVersion.version.desc()).limit(1)
        )
        last = session.scalar(
            select(BacktestRun)
            .join(StrategyVersion)
            .where(StrategyVersion.strategy_id == s.id, BacktestRun.user_id == user.id)
            .order_by(BacktestRun.id.desc())
            .limit(1)
        )
        return {
            **record(s),
            "latest_version": record(latest) if latest else None,
            "last_backtest": {"id": last.id, "status": last.status} if last else None,
        }

    return page(session, Strategy, [Strategy.user_id == user.id], Strategy.id.desc(), limit, offset, convert)


@router.get("/strategies/{strategy_id}")
def strategy_detail(strategy_id: int, user=Depends(current_user), session=Depends(db)):
    return record(owned(session, Strategy, strategy_id, user.id))


@router.patch("/strategies/{strategy_id}")
def strategy_status(strategy_id: int, body: StrategyStatus, user=Depends(current_user), session=Depends(db)):
    strategy = owned(session, Strategy, strategy_id, user.id)
    strategy.status = body.status
    session.commit()
    return record(strategy)


@router.post("/strategies/{strategy_id}/versions")
def new_version(strategy_id: int, body: VersionCreate, user=Depends(current_user), session=Depends(db)):
    try:
        return record(create_version(session, strategy_id, user.id, body))
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Concurrent version change; retry")


@router.get("/strategies/{strategy_id}/versions")
def versions(
    strategy_id: int, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)
):
    owned(session, Strategy, strategy_id, user.id)
    return page(session, StrategyVersion, [StrategyVersion.strategy_id == strategy_id], StrategyVersion.version.desc(), limit, offset)


@router.post("/backtests")
def new_backtest(body: RunCreate, user=Depends(current_user), session=Depends(db)):
    return record(run_backtest(session, user.id, body))


@router.get("/backtests")
def backtests(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    return page(
        session,
        BacktestRun,
        [BacktestRun.user_id == user.id],
        BacktestRun.id.desc(),
        limit,
        offset,
        lambda r: {k: v for k, v in record(r).items() if k not in ("equity_curve", "strategy_snapshot", "config_snapshot")},
    )


@router.get("/backtests/{run_id}")
def backtest_detail(run_id: int, user=Depends(current_user), session=Depends(db)):
    return record(owned(session, BacktestRun, run_id, user.id))


@router.get("/backtests/{run_id}/trades")
def trades(
    run_id: int, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)
):
    owned(session, BacktestRun, run_id, user.id)
    return page(session, BacktestTrade, [BacktestTrade.backtest_run_id == run_id], BacktestTrade.sequence_no, limit, offset)
