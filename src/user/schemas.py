from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    name: str
    surname: str
    email: str
    password: str
