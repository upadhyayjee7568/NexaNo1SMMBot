from fastapi import APIRouter

from app.core.settings import settings
from app.services.platforms import platform_catalog

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.environment}


@router.get("/config/summary")
def config_summary() -> dict:
    return {
        "project_name": settings.project_name,
        "bot_username": settings.telegram_bot_username,
        "support_username": settings.telegram_support_username,
        "payment_gateway": settings.payment_gateway,
        "cashfree_mode": settings.cashfree_mode,
        "timezone": settings.timezone,
    }


@router.get("/services/platforms")
def services_platforms() -> dict:
    return {"platforms": platform_catalog(), "count": len(platform_catalog())}
