"""Sync services catalog from providers into DB and JSON snapshot."""
"""Sync services catalog from providers.

Usage:
  python scripts/sync_services.py
"""
import asyncio
import json
from pathlib import Path

from app.core.settings import settings
from app.services.providers import ProviderClient
from app.services.catalog_sync import upsert_services
from app.db.session import SessionLocal

OUT_FILE = Path("data/provider_services_snapshot.json")


async def main() -> None:
    providers = [
        ProviderClient("JustAnotherPanel", settings.provider_1_base_url, settings.provider_1_api_key),
        ProviderClient("Peakerr API", settings.provider_2_base_url, settings.provider_2_api_key),
    ]

    snapshot: dict[str, list[dict]] = {}
    db = SessionLocal()
    try:
        for p in providers:
            if not p.api_key:
                snapshot[p.name] = [{"error": "missing_api_key"}]
                continue
            try:
                services = await p.services()
                snapshot[p.name] = services
                upserted = upsert_services(db, p.name, services)
                print(f"{p.name}: upserted {upserted} services")
            except Exception as exc:  # noqa: BLE001
                snapshot[p.name] = [{"error": str(exc)}]
    finally:
        db.close()
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
