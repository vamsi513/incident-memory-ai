from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes.search import router as search_router
from core.auth import verify_production_config
from core.config import settings
from core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    verify_production_config()
    logger = get_logger(__name__)
    logger.info("app_startup", app_name=settings.app_name, environment=settings.app_env)
    yield
    logger.info("app_shutdown", app_name=settings.app_name)


app = FastAPI(
    title="IncidentMemory Enterprise RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(search_router, prefix="/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
