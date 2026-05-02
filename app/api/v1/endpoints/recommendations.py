import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.services.content_based_service import ContentBasedService

router = APIRouter()


@router.get("/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: uuid.UUID,
    category: str | None = Query(
        default=None,
        description="Filter recommendations by category",
    ),
    top_n: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    results = ContentBasedService(db).recommend(
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
                title=r.title,
                score=r.score,
                reason=r.reason,
                category=r.category,
            )
            for r in results
        ],
    )
