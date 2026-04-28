from fastapi import APIRouter

from app.api.v1.endpoints import (
    collaborative_recommendations,
    health,
    hybrid_recommendations,
    items,
    recommendations,
    user_events,
    users,
)

router = APIRouter(prefix="/v1")
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(items.router, prefix="/items", tags=["items"])
router.include_router(user_events.router, prefix="/events", tags=["events"])
router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
router.include_router(
    collaborative_recommendations.router,
    prefix="/recommendations/collaborative",
    tags=["recommendations-collaborative"],
)
router.include_router(
    hybrid_recommendations.router,
    prefix="/recommendations/hybrid",
    tags=["recommendations-hybrid"],
)
