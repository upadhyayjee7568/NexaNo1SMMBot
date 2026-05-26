from fastapi import FastAPI

from app.api.routes import router
from app.web.routes import router as web_router
from app.core.settings import settings

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix="/api")
app.include_router(web_router)
