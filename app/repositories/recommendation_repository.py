"""
Repository helpers for the recommendation layer.
Keeps all DB queries for recommendations in one place.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.user_event import UserEvent


class RecommendationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all_active_items(self) -> list[Item]:
        return self.db.query(Item).filter(Item.is_active.is_(True)).all()

    def get_user_events(self, user_id: uuid.UUID) -> list[UserEvent]:
        """Return all events for a user ordered by recency."""
        return (
            self.db.query(UserEvent)
            .filter(UserEvent.user_id == user_id)
            .order_by(UserEvent.created_at.desc())
            .all()
        )

    def get_item_by_id(self, item_id: uuid.UUID) -> Item | None:
        return self.db.query(Item).filter(Item.id == item_id).first()
