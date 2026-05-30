import logging
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.routes import router
from app.core.settings import settings
from app.web.routes import router as web_router
from app.services.health_monitor import start_health_monitoring

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix="/api")
app.include_router(web_router)

_DB_READY = {"done": False}


@app.on_event("startup")
def _startup() -> None:
    # Create tables on first boot. create_all is idempotent.
    try:
        from app.db.session import init_db

        init_db()
        _DB_READY["done"] = True
        
        # Start health monitoring
        logging.info("[STARTUP] Starting health monitoring system...")
        try:
            asyncio.create_task(start_health_monitoring())
        except Exception as e:
            logging.error(f"[STARTUP] Failed to start health monitoring: {e}")
            
    except Exception:  # noqa: BLE001
        logging.getLogger("nexa").exception("init_db failed at startup")


@app.get("/")
def root():
    return RedirectResponse(url="/web/login")


@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok", "app": settings.app_name, "db_ready": _DB_READY["done"]})
