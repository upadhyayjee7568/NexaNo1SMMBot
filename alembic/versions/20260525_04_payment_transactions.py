"""add payment transactions table for webhook idempotency

Revision ID: 20260525_04
Revises: 20260525_03
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_04'
down_revision = '20260525_03'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('gateway', sa.String(length=32), nullable=False),
        sa.Column('gateway_event_id', sa.String(length=128), nullable=False),
        sa.Column('order_id', sa.String(length=128), nullable=True),
        sa.Column('telegram_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='received'),
        sa.Column('raw_payload', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('gateway', 'gateway_event_id', name='uq_gateway_event'),
    )
    op.create_index('ix_payment_transactions_gateway', 'payment_transactions', ['gateway'])
    op.create_index('ix_payment_transactions_gateway_event_id', 'payment_transactions', ['gateway_event_id'])


def downgrade() -> None:
    op.drop_index('ix_payment_transactions_gateway_event_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_gateway', table_name='payment_transactions')
    op.drop_table('payment_transactions')
