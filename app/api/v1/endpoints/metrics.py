from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metrics import MetricsSummary
from app.services.metrics_service import MetricsService

router = APIRouter()


@router.get("", response_model=MetricsSummary)
def get_metrics(
    top_n: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Number of top recommended items to return",
    ),
    k: int = Query(
        default=10,
        ge=1,
        le=50,
        description="k value for precision@k leave-one-out evaluation",
    ),
    db: Session = Depends(get_db),
):
    """
    Compute and return offline recommendation quality metrics.

    - **usage**: fraction of active users with ≥ 1 interaction, total events,
      average events per user, and per-type breakdown.
    - **precision_at_k**: leave-one-out content-based precision — fraction of
      users for whom the held-out item lands in the top-k ranking.
    - **top_recommended_items**: items that appear most often across all users'
      content-based recommendation lists.
    """
    return MetricsService(db).get_summary(top_n=top_n, k=k)
