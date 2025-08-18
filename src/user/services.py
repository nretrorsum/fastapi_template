import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from src.user import (
    schemas as user_schemas,  #import UserCreate, UserResponse, UserUpdate
)
from src.user.models import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

password_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="password_")


class UserService:

    @classmethod
    async def _hash_password_async(cls, password: str) -> str:
        return await asyncio.to_thread(pwd_context.hash, password)

    @classmethod
    async def create_user_service(
            cls,
            user_to_create: user_schemas.UserCreate,
            session: AsyncSession
    ) -> User:

        await cls._validate_user_uniqueness(user_to_create, session)

        password_hash = await cls._hash_password_async(user_to_create.password)

        user_data = {
            "username": user_to_create.username,
            "name": user_to_create.name,
            "surname": user_to_create.surname,
            "email": user_to_create.email,
            "password_hash": password_hash,
            'user_gender': None,
            'user_birthday': None,
            'user_preferences': {},
            'user_avatar': None,
            'user_weight': None,
            'user_height': None,
            'user_subscription': None,
        }

        return await User.create(user_data, session)

    @classmethod
    async def _validate_user_uniqueness(
            cls,
            user_data: user_schemas.UserCreate,
            session: AsyncSession
    ) -> None:

        existing_user = await User.get_by_field(
            session, "email", user_data.email
        )
        if existing_user:
            raise ValueError("Email already exists")

        existing_user = await User.get_by_field(
            session, "username", user_data.username
        )
        if existing_user:
            raise ValueError("Username already exists")

    @classmethod
    async def get_all_users(
            cls,
            session: AsyncSession,
            prefetch: Any | None = None,
            options: list[Any] | None = None,
            filters: dict[str, Any] | None = None,
    ) -> list[User]:

        base_options = [defer(User.password_hash)]
        if options:
            base_options.extend(options)

        return await User.all(
            session=session,
            prefetch=prefetch,
            options=base_options,
        )

    @classmethod
    async def get_user_by_email(
            cls,
            email: str,
            session: AsyncSession
    ) -> User | None:
        return await User.get_by_field(session, "email", email)

    @classmethod
    async def update_user(
            cls,
            user_data: dict,
            user_id: UUID,
            session: AsyncSession
    ) -> User | None:

        where_clause = User.id == user_id
        return await User.update(session, user_data, where_clause)

    @classmethod
    async def delete_user(
            cls,
            user_id: UUID,
            session: AsyncSession
    ) -> int:
        where_clause = User.id == user_id
        return await User.delete(session, where_clause)

    @classmethod
    async def create_users_batch(
            cls,
            users_data: list[user_schemas.UserCreate],
            session: AsyncSession
    ) -> list[User]:

        password_tasks = [
            cls._hash_password_async(user.password)
            for user in users_data
        ]
        password_hashes = await asyncio.gather(*password_tasks)

        users = []
        for user_data, password_hash in zip(users_data, password_hashes, strict=False):
            user = User(
                username=user_data.username,
                name=user_data.name,
                surname=user_data.surname,
                email=user_data.email,
                password_hash=password_hash,
            )
            users.append(user)

        # Batch insert
        session.add_all(users)
        await session.commit()

        return users

    @classmethod
    async def save_user_data(
            cls,
            user_id: UUID,
            users_data: dict[str, Any],
            session: AsyncSession,
    ):
        user = await User.get_by_field(session, 'id', user_id)
        print(f'User found: {user}')
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        where_clause=(User.id == user_id)
        await User.update(
            session,
            users_data,
            where_clause,
            )
