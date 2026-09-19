from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from .deps import db
from ..config import settings
router=APIRouter(tags=['system'])
@router.get('/health')
def health(): return {'status':'ok','version':'1.0.0-dev','environment':settings.environment}
@router.get('/ready')
def ready(session=Depends(db)):
    try:
        session.execute(text('SELECT 1'))
    except Exception:
        raise HTTPException(503, 'Database unavailable') from None
    return {'status':'ready','database':'reachable'}
