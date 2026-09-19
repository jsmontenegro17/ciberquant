from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth,trading,health
app=FastAPI(title='CiberQuant API',version='0.2.0-dev')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(health.router); app.include_router(auth.router,prefix='/api/v1'); app.include_router(trading.router,prefix='/api/v1')
