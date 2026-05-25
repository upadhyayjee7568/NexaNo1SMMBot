import hmac
import hashlib
from fastapi import HTTPException
from fastapi import Header, HTTPException

from app.core.settings import settings


def verify_cashfree_signature(raw_body: bytes, signature: str | None) -> None:
    if not settings.cashfree_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    digest = hmac.new(
        settings.cashfree_webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


def is_success_event(order_status: str | None) -> bool:
    if not order_status:
        return False
    return order_status.upper() in {"PAID", "SUCCESS"}
