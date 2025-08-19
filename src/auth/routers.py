from typing import Annotated

from fastapi import APIRouter, Depends, Response

from config import ACCESS_TOKEN_LIVE
from src.auth.schemas import UserLogin
from src.auth.services import AuthService
from src.database.connection import db_dependency
from src.user.models import User

auth_router = APIRouter(
    tags=["auth"],
)
auth_dependency = Annotated[User, Depends(AuthService.get_current_user)]

@auth_router.post("/login")
async def login_user(
        user: UserLogin,
        response: Response,
        session: db_dependency
):
    tokens = await AuthService.login_user(user, session)

    response.set_cookie(
        key="auth_token",
        value=tokens["access_token"],
        httponly=False,
        secure=False,  # True для production
        samesite="lax",
        max_age=int(ACCESS_TOKEN_LIVE) * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=2592000,
    )

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }

@auth_router.get("/protected_root")
async def protected_root(user: auth_dependency):
    return {"message": f"Hello, {user.name}!"}

@auth_router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie("auth_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
