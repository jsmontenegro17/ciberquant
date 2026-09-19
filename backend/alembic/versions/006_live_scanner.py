"""REQ-007 read-only live provenance, private scanner config/events/paper evidence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "006_live_scanner"
down_revision = "005_validation"


def upgrade():
    j, dt = sa.JSON().with_variant(JSONB(), "postgresql"), sa.DateTime(timezone=True)

    def col(k, t, nullable=False, **kw):
        return sa.Column(k, t, nullable=nullable, **kw)

    def ident():
        return sa.Column("id", sa.Integer, primary_key=True)

    def fk(k, target):
        return sa.Column(k, sa.Integer, sa.ForeignKey(target), nullable=False)

    op.create_table(
        "scanner_watchlists",
        ident(),
        fk("user_id", "users.id"),
        col("name", sa.String(120)),
        col("enabled", sa.Boolean),
        col("created_at", dt),
    )
    op.create_index("ix_scanner_watchlists_user_id", "scanner_watchlists", ["user_id"])
    op.create_table(
        "scanner_watch_items",
        ident(),
        fk("user_id", "users.id"),
        fk("watchlist_id", "scanner_watchlists.id"),
        fk("strategy_version_id", "strategy_versions.id"),
        col("provider", sa.String(20)),
        col("dataset", j),
        col("subscription_key", sa.String(64)),
        col("research_mode", sa.Boolean),
        col("research_payout", sa.Numeric(12, 6), True),
        col("research_expiry", sa.Integer, True),
        col("enabled", sa.Boolean),
        col("state", sa.String(40)),
        col("latest", j, True),
        col("updated_at", dt),
        col("created_at", dt),
        sa.UniqueConstraint("watchlist_id", "subscription_key", "strategy_version_id", name="uq_scanner_item"),
        sa.CheckConstraint("provider IN ('REPLAY','MT5','IQOPTION')", name="ck_scanner_provider"),
    )
    op.create_index("ix_scanner_watch_items_user_id", "scanner_watch_items", ["user_id"])
    op.create_table(
        "live_subscriptions",
        sa.Column("key", sa.String(64), primary_key=True),
        col("provider", sa.String(20)),
        col("dataset", j),
        col("status", sa.String(30)),
        col("health", j),
        col("snapshot", j, True),
        col("updated_at", dt),
    )
    op.create_table(
        "live_observations",
        ident(),
        fk("candle_id", "candles.id"),
        col("provider", sa.String(20)),
        col("mode", sa.String(10)),
        col("phase", sa.String(20)),
        col("provider_timestamp", dt),
        col("received_at", dt),
        sa.UniqueConstraint("provider", "candle_id", "mode", "phase", name="uq_live_observation"),
        sa.CheckConstraint("mode IN ('LIVE','REPLAY') AND phase IN ('BOOTSTRAP','OBSERVED')", name="ck_live_provenance"),
    )
    op.create_table(
        "scanner_events",
        ident(),
        fk("user_id", "users.id"),
        fk("watch_item_id", "scanner_watch_items.id"),
        fk("strategy_version_id", "strategy_versions.id"),
        col("dataset", j),
        *[
            col(k, sa.String(50))
            for k in ("scanner_engine_version", "feature_engine_version", "strategy_dsl_version", "live_data_engine_version")
        ],
        fk("signal_candle_id", "candles.id"),
        col("signal_time", dt),
        col("state", sa.String(30)),
        col("mode", sa.String(10)),
        col("direction", sa.String(10)),
        col("signal_context", j),
        col("validation_state_snapshot", sa.String(30)),
        col("current_payout", sa.Numeric(12, 6), True),
        col("evidence", j),
        col("provider_timestamp", dt),
        col("received_at", dt),
        col("created_at", dt),
        sa.UniqueConstraint("watch_item_id", "strategy_version_id", "signal_time", "state", name="uq_scanner_event"),
        sa.CheckConstraint(
            "state IN ('MATCH','NO_MATCH','UNAVAILABLE','STALE','INSUFFICIENT_HISTORY','PROVIDER_DOWN')", name="ck_scanner_event_state"
        ),
        sa.CheckConstraint("mode IN ('LIVE','REPLAY')", name="ck_scanner_event_mode"),
    )
    op.create_index("ix_scanner_events_user_id", "scanner_events", ["user_id"])
    op.create_table(
        "scanner_outcomes",
        ident(),
        fk("scanner_event_id", "scanner_events.id"),
        col("result", sa.String(20)),
        col("evidence", j),
        col("created_at", dt),
        sa.UniqueConstraint("scanner_event_id", name="uq_scanner_outcome"),
        sa.CheckConstraint("result IN ('WIN','LOSS','DRAW','UNAVAILABLE','GAP')", name="ck_scanner_outcome"),
    )


def downgrade():
    for table in (
        "scanner_outcomes",
        "scanner_events",
        "live_observations",
        "live_subscriptions",
        "scanner_watch_items",
        "scanner_watchlists",
    ):
        op.drop_table(table)
