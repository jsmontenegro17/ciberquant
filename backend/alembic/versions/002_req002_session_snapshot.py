from alembic import op
import sqlalchemy as sa
revision='002_req002_session_snapshot'; down_revision='001_initial'; branch_labels=None; depends_on=None
def upgrade():
    op.add_column('trading_sessions', sa.Column('minimum_payout_percent', sa.Numeric(8,4), nullable=False, server_default='0'))
def downgrade(): op.drop_column('trading_sessions','minimum_payout_percent')
