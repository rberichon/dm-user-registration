from fastapi import FastAPI

from .api.v1.routes import router as v1_router

app = FastAPI(title="User Registration API")

app.include_router(v1_router, prefix="/api/v1")
