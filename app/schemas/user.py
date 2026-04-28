import uuid

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}
