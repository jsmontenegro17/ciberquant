"""REQ-006 immutable validation evidence and internal backtest purpose."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "005_validation"
down_revision = "004_strategy_backtesting"


def upgrade():
    with op.batch_alter_table("backtest_runs") as batch:
        batch.add_column(sa.Column("purpose", sa.String(20), nullable=False, server_default="MANUAL"))
        batch.create_check_constraint("ck_backtest_purpose", "purpose IN ('MANUAL','VALIDATION')")
    j, dt = sa.JSON().with_variant(JSONB(), "postgresql"), sa.DateTime(timezone=True)
    op.create_table(
        "validation_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_version_id", sa.Integer, sa.ForeignKey("strategy_versions.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("verdict", sa.String(20), nullable=False),
        *[
            sa.Column(k, sa.String(50), nullable=False)
            for k in ("validation_engine_version", "feature_engine_version", "strategy_dsl_version", "backtest_engine_version")
        ],
        sa.Column("definition_sha256", sa.String(64), nullable=False),
        sa.Column("dataset", j, nullable=False),
        sa.Column("as_of_candle_id", sa.Integer, nullable=False),
        *[
            sa.Column(k, dt, nullable=False)
            for k in (
                "overall_start",
                "overall_end",
                "train_start",
                "train_end",
                "validation_start",
                "validation_end",
                "test_start",
                "test_end",
            )
        ],
        sa.Column("payout_percent", sa.Numeric(12, 6), nullable=False),
        sa.Column("expiry_bars", sa.Integer, nullable=False),
        sa.Column("entry_model", sa.String(30), nullable=False),
        sa.Column("overlap_policy", sa.String(30), nullable=False),
        sa.Column("config_snapshot", j, nullable=False),
        sa.Column("config_sha256", sa.String(64), nullable=False),
        *[
            sa.Column(k, j)
            for k in ("development_summary", "walk_forward_summary", "test_summary", "bootstrap_summary", "temporal_stability", "gates")
        ],
        sa.Column("holdout_warnings", j, nullable=False),
        sa.Column("test_revealed_at", dt),
        sa.Column("started_at", dt, nullable=False),
        sa.Column("completed_at", dt),
        sa.Column("created_at", dt, nullable=False),
        sa.Column("error_summary", sa.String(500)),
        sa.CheckConstraint("status IN ('RUNNING_DEVELOPMENT','SEALED','RUNNING_TEST','COMPLETED','FAILED')", name="ck_validation_status"),
        sa.CheckConstraint("verdict IN ('PENDING_TEST','PASS','FAIL','INCONCLUSIVE')", name="ck_validation_verdict"),
        sa.CheckConstraint("validation_engine_version = 'cq-validation-v1'", name="ck_validation_engine"),
        sa.CheckConstraint(
            "feature_engine_version = 'cq-features-v1' AND strategy_dsl_version = 'cq-strategy-dsl-v1' AND backtest_engine_version = 'cq-binary-backtest-v1'",
            name="ck_validation_dependencies",
        ),
        sa.CheckConstraint(
            "overall_start = train_start AND train_start < train_end AND train_end = validation_start AND validation_start < validation_end AND validation_end = test_start AND test_start < test_end AND test_end = overall_end",
            name="ck_validation_ranges",
        ),
        sa.CheckConstraint(
            "as_of_candle_id >= 0 AND expiry_bars BETWEEN 1 AND 60 AND payout_percent > 0 AND payout_percent <= 100",
            name="ck_validation_parameters",
        ),
        sa.CheckConstraint(
            "entry_model = 'NEXT_CANDLE_OPEN' AND overlap_policy IN ('ALLOW','SKIP_UNTIL_EXPIRY')", name="ck_validation_execution"
        ),
        sa.CheckConstraint(
            "(status = 'COMPLETED' AND verdict <> 'PENDING_TEST' AND test_revealed_at IS NOT NULL) OR (status <> 'COMPLETED' AND verdict = 'PENDING_TEST')",
            name="ck_validation_final",
        ),
    )
    op.create_index("ix_validation_owner_version", "validation_runs", ["user_id", "strategy_version_id", "created_at"])
    op.create_table(
        "validation_segments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("validation_run_id", sa.Integer, sa.ForeignKey("validation_runs.id"), nullable=False),
        sa.Column("segment_type", sa.String(20), nullable=False),
        sa.Column("fold_number", sa.Integer, nullable=False),
        sa.Column("signal_start", dt, nullable=False),
        sa.Column("signal_end", dt, nullable=False),
        sa.Column("backtest_run_id", sa.Integer, sa.ForeignKey("backtest_runs.id")),
        sa.Column("created_at", dt, nullable=False),
        sa.UniqueConstraint("validation_run_id", "segment_type", "fold_number", name="uq_validation_segment"),
        sa.UniqueConstraint("backtest_run_id", name="uq_validation_child"),
        sa.CheckConstraint(
            "(segment_type = 'WALK_FORWARD' AND fold_number BETWEEN 1 AND 4) OR (segment_type IN ('TRAIN','VALIDATION','TEST') AND fold_number = 0)",
            name="ck_validation_segment_type",
        ),
        sa.CheckConstraint("signal_start < signal_end", name="ck_validation_segment_range"),
    )


def downgrade():
    # Destructive derived-evidence downgrade: export/backup first.
    op.drop_table("validation_segments")
    op.drop_table("validation_runs")
    with op.batch_alter_table("backtest_runs") as batch:
        batch.drop_constraint("ck_backtest_purpose", type_="check")
        batch.drop_column("purpose")
