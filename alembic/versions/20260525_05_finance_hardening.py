"""finance hardening: immutable ledger, double-entry journal, finance report view

Revision ID: 20260525_05
Revises: 20260525_04
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '20260525_05'
down_revision = '20260525_04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'journal_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_ref', sa.String(length=128), nullable=False, index=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('entry_ref', name='uq_journal_entry_ref'),
    )
    op.create_table(
        'journal_lines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entry_id', sa.Integer(), sa.ForeignKey('journal_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_code', sa.String(length=64), nullable=False),
        sa.Column('direction', sa.String(length=8), nullable=False),  # debit|credit
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_journal_lines_entry_id', 'journal_lines', ['entry_id'])
    op.create_index('ix_journal_lines_account_code', 'journal_lines', ['account_code'])

    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_wallet_ledger_mutation()
    RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'wallet_ledger is immutable; updates/deletes are not allowed';
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS wallet_ledger_no_update ON wallet_ledger;
    CREATE TRIGGER wallet_ledger_no_update
    BEFORE UPDATE ON wallet_ledger
    FOR EACH ROW
    EXECUTE FUNCTION prevent_wallet_ledger_mutation();
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS wallet_ledger_no_delete ON wallet_ledger;
    CREATE TRIGGER wallet_ledger_no_delete
    BEFORE DELETE ON wallet_ledger
    FOR EACH ROW
    EXECUTE FUNCTION prevent_wallet_ledger_mutation();
    """)

    op.execute("""
    CREATE OR REPLACE VIEW finance_daily_report AS
    SELECT
      date_trunc('day', created_at) AS report_day,
      entry_type,
      currency,
      COUNT(*) AS tx_count,
      SUM(amount) AS total_amount
    FROM wallet_ledger
    GROUP BY 1,2,3
    ORDER BY 1 DESC;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS finance_daily_report")
    op.execute("DROP TRIGGER IF EXISTS wallet_ledger_no_update ON wallet_ledger")
    op.execute("DROP TRIGGER IF EXISTS wallet_ledger_no_delete ON wallet_ledger")
    op.execute("DROP FUNCTION IF EXISTS prevent_wallet_ledger_mutation")
    op.drop_index('ix_journal_lines_account_code', table_name='journal_lines')
    op.drop_index('ix_journal_lines_entry_id', table_name='journal_lines')
    op.drop_table('journal_lines')
    op.drop_table('journal_entries')
