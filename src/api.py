from fastapi import FastAPI

from logger import setup_logger
from src.auth.routers import auth_router
from src.user.routers import user_router

setup_logger()
app = FastAPI()
app.include_router(user_router)

app.include_router(auth_router)

