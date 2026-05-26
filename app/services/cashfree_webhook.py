import hashlib
import hmac
import json
from fastapi import HTTPException

from app.core.settings import settings


def verify_cashfree_signature(raw_body: bytes, signature: str | None) -> None:
    if not settings.cashfree_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    digest = hmac.new(settings.cashfree_webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


def is_success_event(order_status: str | None) -> bool:
    return bool(order_status and order_status.upper() in {"PAID", "SUCCESS"})


def extract_event_id(payload: dict) -> str:
    for key in ("cf_payment_id", "payment_id", "event_id", "order_id"):
        val = payload.get(key)
        if val:
            return str(val)
    raise HTTPException(status_code=400, detail="Missing event/payment ID in webhook payload")


def safe_dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
