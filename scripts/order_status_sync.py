"""Sync order statuses from providers for pending/created orders."""
from __future__ import annotations

import asyncio

from app.db.session import SessionLocal
from app.db.models import Order
from app.services.providers import ProviderClient
from app.core.settings import settings


async def sync_once() -> None:
    db = SessionLocal()
    try:
        pending = db.query(Order).filter(Order.status.in_(["created", "processing", "pending"])).all()
        for order in pending:
            provider = ProviderClient(
                order.provider_name,
                settings.provider_1_base_url if order.provider_name == "JustAnotherPanel" else settings.provider_2_base_url,
                settings.provider_1_api_key if order.provider_name == "JustAnotherPanel" else settings.provider_2_api_key,
            )
            if not provider.api_key or not order.provider_order_id:
                continue
            try:
                result = await provider.status(order.provider_order_id)
                new_status = (result.get("status") or "").lower()
                if new_status:
                    order.status = new_status
            except Exception:
                continue
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(sync_once())
    print("Order status sync complete")
