from fastapi import APIRouter
from passlib.context import CryptContext

from src.user.services import crud_user
from src.user.models import User
from src.user.schemas import UserCreate

user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@user_router.post("/create")
async def create_user(user: UserCreate):
    """
    Create a new user.
    """
    try:
        user_to_create = User(
            username=user.username,
            name=user.name,
            surname=user.surname,
            email=user.email,
            password_hash= pwd_context.hash(user.password),
        )

        await crud_user.create_user(user_to_create)
        return {"message": "User created successfully"}
    except Exception as e:
        return {"message": f"Error creating user: {str(e)}"}

@user_router.get("/get/{email}")
async def get_user_by_email(email: str):
    """
    Get a user by email.
    """
    user = await crud_user.get_user_by_email(email)
    if user:
        return {
            'id': str(user.id),
            'username': user.username,
            'name': user.name,
            'surname': user.surname,
            'email': user.email,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'is_active': user.is_active
        }
    return {"message": "User not found"}