from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth,trading,health
from .api import market_data, features, research
from .market_data.upload_limit import UploadLimitMiddleware
from .strategies.request_limit import ResearchRequestLimit
app=FastAPI(title='CiberQuant API',version='0.5.0-dev')
app.include_router(research.router, prefix='/api/v1')
app.add_middleware(UploadLimitMiddleware)
app.add_middleware(ResearchRequestLimit)
app.include_router(market_data.router, prefix='/api/v1')
app.include_router(features.router, prefix='/api/v1')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(health.router); app.include_router(auth.router,prefix='/api/v1'); app.include_router(trading.router,prefix='/api/v1')
