import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.services.collaborative_service import CollaborativeService

router = APIRouter()


@router.get("/{user_id}", response_model=RecommendationResponse)
def get_cf_recommendations(
    user_id: uuid.UUID,
    category: str | None = Query(
        default=None,
        description="Filter recommendations by category",
    ),
    top_n: int = Query(default=10, ge=1, le=50),
    n_neighbors: int = Query(default=5, ge=2, le=20),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    results = CollaborativeService(db, n_neighbors=n_neighbors).recommend(
        user_id=user_id,
        top_n=top_n,
        category=category,
    )

    return RecommendationResponse(
        user_id=user_id,
        total=len(results),
        recommendations=[
            RecommendationItem(
                item_id=r.item_id,
                score=r.score,
                reason=r.reason,
                category=r.category,
            )
            for r in results
        ],
    )
