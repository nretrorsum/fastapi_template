from sqlalchemy import select, func
from logging import getLogger
from fastapi import HTTPException

from src.user.models import User,
from src.database.connection import async_session

logger = getLogger(__name__)

class CrudRepositoryUser:
    def __init__(self, async_session):
        self.async_session = async_session

    async def create_user(self, user: User) -> User:
        async with self.async_session() as session:
            try:
                print(f'User in query:{user.__dict__}')
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            except Exception as error:
                logger.debug("Failed to create user", exc_info=error)
                raise HTTPException(status_code=500, detail=f"Failed to create user: {error}")

    async def get_user_by_email(self, email) -> User | None:
        async with self.async_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            user = result.scalar()
            return user

    async def get_user_by_id(self, user_id) -> User | None:
        async with self.async_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar()
            return user

class AuthServicesRepository:
    def __init__(self, async_session):
        self.async_session = async_session

    async def check_refresh_token(self, refresh_token) -> str:
        async with self.async_session() as session:
            query = select(User).where(User.refresh_token == refresh_token)


class UserRepository:
    def __init__(self):
        self.user_crud: CrudRepositoryUser = CrudRepositoryUser(async_session=async_session)

    @property
    def get_crud_user(self):
        return self.user_crud


user_repository = UserRepository()