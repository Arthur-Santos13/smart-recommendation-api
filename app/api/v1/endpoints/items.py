import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate, PaginatedItems
from app.services.item_service import ItemService

router = APIRouter()


@router.get("/", response_model=PaginatedItems)
def list_items(
    category: str | None = Query(default=None, description="Filter by category"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ItemService(db).list_items(category=category, page=page, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    return ItemService(db).get_item(item_id)


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate, db: Session = Depends(get_db)):
    return ItemService(db).create_item(data)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: uuid.UUID, data: ItemUpdate, db: Session = Depends(get_db)):
    return ItemService(db).update_item(item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: uuid.UUID, db: Session = Depends(get_db)):
    ItemService(db).delete_item(item_id)
