from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import ServiceCatalog


def detect_platform(name: str, category: str | None) -> str:
    source = f"{name} {category or ''}".lower()
    if "instagram" in source:
        return "Instagram"
    if "youtube" in source:
        return "YouTube"
    if "telegram" in source:
        return "Telegram"
    if "facebook" in source:
        return "Facebook"
    return "Other"


def upsert_services(db: Session, provider_name: str, services: list[dict]) -> int:
    updated = 0
    for s in services:
        sid = str(s.get("service", ""))
        if not sid:
            continue
        item = (
            db.query(ServiceCatalog)
            .filter(ServiceCatalog.provider_name == provider_name, ServiceCatalog.provider_service_id == sid)
            .first()
        )
        name = str(s.get("name", "Unknown Service"))
        category = s.get("category")
        rate = Decimal(str(s.get("rate", 0) or 0))
        min_qty = int(s.get("min", 1) or 1)
        max_qty = int(s.get("max", 1) or 1)
        platform = detect_platform(name, str(category) if category else None)

        if not item:
            item = ServiceCatalog(
                provider_name=provider_name,
                provider_service_id=sid,
                platform=platform,
                category=str(category) if category else None,
                service_name=name,
                base_rate=rate,
                min_qty=min_qty,
                max_qty=max_qty,
                enabled=True,
            )
            db.add(item)
        else:
            item.platform = platform
            item.category = str(category) if category else None
            item.service_name = name
            item.base_rate = rate
            item.min_qty = min_qty
            item.max_qty = max_qty
            item.enabled = True
        updated += 1
    db.commit()
    return updated
