from __future__ import annotations

from uuid import uuid4
from typing import Any

from app.core.settings import settings
from app.services.providers import ProviderClient
from app.services.pricing import apply_markup


def _provider_clients() -> list[ProviderClient]:
    return [
        ProviderClient(
            name="JustAnotherPanel",
            base_url=settings.provider_1_base_url,
            api_key=settings.provider_1_api_key,
        ),
        ProviderClient(
            name="Peakerr API",
            base_url=settings.provider_2_base_url,
            api_key=settings.provider_2_api_key,
        ),
    ]


async def place_order(service_id: int, link: str, quantity: int, base_rate: float, category: str | None = None) -> dict[str, Any]:
    provider_errors: list[dict[str, str]] = []

    for provider in _provider_clients():
        if not provider.api_key:
            provider_errors.append({"provider": provider.name, "error": "missing_api_key"})
            continue

        try:
            result = await provider.create_order(service=service_id, link=link, quantity=quantity)
            if result.get("order"):
                charged = apply_markup(base_rate=base_rate, category=category) * quantity
                return {
                    "order_id": str(uuid4()),
                    "provider": provider.name,
                    "provider_order_id": str(result.get("order")),
                    "status": "created",
                    "charged_amount": round(charged, 2),
                    "currency": "INR",
                    "failover_attempts": provider_errors,
                }
            provider_errors.append({"provider": provider.name, "error": str(result)})
        except Exception as e:  # noqa: BLE001
            provider_errors.append({"provider": provider.name, "error": str(e)})

    return {
        "order_id": str(uuid4()),
        "provider": "none",
        "status": "failed",
        "charged_amount": 0,
        "currency": "INR",
        "errors": provider_errors,
    }
