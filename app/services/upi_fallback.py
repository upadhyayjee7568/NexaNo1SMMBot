"""UPI fallback payment flow.

Used automatically when the Cashfree gateway is disabled or unavailable. A UPI
``upi://pay`` deep link + QR code is generated for the admin UPI ID, the user pays
from any UPI app, then submits the bank UTR/reference number.

Flow (admin-verified):
  * The UTR column is UNIQUE -> the same reference can never be reused.
  * When the user submits a UTR the top-up moves to ``pending_review``.
  * An admin approves (credits the wallet) or rejects it from the admin panel / bot.
  * Every credit is written to the double-entry journal so it can be audited / reversed.
"""

from __future__ import annotations

import base64
import io
from decimal import Decimal
from secrets import token_hex
from urllib.parse import quote

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models import UpiTopup, User
from app.services.finance import post_double_entry
from app.services.wallet import add_ledger_entry


class UpiError(Exception):
    """Raised for user-facing UPI fallback errors."""


def _new_reference() -> str:
    return f"UPI{token_hex(6).upper()}"


def build_upi_uri(amount: Decimal, reference: str, note: str | None = None) -> str:
    if not settings.admin_upi_id:
        raise UpiError("UPI ID is not configured")
    params = [
        f"pa={quote(settings.admin_upi_id)}",
        f"pn={quote(settings.upi_payee_name)}",
        f"am={amount:.2f}",
        "cu=INR",
        f"tr={quote(reference)}",
        f"tn={quote(note or f'Wallet topup {reference}')}",
    ]
    return "upi://pay?" + "&".join(params)


def generate_qr_data_uri(payload: str) -> str:
    """Return a base64 PNG data URI for the given payload (for web/Telegram embedding)."""
    import qrcode

    qr = qrcode.QRCode(version=None, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def generate_qr_png_bytes(payload: str) -> bytes:
    import qrcode

    qr = qrcode.QRCode(version=None, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _ensure_user(db: Session, telegram_id: int) -> User:
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.flush()
    return user


def create_upi_topup(db: Session, telegram_id: int, amount: Decimal) -> tuple[UpiTopup, str, str]:
    """Create a pending UPI top-up. Returns (topup, upi_uri, qr_data_uri)."""
    if not settings.upi_fallback_enabled:
        raise UpiError("UPI fallback is disabled")
    amount = Decimal(amount).quantize(Decimal("0.01"))
    if amount < Decimal(str(settings.min_add_money_inr)):
        raise UpiError(f"Minimum add money is INR {settings.min_add_money_inr}")
    if amount > Decimal(str(settings.max_add_money_inr)):
        raise UpiError(f"Maximum add money is INR {settings.max_add_money_inr}")

    user = _ensure_user(db, telegram_id)
    reference = _new_reference()
    topup = UpiTopup(
        reference=reference,
        user_id=user.id,
        telegram_id=telegram_id,
        amount=amount,
        currency="INR",
        upi_id=settings.admin_upi_id,
        status="pending",
    )
    db.add(topup)
    db.commit()
    db.refresh(topup)

    uri = build_upi_uri(amount, reference, note=f"Topup {reference}")
    return topup, uri, generate_qr_data_uri(uri)


def credit_upi_topup(db: Session, topup: UpiTopup, by: str = "system") -> str:
    """Credit the wallet for a UPI top-up. Idempotent on the ledger reference."""
    if topup.status == "credited":
        return "already_credited"
    ref = f"upi:{topup.reference}"
    from app.db.models import WalletLedger

    already = (
        db.query(WalletLedger)
        .filter(
            WalletLedger.user_id == topup.user_id,
            WalletLedger.reference_id == ref,
            WalletLedger.entry_type == "credit",
        )
        .first()
    )
    if not already:
        add_ledger_entry(
            db,
            topup.user_id,
            "credit",
            Decimal(str(topup.amount)),
            reference_id=ref,
            note=f"UPI top-up (UTR {topup.utr}) approved by {by}",
        )
        post_double_entry(
            db,
            entry_ref=ref,
            description="Wallet topup via UPI fallback",
            debit_account="upi_clearing",
            credit_account="wallet_user",
            amount=Decimal(str(topup.amount)),
            user_id=topup.user_id,
        )
    topup.status = "credited"
    db.flush()
    return "credited"


def submit_utr(db: Session, reference: str, utr: str) -> tuple[UpiTopup, str]:
    """Attach a UTR to a top-up and hold it for manual admin approval.

    Returns (topup, status) where status is one of:
      pending_review | duplicate_utr | not_found | already_done
    """
    utr = (utr or "").strip()
    if not utr or len(utr) < 6:
        raise UpiError("Please send a valid UTR / reference number (min 6 chars)")

    topup = db.query(UpiTopup).filter(UpiTopup.reference == reference).first()
    if not topup:
        return None, "not_found"  # type: ignore[return-value]
    if topup.status in {"credited", "rejected"}:
        return topup, "already_done"

    # Reject reused UTRs (DB unique constraint is the source of truth).
    existing = db.query(UpiTopup).filter(UpiTopup.utr == utr, UpiTopup.id != topup.id).first()
    if existing:
        return topup, "duplicate_utr"

    topup.utr = utr
    topup.status = "pending_review"
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return topup, "duplicate_utr"

    db.commit()
    return topup, "pending_review"


def approve_topup(db: Session, reference: str, by: str = "admin") -> tuple[UpiTopup | None, str]:
    """Admin approves a pending UPI top-up and credits the wallet."""
    topup = db.query(UpiTopup).filter(UpiTopup.reference == reference).first()
    if not topup:
        return None, "not_found"
    if topup.status == "credited":
        return topup, "already_credited"
    if not topup.utr:
        return topup, "no_utr"
    status = credit_upi_topup(db, topup, by=by)
    db.commit()
    return topup, status


def reject_topup(db: Session, reference: str, by: str = "admin") -> tuple[UpiTopup | None, str]:
    """Admin rejects a UPI top-up. No wallet credit is made."""
    topup = db.query(UpiTopup).filter(UpiTopup.reference == reference).first()
    if not topup:
        return None, "not_found"
    if topup.status == "credited":
        return topup, "already_credited"
    topup.status = "rejected"
    db.commit()
    return topup, "rejected"


def list_pending(db: Session, limit: int = 50) -> list[UpiTopup]:
    return (
        db.query(UpiTopup)
        .filter(UpiTopup.status == "pending_review")
        .order_by(UpiTopup.id.desc())
        .limit(limit)
        .all()
    )
