from sqlalchemy import select, func
from sqlalchemy.orm import defer
from passlib.context import CryptContext
from typing import Optional, List, Any
from uuid import UUID

from src.user.models import User
from src.database.connection import async_session
from src.user.schemas import UserCreate, UserUpdate
from src.user.repository import user_repository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:

    @classmethod
    async def create_user_service(cls, user_to_create: UserCreate):
        user_model = User(
            username=user_to_create.username,
            name = user_to_create.name,
            surname = user_to_create.surname,
            email=user_to_create.email,
            password_hash=pwd_context.hash(user_to_create.password),
        )
        print(f'User model DTO:{user_model.__dict__}')

        created_user = await User.create(user_model)

        print(f'Created user:{created_user}')

        return created_user

    @classmethod
    async def get_all_users(
            cls,
            prefetch: Optional[None] = None,
            options: Optional[None] = None,
            filters: Optional[None] = None,
    ) -> List[User]:
        base_options = [defer(User.password_hash)]
        if options:
          base_options.extend(options)
        return await User.all(
            prefetch=prefetch,
            options=base_options,
            filters=filters,
        )
    @classmethod
    async def get_user_by_email(cls, email: str):
        return await User.get_by_field('email', email)

    @classmethod
    async def update_user(
            cls,
            user_data: dict,
            user_id: UUID
        ):
        return await User.update(user_data, (User.id == user_id))



