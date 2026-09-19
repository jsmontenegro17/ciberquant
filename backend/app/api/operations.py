from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from .deps import current_user, db
from .research import record
from ..config import settings
from ..models import WorkerHeartbeat, LiveSubscription, ScannerWatchItem, MarketDataImport, BacktestRun, ValidationRun, now
from ..market_data.normalization import stored_utc

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/status")
def status(user=Depends(current_user), session=Depends(db)):
    worker = session.get(WorkerHeartbeat, "scanner")
    worker_state = (
        "UNAVAILABLE"
        if worker is None
        else "STALE"
        if now() - stored_utc(worker.updated_at) > timedelta(seconds=settings.live_heartbeat_seconds)
        else worker.status
    )
    keys = select(ScannerWatchItem.subscription_key).where(ScannerWatchItem.user_id == user.id)
    subscriptions = session.scalars(
        select(LiveSubscription).where(LiveSubscription.key.in_(keys)).order_by(LiveSubscription.key).limit(100)
    )
    providers = []
    for sub in subscriptions:
        expired = now() - stored_utc(sub.updated_at) > timedelta(seconds=settings.live_heartbeat_seconds)
        providers.append(
            dict(
                provider=sub.provider,
                dataset=sub.dataset,
                status="STALE" if expired else sub.status,
                updated_at=stored_utc(sub.updated_at),
                diagnostics=sub.health,
            )
        )
    jobs = {}
    for model, name, owner, states in (
        (MarketDataImport, "import", MarketDataImport.created_by_user_id, ["PROCESSING"]),
        (BacktestRun, "backtest", BacktestRun.user_id, ["RUNNING"]),
        (ValidationRun, "validation", ValidationRun.user_id, ["RUNNING_DEVELOPMENT", "RUNNING_TEST"]),
    ):
        where = [owner == user.id]
        jobs[name] = dict(
            running=session.scalar(select(func.count()).select_from(model).where(*where, model.status.in_(states))),
            old_running=session.scalar(
                select(func.count())
                .select_from(model)
                .where(*where, model.status.in_(states), model.started_at < now() - timedelta(minutes=5))
            ),
            recent_failures=[
                dict(id=r.id, status=r.status, completed_at=r.completed_at)
                for r in session.scalars(select(model).where(*where, model.status == "FAILED").order_by(model.id.desc()).limit(5))
            ],
        )
    return dict(
        version="1.0.0-dev",
        environment=settings.environment,
        worker=dict(state=worker_state, heartbeat=record(worker) if worker else None),
        subscriptions=providers,
        subscription_limit=100,
        jobs=jobs,
        note="Old RUNNING is not proof of abandonment. Operator recovery requires exclusive PostgreSQL lifecycle ownership.",
    )
