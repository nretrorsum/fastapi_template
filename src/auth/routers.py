from fastapi import APIRouter
from src.auth.schemas import UserLogin

auth_router = APIRouter(
    tags=['auth'],
)

@auth_router.post('/login')
async def login_user(user: UserLogin):
    pass
