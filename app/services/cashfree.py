"""Cashfree payment-link creation.

Creates a hosted Cashfree payment link for wallet top-ups. The webhook handler in
``app/api/routes.py`` credits the wallet once Cashfree calls back with a PAID status.

If link creation fails for any reason (missing credentials, network error, gateway
down, non-2xx response) a ``CashfreeError`` is raised so the caller can fall back to
the UPI QR flow.
"""

from __future__ import annotations

from decimal import Decimal
from secrets import token_hex

import httpx

from app.core.settings import settings

API_VERSION = "2023-08-01"


class CashfreeError(Exception):
    pass


def _base_url() -> str:
    if settings.cashfree_mode.upper() == "TEST":
        return "https://sandbox.cashfree.com/pg"
    return "https://api.cashfree.com/pg"


def is_configured() -> bool:
    return bool(
        settings.payment_gateway.lower() == "cashfree"
        and settings.cashfree_app_id
        and settings.cashfree_secret_key
    )


async def create_payment_link(telegram_id: int, amount: Decimal, phone: str | None = None) -> dict:
    """Create a Cashfree payment link. Returns {link_url, link_id}. Raises CashfreeError."""
    if not is_configured():
        raise CashfreeError("Cashfree is not configured")

    amount = Decimal(amount).quantize(Decimal("0.01"))
    link_id = f"NEXA{telegram_id}-{token_hex(4)}"
    return_url = f"{settings.public_base_url.rstrip('/')}/app" if settings.public_base_url else None
    notify_url = (
        f"{settings.public_base_url.rstrip('/')}/api/payments/cashfree/webhook"
        if settings.public_base_url
        else None
    )

    payload: dict = {
        "link_id": link_id,
        "link_amount": float(amount),
        "link_currency": "INR",
        "link_purpose": "Nexa SMM wallet top-up",
        "customer_details": {
            "customer_id": str(telegram_id),
            "customer_phone": phone or "9999999999",
        },
        "link_notify": {"send_sms": False, "send_email": False},
        "link_auto_reminders": False,
        "link_meta": {},
    }
    if return_url:
        payload["link_meta"]["return_url"] = return_url
    if notify_url:
        payload["link_meta"]["notify_url"] = notify_url

    headers = {
        "x-client-id": settings.cashfree_app_id,
        "x-client-secret": settings.cashfree_secret_key,
        "x-api-version": API_VERSION,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.provider_timeout_seconds) as client:
            resp = await client.post(f"{_base_url()}/links", json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise CashfreeError(f"network_error: {exc}") from exc

    if resp.status_code >= 300:
        raise CashfreeError(f"cashfree_http_{resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    link_url = data.get("link_url")
    if not link_url:
        raise CashfreeError(f"no_link_url: {data}")
    return {"link_url": link_url, "link_id": data.get("link_id", link_id)}
