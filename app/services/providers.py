from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ProviderClient:
    name: str
    base_url: str
    api_key: str

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(self.base_url, data=payload)
            r.raise_for_status()
            return r.json()

    async def create_order(self, service: int, link: str, quantity: int) -> dict[str, Any]:
        result = await self._request(
            {
                "key": self.api_key,
                "action": "add",
                "service": service,
                "link": link,
                "quantity": quantity,
            }
        )
        return result if isinstance(result, dict) else {"status": "error", "raw": result}

    async def status(self, order: str) -> dict[str, Any]:
        result = await self._request({"key": self.api_key, "action": "status", "order": order})
        return result if isinstance(result, dict) else {"status": "error", "raw": result}

    async def services(self) -> list[dict[str, Any]]:
        result = await self._request({"key": self.api_key, "action": "services"})
        return result if isinstance(result, list) else []

    async def refill(self, order: str) -> dict[str, Any]:
        result = await self._request({"key": self.api_key, "action": "refill", "order": order})
        return result if isinstance(result, dict) else {"status": "error", "raw": result}

    async def cancel(self, order: str) -> dict[str, Any]:
        result = await self._request({"key": self.api_key, "action": "cancel", "order": order})
        return result if isinstance(result, dict) else {"status": "error", "raw": result}
