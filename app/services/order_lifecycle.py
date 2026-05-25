from __future__ import annotations

from app.db.models import Order
from app.services.providers import ProviderClient
from app.core.settings import settings


STATUS_MAP = {
    "pending": "pending",
    "in progress": "processing",
    "processing": "processing",
    "partial": "partial",
    "completed": "completed",
    "complete": "completed",
    "canceled": "cancelled",
    "cancelled": "cancelled",
    "failed": "failed",
}


def _provider_for(order: Order) -> ProviderClient:
    if order.provider_name == "JustAnotherPanel":
        return ProviderClient(order.provider_name, settings.provider_1_base_url, settings.provider_1_api_key)
    return ProviderClient(order.provider_name, settings.provider_2_base_url, settings.provider_2_api_key)


def normalize_status(raw: str | None) -> str:
    if not raw:
        return "unknown"
    return STATUS_MAP.get(raw.lower(), raw.lower())


async def refresh_order_status(order: Order) -> str:
    client = _provider_for(order)
    if not client.api_key or not order.provider_order_id:
        return order.status
    result = await client.status(order.provider_order_id)
    new_status = normalize_status(result.get("status"))
    if new_status != "unknown":
        order.status = new_status
    return order.status


async def request_refill(order: Order) -> dict:
    client = _provider_for(order)
    if not client.api_key or not order.provider_order_id:
        return {"ok": False, "error": "missing_provider_credentials_or_order_id"}
    return await client.refill(order.provider_order_id)


async def request_cancel(order: Order) -> dict:
    client = _provider_for(order)
    if not client.api_key or not order.provider_order_id:
        return {"ok": False, "error": "missing_provider_credentials_or_order_id"}
    return await client.cancel(order.provider_order_id)
