from fastapi import APIRouter

auth_router = APIRouter(
    tags=['auth'],
)

@auth_router.post('/login', response_model=Token)
async def login_user():
