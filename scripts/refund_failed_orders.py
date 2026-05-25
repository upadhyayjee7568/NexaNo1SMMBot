"""Auto-refund failed orders into wallet (idempotent by ledger reference)."""
from __future__ import annotations

from app.db.models import Order, WalletLedger
from app.db.session import SessionLocal
from app.services.refund_engine import TERMINAL_FAILED_STATES
from app.services.wallet import add_ledger_entry


def run() -> None:
    db = SessionLocal()
    refunded = 0
    try:
        orders = db.query(Order).filter(Order.status.in_(list(TERMINAL_FAILED_STATES))).all()
        for o in orders:
            ref = f"refund:{o.client_order_id}"
            exists = (
                db.query(WalletLedger)
                .filter(
                    WalletLedger.user_id == o.user_id,
                    WalletLedger.reference_id == ref,
                    WalletLedger.entry_type == "refund",
                )
                .first()
            )
            if exists:
                continue
            add_ledger_entry(
                db,
                user_id=o.user_id,
                entry_type="refund",
                amount=o.charge_amount,
                reference_id=ref,
                note="Auto refund for failed/cancelled order",
            )
            refunded += 1
        db.commit()
    finally:
        db.close()
    print(f"Auto-refund completed. Refunded orders: {refunded}")


if __name__ == "__main__":
    run()
