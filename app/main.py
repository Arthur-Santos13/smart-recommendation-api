from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.include_router(v1_router, prefix="/api")


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
