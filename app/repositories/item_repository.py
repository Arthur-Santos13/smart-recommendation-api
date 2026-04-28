import uuid

from sqlalchemy.orm import Session

from app.models.item import Item


class ItemRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, item_id: uuid.UUID) -> Item | None:
        return (
            self.db.query(Item)
            .filter(Item.id == item_id, Item.is_active.is_(True))
            .first()
        )

    def list_items(
        self,
        category: str | None,
        page: int,
        limit: int,
    ) -> tuple[int, list[Item]]:
        query = self.db.query(Item).filter(Item.is_active.is_(True))
        if category:
            query = query.filter(Item.category == category)
        total = query.count()
        items = query.offset((page - 1) * limit).limit(limit).all()
        return total, items

    def create(
        self,
        title: str,
        category: str,
        description: str | None = None,
        tags: str | None = None,
    ) -> Item:
        item = Item(title=title, category=category, description=description, tags=tags)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item: Item, **fields) -> Item:
        for key, value in fields.items():
            if value is not None:
                setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def soft_delete(self, item: Item) -> Item:
        item.is_active = False
        self.db.commit()
        return item
