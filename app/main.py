import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.routes import router
from app.core.settings import settings
from app.web.routes import router as web_router

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
    except Exception:  # noqa: BLE001
        logging.getLogger("nexa").exception("init_db failed at startup")


@app.get("/")
def root():
    return RedirectResponse(url="/web/login")


@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok", "app": settings.app_name, "db_ready": _DB_READY["done"]})
