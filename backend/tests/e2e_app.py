"""Isolated temporary SQLite API fixture for browser QA. Never used by production."""

from decimal import Decimal
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tempfile import TemporaryDirectory
from pathlib import Path
from app.main import app
from app.db import Base
from app.api.deps import db
from app.api.auth import pwd
from app.models import User, TradingAccount, RiskProfile, LedgerEntry
from dataclasses import asdict,replace
from app.models import Candle
from feature_fixture import series
from backtest_fixture import candles as binary_candles
from validation_fixture import data as validation_candles
from validation_fixture import request as validation_request
from backtest_fixture import definition,leaf
from app.models import Strategy
from app.strategies.repository import create_version
from app.validation.repository import create as create_validation,reveal
from app.config import settings
from app.api import scanner as scanner_api
from contextlib import asynccontextmanager
import os
import sys
import subprocess

test_directory = TemporaryDirectory(prefix="ciberquant-e2e-")
engine = create_engine("sqlite:///" + str(Path(test_directory.name) / "qa.db"), connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
factory = sessionmaker(bind=engine)
scanner_api.SessionLocal=factory
settings.enable_replay_provider=True
with factory() as s:
    for index,candle in enumerate(validation_candles()):
        values=asdict(replace(candle,source='SCANNER_FIXTURE',close=Decimal(99 if index==1490 else 101)))
        values.pop('candle_id')
        s.add(Candle(**values))
    for candle in validation_candles():
        values = asdict(candle)
        values.pop('candle_id')
        values['source'] = 'VALIDATION_FIXTURE'
        s.add(Candle(**values))
    for candle in series(size=100):
        values = asdict(candle)
        values.pop('candle_id')
        s.add(Candle(**values))
    for candle in binary_candles():
        values = asdict(candle)
        values.pop('candle_id')
        values['source'] = 'BINARY_FIXTURE'
        s.add(Candle(**values))
    s.add(User(email="market-admin@example.com", name="Market Admin", password_hash=pwd.hash("browser-test-only"), role="ADMIN"))
    user = User(email="qa@example.com", name="Browser QA", password_hash=pwd.hash("browser-test-only"))
    s.add(user)
    s.flush()
    s.add(
        RiskProfile(
            user_id=user.id,
            risk_per_trade_percent=Decimal("1"),
            max_session_loss_percent=Decimal("2"),
            max_session_operations=4,
            minimum_payout_percent=Decimal("80"),
        )
    )
    for name, balance, currency in [("QA USD", "2000", "USD"), ("QA EUR", "750", "EUR")]:
        account = TradingAccount(
            user_id=user.id, name=name, currency=currency, initial_balance=Decimal(balance), current_balance=Decimal(balance)
        )
        s.add(account)
        s.flush()
        s.add(
            LedgerEntry(
                account_id=account.id,
                entry_type="INITIAL_BALANCE",
                amount=Decimal(balance),
                balance_before=Decimal("0"),
                balance_after=Decimal(balance),
            )
        )
    s.commit()
    strategy=Strategy(user_id=user.id,name='Scanner validated fixture',status='TESTING')
    s.add(strategy);s.commit()
    version=create_version(s,strategy.id,user.id,definition(leaf(value='100')))
    plan=create_validation(s,user.id,validation_request(strategy_version_id=version.id,dataset={'source':'SCANNER_FIXTURE','broker':'DEMO','symbol':'EURUSD','market_type':'REGULAR','timeframe':'1h'}))
    assert reveal(s,user.id,plan.id).verdict=='PASS'


@asynccontextmanager
async def qa_lifespan(_app):
    # Browser QA only: dedicated worker process, never an HTTP ingestion loop.
    env={**os.environ,'DATABASE_URL':str(engine.url),'ENABLE_REPLAY_PROVIDER':'true','REPLAY_PREFIX_CANDLES':'1490','REPLAY_PAYOUT':'79','LIVE_POLL_SECONDS':'1','REPLAY_SPEED':'MAX'}
    worker=subprocess.Popen([sys.executable,'-m','app.live.worker'],env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:yield
    finally:
        worker.terminate()
        worker.wait(timeout=10)


app.router.lifespan_context=qa_lifespan


def test_db():
    with factory() as session:
        yield session


app.dependency_overrides[db] = test_db
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5174"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
