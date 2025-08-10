from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    name: str
    surname: str
    email: str
    password: str

class UserUpdate(BaseModel):
    username: str
    name: str
    surname: str
    email: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    name: str
    surname: str
    email: str
    created_at: datetime
    updated_at: datetime