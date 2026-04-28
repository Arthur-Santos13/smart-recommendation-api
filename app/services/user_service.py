import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def list_users(self):
        return self.repo.list_all()

    def get_user(self, user_id: uuid.UUID):
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    def create_user(self, data: UserCreate):
        if self.repo.get_by_email(str(data.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        return self.repo.create(name=data.name, email=str(data.email))

    def update_user(self, user_id: uuid.UUID, data: UserUpdate):
        user = self.get_user(user_id)
        if data.email and str(data.email) != user.email:
            if self.repo.get_by_email(str(data.email)):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use",
                )
        return self.repo.update(
            user,
            name=data.name,
            email=str(data.email) if data.email else None,
        )

    def delete_user(self, user_id: uuid.UUID) -> None:
        user = self.get_user(user_id)
        self.repo.deactivate(user)
