import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.user_event import EventType


class UserEventCreate(BaseModel):
    user_id: uuid.UUID
    item_id: uuid.UUID
    event_type: EventType


class UserEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    item_id: uuid.UUID
    event_type: str
    weight: int
    created_at: datetime

    model_config = {"from_attributes": True}
