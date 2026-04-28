import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user_event import UserEventCreate, UserEventResponse
from app.services.user_event_service import UserEventService

router = APIRouter()


@router.post("/", response_model=UserEventResponse, status_code=status.HTTP_201_CREATED)
def register_event(data: UserEventCreate, db: Session = Depends(get_db)):
    return UserEventService(db).register_event(data)


@router.get("/user/{user_id}", response_model=list[UserEventResponse])
def list_user_events(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return UserEventService(db).list_user_events(user_id)
