from fastapi import FastAPI

from src.user.routers import user_router

app = FastAPI()


app.include_router(user_router)

