"""anti-fraud tables and risk flags

Revision ID: 20260526_08
Revises: 20260525_07
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa

revision = '20260526_08'
down_revision = '20260525_07'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'fraud_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_fraud_events_user_id', 'fraud_events', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_fraud_events_user_id', table_name='fraud_events')
    op.drop_table('fraud_events')
