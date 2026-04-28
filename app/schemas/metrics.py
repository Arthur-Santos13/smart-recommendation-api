import uuid

from pydantic import BaseModel


class UsageRateMetrics(BaseModel):
    total_active_users: int
    users_with_interactions: int
    usage_rate: float
    total_events: int
    avg_events_per_active_user: float
    events_by_type: dict[str, int]


class TopRecommendedItem(BaseModel):
    item_id: uuid.UUID
    title: str
    category: str
    recommendation_count: int


class PrecisionAtKMetrics(BaseModel):
    k: int
    evaluated_users: int
    hits: int
    precision_at_k: float


class MetricsSummary(BaseModel):
    usage: UsageRateMetrics
    precision_at_k: PrecisionAtKMetrics
    top_recommended_items: list[TopRecommendedItem]
