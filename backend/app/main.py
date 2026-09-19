from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth,trading,health
from .api import market_data, features, research
from .market_data.upload_limit import UploadLimitMiddleware
from .strategies.request_limit import ResearchRequestLimit
from .api import validation
from .api import scanner
from .api import workspace
from .api import operations
from .config import settings
from .security_boundary import SecurityBoundary
app=FastAPI(title='CiberQuant API',version='1.0.0-dev')
app.include_router(workspace.router, prefix='/api/v1')
app.include_router(operations.router, prefix='/api/v1')
app.include_router(scanner.router, prefix='/api/v1')
app.include_router(validation.router, prefix='/api/v1')
app.include_router(research.router, prefix='/api/v1')
app.add_middleware(UploadLimitMiddleware)
app.add_middleware(ResearchRequestLimit)
app.include_router(market_data.router, prefix='/api/v1')
app.include_router(features.router, prefix='/api/v1')
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=True,allow_methods=['GET','POST','PATCH','DELETE','OPTIONS'],allow_headers=['Content-Type'])
app.add_middleware(SecurityBoundary, config=settings)
app.include_router(health.router); app.include_router(auth.router,prefix='/api/v1'); app.include_router(trading.router,prefix='/api/v1')
