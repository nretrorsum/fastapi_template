from sqlalchemy import select, func

from src.user.models import User
from src.database.connection import async_session


class CrudUser:
    def __init__(self, async_session):
        self.async_session = async_session

    async def create_user(self, user: User):
        async with self.async_session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def get_user_by_email(self, email) -> list[User] | None:
        async with self.async_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            users = result.scalar()
            return users

crud_user = CrudUser(async_session)