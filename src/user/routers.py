from fastapi import APIRouter
from uuid import UUID

from src.user.schemas import UserCreate, UserResponse, UserUpdate
from src.user.services import UserService
from sqlalchemy.orm import defer
user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@user_router.post("/create", response_model=UserResponse)
async def create_user(user: UserCreate):
    return await UserService.create_user_service(user)

@user_router.get("/get/all")
async def get_all_users() -> list[UserResponse]:
    return await UserService.get_all_users()

@user_router.get("/get/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    print(f'User email:{email}')
    return await UserService.get_user_by_email(email)

@user_router.patch("/update/{user_id}", response_model=UserResponse)
async def update_user(user: dict, user_id: UUID):
    return await UserService.update_user(user, user_id)