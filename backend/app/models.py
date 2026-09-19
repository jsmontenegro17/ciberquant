from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, JSON, UniqueConstraint, Index, CheckConstraint, event, inspect, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
def now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__='users'; id: Mapped[int]=mapped_column(primary_key=True); email: Mapped[str]=mapped_column(String(320),unique=True,index=True); password_hash: Mapped[str]=mapped_column(String(255)); name: Mapped[str]=mapped_column(String(120)); role: Mapped[str]=mapped_column(String(20),default='USER'); status: Mapped[str]=mapped_column(String(20),default='ACTIVE'); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class TradingAccount(Base):
    __tablename__='trading_accounts'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); name: Mapped[str]=mapped_column(String(120)); broker: Mapped[str|None]=mapped_column(String(120)); currency: Mapped[str]=mapped_column(String(3),default='USD'); initial_balance: Mapped[Decimal]=mapped_column(Numeric(18,8)); current_balance: Mapped[Decimal]=mapped_column(Numeric(18,8)); status: Mapped[str]=mapped_column(String(20),default='ACTIVE'); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class RiskProfile(Base):
    __tablename__='risk_profiles'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id'),unique=True); risk_per_trade_percent: Mapped[Decimal]=mapped_column(Numeric(8,4)); max_session_loss_percent: Mapped[Decimal]=mapped_column(Numeric(8,4)); max_session_operations: Mapped[int]=mapped_column(Integer); minimum_payout_percent: Mapped[Decimal]=mapped_column(Numeric(8,4)); profit_target_percent: Mapped[Decimal|None]=mapped_column(Numeric(8,4)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class TradingSession(Base):
    __tablename__='trading_sessions'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); trading_account_id: Mapped[int]=mapped_column(ForeignKey('trading_accounts.id')); started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); ended_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); starting_balance: Mapped[Decimal]=mapped_column(Numeric(18,8)); ending_balance: Mapped[Decimal|None]=mapped_column(Numeric(18,8)); risk_per_trade_percent: Mapped[Decimal]=mapped_column(Numeric(8,4)); max_loss_amount: Mapped[Decimal]=mapped_column(Numeric(18,8)); max_operations: Mapped[int]=mapped_column(Integer); minimum_payout_percent: Mapped[Decimal]=mapped_column(Numeric(8,4),default=Decimal('0')); profit_target_amount: Mapped[Decimal|None]=mapped_column(Numeric(18,8)); status: Mapped[str]=mapped_column(String(20),default='OPEN'); notes: Mapped[str|None]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class Trade(Base):
    __tablename__='trades'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); trading_account_id: Mapped[int]=mapped_column(ForeignKey('trading_accounts.id')); trading_session_id: Mapped[int]=mapped_column(ForeignKey('trading_sessions.id')); source: Mapped[str]=mapped_column(String(30),default='MANUAL'); symbol: Mapped[str]=mapped_column(String(50)); market_type: Mapped[str]=mapped_column(String(20)); timeframe: Mapped[str]=mapped_column(String(20)); direction: Mapped[str]=mapped_column(String(10)); opened_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); expiration_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); stake: Mapped[Decimal]=mapped_column(Numeric(18,8)); payout_percent: Mapped[Decimal]=mapped_column(Numeric(8,4)); result: Mapped[str|None]=mapped_column(String(20)); profit_loss: Mapped[Decimal|None]=mapped_column(Numeric(18,8)); notes: Mapped[str|None]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class LedgerEntry(Base):
    __tablename__='account_ledger_entries'; id: Mapped[int]=mapped_column(primary_key=True); account_id: Mapped[int]=mapped_column(ForeignKey('trading_accounts.id')); trade_id: Mapped[int|None]=mapped_column(ForeignKey('trades.id')); session_id: Mapped[int|None]=mapped_column(ForeignKey('trading_sessions.id')); entry_type: Mapped[str]=mapped_column(String(30)); amount: Mapped[Decimal]=mapped_column(Numeric(18,8)); balance_before: Mapped[Decimal]=mapped_column(Numeric(18,8)); balance_after: Mapped[Decimal]=mapped_column(Numeric(18,8)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); metadata_json: Mapped[dict|None]=mapped_column('metadata',JSON)
class JournalEntry(Base):
    __tablename__='journal_entries'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); trade_id: Mapped[int|None]=mapped_column(ForeignKey('trades.id')); session_id: Mapped[int|None]=mapped_column(ForeignKey('trading_sessions.id')); title: Mapped[str]=mapped_column(String(200)); content: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class AuditLog(Base):
    __tablename__='audit_logs'; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); event_type: Mapped[str]=mapped_column(String(50)); entity_type: Mapped[str]=mapped_column(String(50)); entity_id: Mapped[int|None]=mapped_column(Integer); metadata_json: Mapped[dict|None]=mapped_column('metadata',JSON); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class MarketDataImport(Base):
    __tablename__ = 'market_data_imports'
    __table_args__ = (Index('ix_market_data_imports_created_at', 'created_at', 'id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    ingestion_method: Mapped[str] = mapped_column(String(20), default='CSV')
    source: Mapped[str] = mapped_column(String(50))
    broker: Mapped[str] = mapped_column(String(120))
    symbol: Mapped[str] = mapped_column(String(50))
    market_type: Mapped[str] = mapped_column(String(20))
    timeframe: Mapped[str] = mapped_column(String(20))
    file_name: Mapped[str] = mapped_column(String(255))
    file_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default='PROCESSING')
    rows_received: Mapped[int] = mapped_column(default=0)
    rows_valid: Mapped[int] = mapped_column(default=0)
    rows_inserted: Mapped[int] = mapped_column(default=0)
    rows_duplicates: Mapped[int] = mapped_column(default=0)
    rows_rejected: Mapped[int] = mapped_column(default=0)
    rows_conflicting: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Candle(Base):
    __tablename__ = 'candles'
    # The unique B-tree also serves equality-prefix + open_time range scans.
    __table_args__ = (UniqueConstraint('source', 'broker', 'symbol', 'market_type', 'timeframe', 'open_time', name='uq_candle_identity'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    broker: Mapped[str] = mapped_column(String(120), default='UNSPECIFIED', server_default='UNSPECIFIED')
    symbol: Mapped[str] = mapped_column(String(50))
    market_type: Mapped[str] = mapped_column(String(20))
    timeframe: Mapped[str] = mapped_column(String(20))
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    high: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    low: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    close: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    tick_volume: Mapped[Decimal | None] = mapped_column(Numeric(24, 10))
    spread: Mapped[Decimal | None] = mapped_column(Numeric(24, 10))
    import_id: Mapped[int | None] = mapped_column(ForeignKey('market_data_imports.id', name='fk_candle_import'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Strategy(Base):
    __tablename__ = 'strategies'
    __table_args__ = (CheckConstraint("status IN ('DRAFT','TESTING','DISABLED')", name='ck_strategy_status'), Index('ix_strategies_user', 'user_id', 'created_at'))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='DRAFT')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class StrategyVersion(Base):
    __tablename__ = 'strategy_versions'
    __table_args__ = (UniqueConstraint('strategy_id', 'version', name='uq_strategy_version'), CheckConstraint('version > 0', name='ck_version_positive'), CheckConstraint("trade_direction IN ('CALL','PUT')", name='ck_version_direction'))
    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey('strategies.id'))
    version: Mapped[int] = mapped_column(Integer)
    strategy_dsl_version: Mapped[str] = mapped_column(String(50))
    feature_engine_version: Mapped[str] = mapped_column(String(50))
    trade_direction: Mapped[str] = mapped_column(String(10))
    indicator_specs: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    condition_tree: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    definition_sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BacktestRun(Base):
    __tablename__ = 'backtest_runs'
    __table_args__ = (Index('ix_backtest_runs_user_created', 'user_id', 'created_at'),
                      CheckConstraint("status IN ('RUNNING','COMPLETED','FAILED')", name='ck_run_status'),
                      CheckConstraint('expiry_bars BETWEEN 1 AND 60', name='ck_run_expiry'),
                      CheckConstraint('payout_percent > 0 AND payout_percent <= 100', name='ck_run_payout'),
                      CheckConstraint('signal_end > signal_start', name='ck_run_range'),
                      CheckConstraint('as_of_candle_id >= 0', name='ck_run_asof'),
                      CheckConstraint("entry_model = 'NEXT_CANDLE_OPEN'", name='ck_run_entry'),
                      CheckConstraint("overlap_policy IN ('ALLOW','SKIP_UNTIL_EXPIRY')", name='ck_run_overlap'))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    strategy_version_id: Mapped[int] = mapped_column(ForeignKey('strategy_versions.id'))
    status: Mapped[str] = mapped_column(String(20), default='RUNNING')
    backtest_engine_version: Mapped[str] = mapped_column(String(50))
    strategy_dsl_version: Mapped[str] = mapped_column(String(50))
    feature_engine_version: Mapped[str] = mapped_column(String(50))
    dataset: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    as_of_candle_id: Mapped[int] = mapped_column(Integer)
    signal_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    signal_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payout_percent: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    expiry_bars: Mapped[int] = mapped_column(Integer)
    entry_model: Mapped[str] = mapped_column(String(30))
    overlap_policy: Mapped[str] = mapped_column(String(30))
    strategy_snapshot: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    config_snapshot: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    config_sha256: Mapped[str] = mapped_column(String(64))
    metrics: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    equity_curve: Mapped[list | None] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BacktestTrade(Base):
    __tablename__ = 'backtest_trades'
    __table_args__ = (UniqueConstraint('backtest_run_id', 'sequence_no', name='uq_backtest_trade_sequence'),
                      Index('ix_backtest_trade_signal', 'backtest_run_id', 'signal_time'),
                      CheckConstraint('sequence_no > 0', name='ck_trade_sequence'),
                      CheckConstraint('entry_time >= signal_time AND expiry_time > entry_time', name='ck_trade_causality'),
                      CheckConstraint("direction IN ('CALL','PUT')", name='ck_backtest_direction'),
                      CheckConstraint("result IN ('WIN','LOSS','DRAW')", name='ck_backtest_result'))
    id: Mapped[int] = mapped_column(primary_key=True)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey('backtest_runs.id'))
    sequence_no: Mapped[int] = mapped_column(Integer)
    signal_candle_id: Mapped[int] = mapped_column(ForeignKey('candles.id'))
    entry_candle_id: Mapped[int] = mapped_column(ForeignKey('candles.id'))
    expiry_candle_id: Mapped[int] = mapped_column(ForeignKey('candles.id'))
    signal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expiry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    expiry_price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    direction: Mapped[str] = mapped_column(String(10))
    result: Mapped[str] = mapped_column(String(10))
    payout_percent: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    unit_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    signal_context: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), 'postgresql'))


def reject_research_mutation(mapper, connection, target):
    raise ValueError('Immutable research evidence cannot be updated or deleted')


for _model in (StrategyVersion, BacktestTrade):
    event.listen(_model, 'before_update', reject_research_mutation)
    event.listen(_model, 'before_delete', reject_research_mutation)


@event.listens_for(BacktestRun, 'before_update')
def guard_run_transition(mapper, connection, target):
    old = connection.scalar(select(BacktestRun.__table__.c.status).where(BacktestRun.__table__.c.id == target.id))
    changed = {a.key for a in inspect(target).attrs if a.history.has_changes()}
    allowed = {'status', 'completed_at', 'error_summary', 'metrics', 'equity_curve'}
    if old != 'RUNNING' or target.status not in ('COMPLETED','FAILED') or not changed <= allowed:
        raise ValueError('Backtest evidence permits only RUNNING to COMPLETED/FAILED transition')


event.listen(BacktestRun, 'before_delete', reject_research_mutation)
