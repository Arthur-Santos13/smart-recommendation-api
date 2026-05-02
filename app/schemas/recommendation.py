import uuid

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    item_id: uuid.UUID
    title: str
    score: float
    reason: str
    category: str

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    user_id: uuid.UUID
    total: int
    recommendations: list[RecommendationItem]
