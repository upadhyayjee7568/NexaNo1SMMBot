from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import WalletLedger

DEBIT_TYPES = {"debit"}
CREDIT_TYPES = {"credit", "refund"}


def _normalized_amount(entry_type: str, amount: Decimal) -> Decimal:
    amt = abs(Decimal(amount))
    if entry_type in DEBIT_TYPES:
        return -amt
    if entry_type in CREDIT_TYPES:
        return amt
    return amt


def wallet_balance(session: Session, user_id: int) -> Decimal:
    stmt = select(func.coalesce(func.sum(WalletLedger.amount), 0)).where(WalletLedger.user_id == user_id)
    return Decimal(session.scalar(stmt) or 0)


def add_ledger_entry(
    session: Session,
    user_id: int,
    entry_type: str,
    amount: Decimal,
    reference_id: str | None = None,
    note: str | None = None,
) -> WalletLedger:
    entry = WalletLedger(
        user_id=user_id,
        entry_type=entry_type,
        amount=_normalized_amount(entry_type, amount),
def add_ledger_entry(session: Session, user_id: int, entry_type: str, amount: Decimal, reference_id: str | None = None, note: str | None = None) -> WalletLedger:
    entry = WalletLedger(
        user_id=user_id,
        entry_type=entry_type,
        amount=amount,
        reference_id=reference_id,
        note=note,
    )
    session.add(entry)
    session.flush()
    return entry
