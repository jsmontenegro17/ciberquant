"""REQ-005 private immutable strategy versions and derived backtest evidence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "004_strategy_backtesting"
down_revision = "003_market_data"
branch_labels = depends_on = None


def upgrade():
    j = sa.JSON().with_variant(JSONB(), "postgresql")
    dt = sa.DateTime(timezone=True)
    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", dt, nullable=False),
        sa.Column("updated_at", dt, nullable=False),
        sa.CheckConstraint("status IN ('DRAFT','TESTING','DISABLED')", name="ck_strategy_status"),
    )
    op.create_index("ix_strategies_user", "strategies", ["user_id", "created_at"])
    op.create_table(
        "strategy_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("strategy_id", sa.Integer, sa.ForeignKey("strategies.id"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("strategy_dsl_version", sa.String(50), nullable=False),
        sa.Column("feature_engine_version", sa.String(50), nullable=False),
        sa.Column("trade_direction", sa.String(10), nullable=False),
        sa.Column("indicator_specs", j, nullable=False),
        sa.Column("condition_tree", j, nullable=False),
        sa.Column("definition_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", dt, nullable=False),
        sa.UniqueConstraint("strategy_id", "version", name="uq_strategy_version"),
        sa.CheckConstraint("version > 0", name="ck_version_positive"),
        sa.CheckConstraint("trade_direction IN ('CALL','PUT')", name="ck_version_direction"),
    )
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_version_id", sa.Integer, sa.ForeignKey("strategy_versions.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *[
            sa.Column(k, sa.String(50), nullable=False)
            for k in ("backtest_engine_version", "strategy_dsl_version", "feature_engine_version")
        ],
        sa.Column("dataset", j, nullable=False),
        sa.Column("as_of_candle_id", sa.Integer, nullable=False),
        sa.Column("signal_start", dt, nullable=False),
        sa.Column("signal_end", dt, nullable=False),
        sa.Column("payout_percent", sa.Numeric(12, 6), nullable=False),
        sa.Column("expiry_bars", sa.Integer, nullable=False),
        sa.Column("entry_model", sa.String(30), nullable=False),
        sa.Column("overlap_policy", sa.String(30), nullable=False),
        sa.Column("strategy_snapshot", j, nullable=False),
        sa.Column("config_snapshot", j, nullable=False),
        sa.Column("config_sha256", sa.String(64), nullable=False),
        sa.Column("metrics", j),
        sa.Column("equity_curve", j),
        sa.Column("started_at", dt, nullable=False),
        sa.Column("completed_at", dt),
        sa.Column("created_at", dt, nullable=False),
        sa.Column("error_summary", sa.String(500)),
        sa.CheckConstraint("status IN ('RUNNING','COMPLETED','FAILED')", name="ck_run_status"),
        sa.CheckConstraint("expiry_bars BETWEEN 1 AND 60", name="ck_run_expiry"),
        sa.CheckConstraint("payout_percent > 0 AND payout_percent <= 100", name="ck_run_payout"),
        sa.CheckConstraint("signal_end > signal_start", name="ck_run_range"),
        sa.CheckConstraint("as_of_candle_id >= 0", name="ck_run_asof"),
        sa.CheckConstraint("entry_model = 'NEXT_CANDLE_OPEN'", name="ck_run_entry"),
        sa.CheckConstraint("overlap_policy IN ('ALLOW','SKIP_UNTIL_EXPIRY')", name="ck_run_overlap"),
    )
    op.create_index("ix_backtest_runs_user_created", "backtest_runs", ["user_id", "created_at"])
    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("backtest_run_id", sa.Integer, sa.ForeignKey("backtest_runs.id"), nullable=False),
        sa.Column("sequence_no", sa.Integer, nullable=False),
        *[
            sa.Column(k, sa.Integer, sa.ForeignKey("candles.id"), nullable=False)
            for k in ("signal_candle_id", "entry_candle_id", "expiry_candle_id")
        ],
        *[sa.Column(k, dt, nullable=False) for k in ("signal_time", "entry_time", "expiry_time")],
        *[sa.Column(k, sa.Numeric(24, 10), nullable=False) for k in ("entry_price", "expiry_price")],
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("result", sa.String(10), nullable=False),
        sa.Column("payout_percent", sa.Numeric(12, 6), nullable=False),
        sa.Column("unit_pnl", sa.Numeric(18, 8), nullable=False),
        sa.Column("signal_context", j, nullable=False),
        sa.UniqueConstraint("backtest_run_id", "sequence_no", name="uq_backtest_trade_sequence"),
        sa.CheckConstraint("sequence_no > 0", name="ck_trade_sequence"),
        sa.CheckConstraint("entry_time >= signal_time AND expiry_time > entry_time", name="ck_trade_causality"),
        sa.CheckConstraint("direction IN ('CALL','PUT')", name="ck_backtest_direction"),
        sa.CheckConstraint("result IN ('WIN','LOSS','DRAW')", name="ck_backtest_result"),
    )
    op.create_index("ix_backtest_trade_signal", "backtest_trades", ["backtest_run_id", "signal_time"])


def downgrade():
    # Explicit downgrade discards derived evidence; backup/export before use.
    for table in ("backtest_trades", "backtest_runs", "strategy_versions", "strategies"):
        op.drop_table(table)
