"""web auth sessions

Revision ID: 20260526_09
Revises: 20260526_08
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa

revision = '20260526_09'
down_revision = '20260526_08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'web_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_token', sa.String(length=128), nullable=False, unique=True),
        sa.Column('csrf_token', sa.String(length=128), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_web_sessions_user_id', 'web_sessions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_web_sessions_user_id', table_name='web_sessions')
    op.drop_table('web_sessions')
