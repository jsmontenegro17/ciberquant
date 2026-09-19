"""REQ-003: broker-aware feed identity and import provenance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "003_market_data"
down_revision = "002_req002_session_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "market_data_imports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("ingestion_method", sa.String(20), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("broker", sa.String(120), nullable=False),
        sa.Column("symbol", sa.String(50), nullable=False),
        sa.Column("market_type", sa.String(20), nullable=False),
        sa.Column("timeframe", sa.String(20), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        *[
            sa.Column(n, sa.Integer, nullable=False)
            for n in ("rows_received", "rows_valid", "rows_inserted", "rows_duplicates", "rows_rejected", "rows_conflicting")
        ],
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_summary", sa.JSON().with_variant(JSONB(), "postgresql")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_market_data_imports_created_at", "market_data_imports", ["created_at", "id"])
    # Canonicalize dataset metadata only; never change OHLC/timestamps. PostgreSQL
    # rolls the migration back if normalization introduces an identity collision.
    op.execute("UPDATE candles SET broker = COALESCE(NULLIF(UPPER(TRIM(broker)), ''), 'UNSPECIFIED')")
    with op.batch_alter_table("candles") as batch:
        batch.drop_constraint("uq_candle_identity", type_="unique")
    op.execute("UPDATE candles SET source = UPPER(TRIM(source)), symbol = UPPER(TRIM(symbol)), market_type = UPPER(TRIM(market_type))")
    op.execute("""UPDATE candles SET timeframe = CASE LOWER(TRIM(timeframe))
        WHEN 'm1' THEN '1m' WHEN 'm5' THEN '5m' WHEN 'm15' THEN '15m'
        WHEN 'm30' THEN '30m' WHEN 'h1' THEN '1h' ELSE LOWER(TRIM(timeframe)) END""")
    with op.batch_alter_table("candles") as batch:
        batch.alter_column("broker", existing_type=sa.String(120), nullable=False, server_default="UNSPECIFIED")
        batch.add_column(sa.Column("import_id", sa.Integer, nullable=True))
        batch.create_foreign_key("fk_candle_import", "market_data_imports", ["import_id"], ["id"])
        batch.create_unique_constraint("uq_candle_identity", ["source", "broker", "symbol", "market_type", "timeframe", "open_time"])


def downgrade():
    collision = (
        op.get_bind()
        .execute(sa.text("SELECT 1 FROM candles GROUP BY source, symbol, market_type, timeframe, open_time HAVING COUNT(*) > 1 LIMIT 1"))
        .first()
    )
    if collision:
        raise RuntimeError("Downgrade refused: broker-less identity would collide. Export/backup and resolve explicitly.")
    with op.batch_alter_table("candles") as batch:
        batch.drop_constraint("uq_candle_identity", type_="unique")
        batch.drop_constraint("fk_candle_import", type_="foreignkey")
        batch.drop_column("import_id")
        batch.alter_column("broker", existing_type=sa.String(120), nullable=True, server_default=None)
        batch.create_unique_constraint("uq_candle_identity", ["source", "symbol", "market_type", "timeframe", "open_time"])
    op.drop_index("ix_market_data_imports_created_at", table_name="market_data_imports")
    op.drop_table("market_data_imports")
