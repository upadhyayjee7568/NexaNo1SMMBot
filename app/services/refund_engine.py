from __future__ import annotations

from decimal import Decimal

from app.db.models import Order
from app.services.wallet import add_ledger_entry

TERMINAL_FAILED_STATES = {"failed", "canceled", "cancelled", "partial"}


def auto_refund_if_failed(db, order: Order) -> bool:
    """Refund order amount to wallet when order reaches failed-like terminal state.

    Returns True if refund was created, else False.
    """
    if order.status.lower() not in TERMINAL_FAILED_STATES:
        return False

    existing_ref = (
        db.query(order.__class__)
        .filter(order.__class__.client_order_id == order.client_order_id)
        .first()
    )
    if not existing_ref:
        return False

    refund_ref = f"refund:{order.client_order_id}"
    # idempotency by reference_id in wallet ledger will be enforced by query in sync script
    add_ledger_entry(
        db,
        user_id=order.user_id,
        entry_type="refund",
        amount=Decimal(str(order.charge_amount)),
        reference_id=refund_ref,
        note="Auto refund for failed/cancelled order",
    )
    return True
