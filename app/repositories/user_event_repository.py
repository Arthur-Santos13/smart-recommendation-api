import uuid

from sqlalchemy.orm import Session

from app.models.user_event import UserEvent


class UserEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_existing(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        event_type: str,
    ) -> UserEvent | None:
        return (
            self.db.query(UserEvent)
            .filter(
                UserEvent.user_id == user_id,
                UserEvent.item_id == item_id,
                UserEvent.event_type == event_type,
            )
            .first()
        )

    def create(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        event_type: str,
        weight: int,
    ) -> UserEvent:
        event = UserEvent(
            user_id=user_id,
            item_id=item_id,
            event_type=event_type,
            weight=weight,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_by_user(self, user_id: uuid.UUID) -> list[UserEvent]:
        return (
            self.db.query(UserEvent)
            .filter(UserEvent.user_id == user_id)
            .order_by(UserEvent.created_at.desc())
            .all()
        )
