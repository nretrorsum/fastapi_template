from fastapi import APIRouter

from src.user.schemas import UserCreate
from src.user.services import UserService
user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)


@user_router.post("/create")
async def create_user(user: UserCreate):
    return await UserService.create_user_service(user)

@user_router.get("/get/{email}")
async def get_user_by_email(email: str):
    pass