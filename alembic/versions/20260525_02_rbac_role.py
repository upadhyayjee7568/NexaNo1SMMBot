"""add role column to users

Revision ID: 20260525_02
Revises: 20260525_01
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_02'
down_revision = '20260525_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(length=24), nullable=False, server_default='user'))


def downgrade() -> None:
    op.drop_column('users', 'role')
