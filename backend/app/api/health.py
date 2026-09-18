from fastapi import APIRouter
router=APIRouter(tags=['system'])
@router.get('/health')
def health(): return {'status':'ok'}
@router.get('/ready')
def ready(): return {'status':'ready'}
