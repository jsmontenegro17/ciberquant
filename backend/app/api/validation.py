from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from .deps import current_user, db
from .research import record, page
from ..models import ValidationRun, ValidationSegment, StrategyVersion, Strategy
from ..strategies.repository import owned
from ..validation import repository as repo
from ..validation.protocol import definitions
from ..validation.schemas import ValidationCreate
from ..strategies.dsl import digest

router = APIRouter(tags=["validation"])


def view(session, run):
    version = session.get(StrategyVersion, run.strategy_version_id)
    strategy = session.get(Strategy, version.strategy_id)
    return {
        **record(run),
        **repo.state(session, run.strategy_version_id),
        "strategy_name": strategy.name,
        "strategy_id": strategy.id,
        "version_number": version.version,
    }


@router.get("/validation/definitions")
def protocol(user=Depends(current_user)):
    return definitions()


@router.post("/validations/preview")
def preview(body: ValidationCreate, user=Depends(current_user), session=Depends(db)):
    *_, frozen = repo.plan(session, user.id, body)
    return {"config_snapshot": frozen, "config_sha256": digest(frozen)}


@router.post("/validations")
def create(body: ValidationCreate, user=Depends(current_user), session=Depends(db)):
    return view(session, repo.create(session, user.id, body))


@router.get("/validations")
def validations(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user=Depends(current_user), session=Depends(db)):
    return page(
        session, ValidationRun, [ValidationRun.user_id == user.id], ValidationRun.id.desc(), limit, offset, lambda r: view(session, r)
    )


@router.get("/validations/{run_id}")
def detail(run_id: int, user=Depends(current_user), session=Depends(db)):
    return view(session, owned(session, ValidationRun, run_id, user.id))


@router.get("/validations/{run_id}/segments")
def segments(run_id: int, user=Depends(current_user), session=Depends(db)):
    owned(session, ValidationRun, run_id, user.id)
    return [
        record(s)
        for s in session.scalars(
            select(ValidationSegment).where(ValidationSegment.validation_run_id == run_id).order_by(ValidationSegment.id)
        )
    ]


@router.post("/validations/{run_id}/reveal-test")
def reveal(run_id: int, user=Depends(current_user), session=Depends(db)):
    return view(session, repo.reveal(session, user.id, run_id))
