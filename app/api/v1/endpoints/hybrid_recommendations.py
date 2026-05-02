import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.services.hybrid_service import HybridService

router = APIRouter()


@router.get("/{user_id}", response_model=RecommendationResponse)
def get_hybrid_recommendations(
    user_id: uuid.UUID,
    category: str | None = Query(
        default=None,
        description="Filter recommendations by category",
    ),
    top_n: int = Query(default=10, ge=1, le=50),
    cb_weight: float = Query(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for content-based scores (0.0–1.0)",
    ),
    cf_weight: float = Query(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for collaborative scores (0.0–1.0)",
    ),
    n_neighbors: int = Query(default=5, ge=2, le=20),
    db: Session = Depends(get_db),
):
    if round(cb_weight + cf_weight, 6) != 1.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cb_weight + cf_weight must equal 1.0",
        )

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    results = HybridService(db).recommend(
        user_id=user_id,
        top_n=top_n,
        category=category,
        cb_weight=cb_weight,
        cf_weight=cf_weight,
        n_neighbors=n_neighbors,
    )

    return RecommendationResponse(
        user_id=user_id,
        total=len(results),
        recommendations=[
            RecommendationItem(
                item_id=r.item_id,
                title=r.title,
                score=r.score,
                reason=r.reason,
                category=r.category,
            )
            for r in results
        ],
    )
