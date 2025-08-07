from sqlalchemy import select, func
from passlib.context import CryptContext

from src.user.models import User
from src.database.connection import async_session
from src.user.schemas import UserCreate
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

        created_user = await user_repository.user_crud.create_user(
            user_model
        )

        print(f'Created user:{created_user}')

        return created_user
