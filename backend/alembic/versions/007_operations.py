"""REQ-008 operational worker heartbeat only; no historical evidence migration."""
from alembic import op
import sqlalchemy as sa

revision = '007_operations'
down_revision = '006_live_scanner'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('worker_heartbeats', sa.Column('name', sa.String(50), primary_key=True),
                    sa.Column('status', sa.String(20), nullable=False),
                    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table('worker_heartbeats')
