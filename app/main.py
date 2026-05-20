import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.v1.routes import router as v1_router
from app.db.pool import close_pool, get_pool
from app.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting up: creating database pool")
    await get_pool()
    logger.info("database pool ready")
    yield
    logger.info("shutting down: closing database pool")
    await close_pool()
    logger.info("database pool closed")


app = FastAPI(title="User Registration API", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s status=%d duration=%.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(v1_router, prefix="/api/v1")
