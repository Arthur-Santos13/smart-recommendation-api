from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.ml.model_registry import load_into_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_into_registry(settings.MODEL_DIR)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(v1_router, prefix="/api")


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
