import decimal
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.user import enums as user_enums


class UserCreate(BaseModel):
    username: str
    name: str
    surname: str
    email: str
    password: str

class UserPreferencesSchema(BaseModel):
    diet: str | None = None
    disliked_ingredients: list[str] | None = None
    allergies: list[str] | None = None

class UserUpdate(BaseModel):
    username: str | None = None
    name: str | None = None
    surname: str | None = None
    email: str | None = None
    user_gender: user_enums.UserGender | None = None
    user_birthday: datetime | None = None
    user_preferences: UserPreferencesSchema | None = None
    user_avatar: str | None = None
    user_weight: decimal.Decimal | None = None
    user_height: decimal.Decimal | None = None
    user_subscription: user_enums.UserSubscription | None = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: UUID
    username: str
    name: str
    surname: str
    email: str
    created_at: datetime
    updated_at: datetime
    username: str | None = None
    name: str | None = None
    surname: str | None = None
    email: str | None = None
    user_gender: user_enums.UserGender | None = None
    user_birthday: datetime | None = None
    user_preferences: UserPreferencesSchema | None = None
    user_avatar: str | None = None
    user_weight: decimal.Decimal | None = None
    user_height: decimal.Decimal | None = None
    user_subscription: user_enums.UserSubscription | None = None

    class Config:
        from_attributes = True

class CreateUserInfo(BaseModel):
    user_gender: user_enums.UserGender | None = None
    user_birthday: datetime | None = None
    user_preferences: UserPreferencesSchema | None = None
    user_avatar: str | None = None
    user_weight: decimal.Decimal | None = None
    user_height: decimal.Decimal | None = None
    user_subscription: user_enums.UserSubscription | None = None

    class Config:
        from_attributes = True
