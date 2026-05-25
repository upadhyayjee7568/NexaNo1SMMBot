"""add service catalog table

Revision ID: 20260525_03
Revises: 20260525_02
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_03'
down_revision = '20260525_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'service_catalog',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider_name', sa.String(length=64), nullable=False),
        sa.Column('provider_service_id', sa.String(length=64), nullable=False),
        sa.Column('platform', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=128), nullable=True),
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('base_rate', sa.Numeric(12, 6), nullable=False, server_default='0'),
        sa.Column('min_qty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('max_qty', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('provider_name', 'provider_service_id', name='uq_provider_service'),
    )
    op.create_index('ix_service_catalog_provider_name', 'service_catalog', ['provider_name'])
    op.create_index('ix_service_catalog_platform', 'service_catalog', ['platform'])


def downgrade() -> None:
    op.drop_index('ix_service_catalog_platform', table_name='service_catalog')
    op.drop_index('ix_service_catalog_provider_name', table_name='service_catalog')
    op.drop_table('service_catalog')
