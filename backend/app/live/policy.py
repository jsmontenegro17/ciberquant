from sqlalchemy import select
from ..models import StrategyVersion, Strategy, ValidationRun
from ..strategies.repository import owned
from ..validation.protocol import historical_state
from ..market_data.normalization import stored_utc
from fastapi import HTTPException


def compatibility(session, user_id, version_id, dataset):
    version = session.get(StrategyVersion, version_id)
    if version is None:
        raise HTTPException(404, "Resource not found")
    strategy = owned(session, Strategy, version.strategy_id, user_id)
    runs = list(session.scalars(select(ValidationRun).where(ValidationRun.strategy_version_id == version_id)))
    compatible = [r for r in runs if r.dataset == dataset.model_dump()]
    global_state, dataset_state = historical_state(runs), historical_state(compatible)
    passes = sorted(
        [r for r in compatible if r.status == "COMPLETED" and r.verdict == "PASS"],
        key=lambda r: (stored_utc(r.test_end), stored_utc(r.test_start), stored_utc(r.created_at), r.id),
    )
    accepted = passes[-1] if passes else None
    return version, dict(
        strategy_name=strategy.name,
        version=version.version,
        lifecycle=strategy.status,
        validation_state=global_state,
        dataset_validation_state=dataset_state,
        compatible=global_state == dataset_state == "HISTORICALLY_VALIDATED" and strategy.status == "TESTING",
        validation_run_id=accepted.id if accepted else None,
        validation_payout=accepted.payout_percent if accepted else None,
        expiry_bars=accepted.expiry_bars if accepted else None,
        definition_sha256=version.definition_sha256,
    )
