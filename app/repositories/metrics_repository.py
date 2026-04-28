"""
Raw database queries for the metrics layer.

All aggregation is done in Python rather than SQL to keep
compatibility with the existing SQLAlchemy query patterns
used throughout the project.
"""

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.user import User
from app.models.user_event import UserEvent


class MetricsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_active_users(self) -> int:
        return self.db.query(User).filter(User.is_active.is_(True)).count()

    def get_active_users_with_events(self) -> list[User]:
        """Return active users that have at least one recorded event."""
        return (
            self.db.query(User)
            .filter(User.is_active.is_(True))
            .join(UserEvent, UserEvent.user_id == User.id)
            .distinct()
            .all()
        )

    def count_total_events(self) -> int:
        return self.db.query(UserEvent).count()

    def count_events_by_type(self) -> dict[str, int]:
        """Return total event count grouped by event_type."""
        rows = (
            self.db.query(UserEvent.event_type, func.count().label("cnt"))
            .group_by(UserEvent.event_type)
            .all()
        )
        return {r.event_type: r.cnt for r in rows}

    def get_all_events_ordered_by_user(self) -> list[UserEvent]:
        """
        All events ordered by (user_id, created_at asc).
        Used for leave-one-out evaluation in precision@k.
        """
        return (
            self.db.query(UserEvent)
            .order_by(UserEvent.user_id, UserEvent.created_at.asc())
            .all()
        )

    def get_all_active_items(self) -> list[Item]:
        return self.db.query(Item).filter(Item.is_active.is_(True)).all()
