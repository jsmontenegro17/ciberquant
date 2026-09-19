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
from dataclasses import asdict
from app.models import Candle
from feature_fixture import series
from backtest_fixture import candles as binary_candles

test_directory = TemporaryDirectory(prefix="ciberquant-e2e-")
engine = create_engine("sqlite:///" + str(Path(test_directory.name) / "qa.db"), connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
factory = sessionmaker(bind=engine)
with factory() as s:
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


def test_db():
    with factory() as session:
        yield session


app.dependency_overrides[db] = test_db
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:5174"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
