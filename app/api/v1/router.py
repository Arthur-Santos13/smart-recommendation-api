from fastapi import APIRouter

from app.api.v1.endpoints import health, users

router = APIRouter(prefix="/v1")
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
