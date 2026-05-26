"""growth features: coupons, referrals, vip tiers, daily rewards

Revision ID: 20260525_07
Revises: 20260525_06
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_07'
down_revision = '20260525_06'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('discount_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('referrer_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('referred_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('reward_percent', sa.Numeric(5, 2), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'daily_rewards',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reward_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('user_id', 'reward_date', name='uq_user_reward_date'),
    )


def downgrade() -> None:
    op.drop_table('daily_rewards')
    op.drop_table('referrals')
    op.drop_table('coupons')
