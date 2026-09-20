"""Conservative PostgreSQL lifecycle ownership, not a computation/job queue."""

from contextlib import contextmanager
from functools import wraps
import logging
from datetime import timedelta
from sqlalchemy import text, select, event
from sqlalchemy.orm import Session
from .models import MarketDataImport, BacktestRun, ValidationRun, AuditLog, now

KEYS = {"import": 808001, "backtest": 808002, "validation": 808003}
log = logging.getLogger("ciberquant.operations")


@contextmanager
def ownership(engine, kind, shared=True):
    if engine.dialect.name != "postgresql":
        raise RuntimeError("Operational recovery requires PostgreSQL")
    # The same physical connection holds ownership AND all job transactions.
    # An interrupted connection cannot continue computation persistence under a new owner.
    with engine.connect() as connection:
        function = "pg_advisory_lock_shared" if shared else "pg_try_advisory_lock"
        acquired = connection.scalar(text(f"SELECT {function}(:key)"), {"key": KEYS[kind]})
        if not shared and not acquired:
            connection.rollback()
            yield None
            return
        pid = connection.scalar(text("SELECT pg_backend_pid()"))
        connection.commit()
        session = Session(bind=connection, expire_on_commit=False)

        @event.listens_for(session, "after_begin")
        def fence(session, transaction, active):
            if active.scalar(text("SELECT pg_backend_pid()")) != pid:
                raise RuntimeError("Operational ownership lost; retry requires a new request")

        try:
            yield session
        finally:
            session.close()
            if not connection.invalidated:
                unlock = "pg_advisory_unlock_shared" if shared else "pg_advisory_unlock"
                connection.execute(text(f"SELECT {unlock}(:key)"), {"key": KEYS[kind]})
                connection.commit()


def lifecycle(kind):
    def decorate(fn):
        @wraps(fn)
        def wrapped(session, *args, **kwargs):
            bind = session.get_bind()
            if bind.dialect.name != "postgresql":
                return fn(session, *args, **kwargs)  # SQLite computation harness; no recovery claim.
            engine = getattr(bind, "engine", bind)
            with ownership(engine, kind) as working:
                log.info("job_start kind=%s", kind)
                try:
                    result = fn(working, *args, **kwargs)
                    working.refresh(result)
                    working.expunge(result)
                    session.expire_all()
                    return result
                finally:
                    log.info("job_stop kind=%s", kind)

        return wrapped

    return decorate


def recover(engine, kind, minimum_age_seconds=300, limit=100):
    if kind not in KEYS or minimum_age_seconds < 0 or not 1 <= limit <= 100:
        raise ValueError("Invalid recovery request")
    models = {
        "import": (MarketDataImport, ["PROCESSING"]),
        "backtest": (BacktestRun, ["RUNNING"]),
        "validation": (ValidationRun, ["RUNNING_DEVELOPMENT", "RUNNING_TEST"]),
    }
    model, states = models[kind]
    with ownership(engine, kind, shared=False) as session:
        if session is None:
            return dict(status="ACTIVE_OR_RECOVERY_BUSY", recovered=[])
        # Absence of every active owner in this category is required, not age alone.
        cutoff = session.scalar(select(func_now())) - timedelta(seconds=minimum_age_seconds)
        rows = list(
            session.scalars(
                select(model)
                .where(model.status.in_(states), model.started_at <= cutoff)
                .order_by(model.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        )
        recovered = []
        for run in rows:
            old = run.status
            run.status, run.completed_at = "FAILED", now()
            message = "ABANDONED: no active PostgreSQL lifecycle owner; explicit new attempt required"
            run.error_summary = {"errors": [{"code": "ABANDONED", "message": message}], "warnings": []} if kind == "import" else message
            uid = run.created_by_user_id if kind == "import" else run.user_id
            session.add(
                AuditLog(
                    user_id=uid,
                    event_type="JOB_RECOVERED",
                    entity_type=model.__tablename__,
                    entity_id=run.id,
                    metadata_json={"kind": kind, "previous_status": old, "status": "FAILED"},
                )
            )
            recovered.append(run.id)
        session.commit()
        log.info("job_recovery kind=%s count=%s", kind, len(recovered))
        return dict(status="RECONCILED", recovered=recovered)


def func_now():
    from sqlalchemy import func

    return func.now()
