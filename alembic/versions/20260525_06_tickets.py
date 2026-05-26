"""add ticket support tables

Revision ID: 20260525_06
Revises: 20260525_05
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_06'
down_revision = '20260525_05'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tickets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticket_ref', sa.String(length=64), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='open'),
        sa.Column('priority', sa.String(length=16), nullable=False, server_default='normal'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_tickets_user_id', 'tickets', ['user_id'])

    op.create_table(
        'ticket_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticket_id', sa.Integer(), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_staff', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ticket_messages_ticket_id', 'ticket_messages', ['ticket_id'])


def downgrade() -> None:
    op.drop_index('ix_ticket_messages_ticket_id', table_name='ticket_messages')
    op.drop_table('ticket_messages')
    op.drop_index('ix_tickets_user_id', table_name='tickets')
    op.drop_table('tickets')
