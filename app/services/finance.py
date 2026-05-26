from __future__ import annotations

from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import JournalEntry, JournalLine


def post_double_entry(
    db: Session,
    entry_ref: str,
    description: str,
    debit_account: str,
    credit_account: str,
    amount: Decimal,
    user_id: int | None = None,
    currency: str = "INR",
) -> JournalEntry:
    amt = abs(Decimal(amount))
    entry = JournalEntry(entry_ref=entry_ref, description=description)
    db.add(entry)
    db.flush()

    db.add(
        JournalLine(
            entry_id=entry.id,
            account_code=debit_account,
            direction="debit",
            amount=amt,
            currency=currency,
            user_id=user_id,
        )
    )
    db.add(
        JournalLine(
            entry_id=entry.id,
            account_code=credit_account,
            direction="credit",
            amount=amt,
            currency=currency,
            user_id=user_id,
        )
    )
    db.flush()
    return entry


def fetch_finance_daily_report(db: Session) -> list[dict]:
    rows = db.execute(text("SELECT report_day, entry_type, currency, tx_count, total_amount FROM finance_daily_report")).fetchall()
    return [
        {
            "report_day": str(r[0]),
            "entry_type": r[1],
            "currency": r[2],
            "tx_count": int(r[3]),
            "total_amount": str(r[4]),
        }
        for r in rows
    ]
