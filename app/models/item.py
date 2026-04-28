import uuid
from enum import Enum as PyEnum

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin


class ItemCategory(str, PyEnum):
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    BUSINESS = "business"
    HEALTH = "health"
    EDUCATION = "education"
    GENERAL = "general"


class Item(AuditMixin, Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    events: Mapped[list["UserEvent"]] = relationship(  # noqa: F821
        "UserEvent", back_populates="item", cascade="all, delete-orphan"
    )
