import uuid

from pydantic import BaseModel, Field

from app.models.item import ItemCategory


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    category: ItemCategory
    tags: str | None = None


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    category: ItemCategory | None = None
    tags: str | None = None


class ItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    category: str
    tags: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PaginatedItems(BaseModel):
    total: int
    page: int
    limit: int
    items: list[ItemResponse]
