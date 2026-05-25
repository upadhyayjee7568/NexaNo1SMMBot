"""Sync services catalog from providers.

Usage:
  python scripts/sync_services.py
"""
import asyncio
import json
from pathlib import Path

from app.core.settings import settings
from app.services.providers import ProviderClient

OUT_FILE = Path("data/provider_services_snapshot.json")


async def main() -> None:
    providers = [
        ProviderClient("JustAnotherPanel", settings.provider_1_base_url, settings.provider_1_api_key),
        ProviderClient("Peakerr API", settings.provider_2_base_url, settings.provider_2_api_key),
    ]

    snapshot: dict[str, list[dict]] = {}
    for p in providers:
        if not p.api_key:
            snapshot[p.name] = [{"error": "missing_api_key"}]
            continue
        try:
            snapshot[p.name] = await p.services()
        except Exception as exc:  # noqa: BLE001
            snapshot[p.name] = [{"error": str(exc)}]

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(snapshot, indent=2))
    print(f"Saved provider snapshot -> {OUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
