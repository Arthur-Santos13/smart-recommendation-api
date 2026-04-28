import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_event import EventType
from app.repositories.item_repository import ItemRepository
from app.repositories.user_event_repository import UserEventRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_event import UserEventCreate

EVENT_WEIGHTS: dict[str, int] = {
    EventType.VIEW: 1,
    EventType.CLICK: 2,
    EventType.COMPLETE: 3,
    EventType.SKIP: 0,
    EventType.RATE: 2,
}


class UserEventService:
    def __init__(self, db: Session) -> None:
        self.repo = UserEventRepository(db)
        self.user_repo = UserRepository(db)
        self.item_repo = ItemRepository(db)

    def register_event(self, data: UserEventCreate):
        if not self.user_repo.get_by_id(data.user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if not self.item_repo.get_by_id(data.item_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )

        existing = self.repo.get_existing(data.user_id, data.item_id, data.event_type)
        if existing:
            return existing

        weight = EVENT_WEIGHTS.get(data.event_type, 1)
        return self.repo.create(
            user_id=data.user_id,
            item_id=data.item_id,
            event_type=data.event_type,
            weight=weight,
        )

    def list_user_events(self, user_id: uuid.UUID):
        if not self.user_repo.get_by_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return self.repo.list_by_user(user_id)
