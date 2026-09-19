from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator
from typing import Literal


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str
    status: str


class Login(BaseModel):
    email: str
    password: str


class AccountCreate(BaseModel):
    name: str
    broker: str | None = None
    currency: str = "USD"
    initial_balance: Decimal = Field(gt=0)


class AccountOut(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    current_balance: Decimal
    status: str


class SessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trading_account_id: int
    notes: str | None = None


class SessionSnapshot(BaseModel):
    trading_account_id: int
    risk_per_trade_percent: Decimal = Field(gt=0, le=100)
    max_loss_amount: Decimal = Field(gt=0)
    max_operations: int = Field(gt=0)
    minimum_payout_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    profit_target_amount: Decimal | None = None
    notes: str | None = None


class SessionOut(SessionSnapshot):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    starting_balance: Decimal
    ending_balance: Decimal | None
    current_balance: Decimal | None = None
    status: str
    started_at: datetime
    ended_at: datetime | None


class TradeCreate(BaseModel):
    trading_account_id: int
    trading_session_id: int
    symbol: str = Field(min_length=1, max_length=50)
    market_type: Literal["REGULAR", "OTC"]
    timeframe: str = Field(min_length=1, max_length=20)
    direction: Literal["CALL", "PUT"]
    stake: Decimal = Field(gt=0)
    payout_percent: Decimal = Field(ge=0, le=100)
    result: Literal["WIN", "LOSS", "DRAW", "CANCELLED"]
    notes: str | None = None
    opened_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiration_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_interval(self):
        if self.expiration_at and self.expiration_at <= self.opened_at:
            raise ValueError("Expiration must follow opening time")
        return self


class TradeOut(TradeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profit_loss: Decimal | None
    opened_at: datetime
    expiration_at: datetime | None = None


class JournalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    trade_id: int | None = None
    session_id: int | None = None


class JournalOut(JournalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime


class LedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entry_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    created_at: datetime
    trade_id: int | None
    session_id: int | None


class SessionSummary(BaseModel):
    session_id: int
    total_trades: int
    wins: int
    losses: int
    draws: int
    cancelled: int
    win_rate: Decimal
    gross_profit: Decimal
    gross_loss: Decimal
    net_pnl: Decimal
    starting_balance: Decimal
    ending_balance: Decimal
    max_win_streak: int
    max_loss_streak: int
    currency: str
    suggested_stake: Decimal
    loss_consumed: Decimal
    remaining_risk: Decimal
    operations_remaining: int
    limit_reached: bool
    limit_reason: str | None


class RiskPreview(SessionSnapshot):
    current_balance: Decimal
    currency: str
    suggested_stake: Decimal


class SessionHistory(SessionOut):
    total_trades: int
    wins: int
    losses: int
    win_rate: Decimal
    net_pnl: Decimal
    currency: str


class AnalyticsOverview(BaseModel):
    recent_trades: list[TradeOut] = Field(default_factory=list)
    current_balance: Decimal
    today_pnl: Decimal
    month_pnl: Decimal
    total_trades: int
    monthly_trades: int
    win_rate: Decimal
    sessions_count: int
    current_session: SessionOut | None
    max_win_streak: int
    max_loss_streak: int
