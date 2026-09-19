from sqlalchemy import select, func
from fastapi import HTTPException
from ..models import Strategy, StrategyVersion, AuditLog, now
from .dsl import digest


def owned(session, model, entity_id, user_id, lock=False):
    stmt = select(model).where(model.id == entity_id, model.user_id == user_id)
    result = session.scalar(stmt.with_for_update() if lock else stmt)
    if result is None:
        raise HTTPException(404, "Resource not found")
    return result


def audit(session, user_id, event, entity, entity_id):
    session.add(AuditLog(user_id=user_id, event_type=event, entity_type=entity, entity_id=entity_id))


def create_version(session, strategy_id, user_id, definition):
    strategy = owned(session, Strategy, strategy_id, user_id, lock=True)
    number = (session.scalar(select(func.max(StrategyVersion.version)).where(StrategyVersion.strategy_id == strategy.id)) or 0) + 1
    snapshot = definition.snapshot()
    version = StrategyVersion(strategy_id=strategy.id, version=number, **snapshot, definition_sha256=digest(snapshot))
    session.add(version)
    session.flush()
    strategy.updated_at = now()
    audit(session, user_id, "STRATEGY_VERSION_CREATED", "strategy_version", version.id)
    session.commit()
    return version
