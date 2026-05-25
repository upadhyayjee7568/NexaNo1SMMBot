"""initial schema

Revision ID: 20260525_01
Revises:
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=128), nullable=True),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)

    op.create_table('wallet_ledger',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('entry_type', sa.String(length=32), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('reference_id', sa.String(length=128), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table('orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('client_order_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('provider_order_id', sa.String(length=64), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('link', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('charge_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_orders_client_order_id', 'orders', ['client_order_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_orders_client_order_id', table_name='orders')
    op.drop_table('orders')
    op.drop_table('wallet_ledger')
    op.drop_index('ix_users_telegram_id', table_name='users')
    op.drop_table('users')
