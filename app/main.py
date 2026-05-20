from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routes import router as v1_router
from app.db.pool import close_pool, get_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(title="User Registration API", lifespan=lifespan)

app.include_router(v1_router, prefix="/api/v1")
