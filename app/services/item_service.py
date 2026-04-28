import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.item_repository import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate, PaginatedItems


class ItemService:
    def __init__(self, db: Session) -> None:
        self.repo = ItemRepository(db)

    def list_items(
        self, category: str | None, page: int, limit: int
    ) -> PaginatedItems:
        total, items = self.repo.list_items(category=category, page=page, limit=limit)
        return PaginatedItems(total=total, page=page, limit=limit, items=items)

    def get_item(self, item_id: uuid.UUID):
        item = self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )
        return item

    def create_item(self, data: ItemCreate):
        return self.repo.create(
            title=data.title,
            category=data.category.value,
            description=data.description,
            tags=data.tags,
        )

    def update_item(self, item_id: uuid.UUID, data: ItemUpdate):
        item = self.get_item(item_id)
        return self.repo.update(
            item,
            title=data.title,
            description=data.description,
            category=data.category.value if data.category else None,
            tags=data.tags,
        )

    def delete_item(self, item_id: uuid.UUID) -> None:
        item = self.get_item(item_id)
        self.repo.soft_delete(item)
