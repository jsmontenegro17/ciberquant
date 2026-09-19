from fastapi import APIRouter, Depends, HTTPException
from .deps import current_user, db
from ..features.schemas import ComputeRequest
from ..features.registry import definitions
from ..features.repository import calculate_snapshot
from ..features.serialization import serialize
from ..config import settings

router = APIRouter(prefix='/features', tags=['features'])


@router.get('/definitions')
def feature_definitions(user=Depends(current_user)):
    return serialize({**definitions(settings.feature_api_max_indicator_specs),
                      'max_return_rows': settings.feature_api_max_return_rows,
                      'max_source_candles': settings.feature_engine_max_source_candles})


@router.post('/compute')
def compute_features(request: ComputeRequest, user=Depends(current_user), session=Depends(db)):
    try:
        return serialize(calculate_snapshot(session, request))
    except ValueError as exc:
        raise HTTPException(422, str(exc))

