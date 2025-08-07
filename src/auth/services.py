from src.user.repository import user_repository
from fastapi import HTTPException, Cookie
from passlib.context import CryptContext
from datetime import timedelta, datetime
from jose import jwt, JWTError, ExpiredSignatureError
from config import SECRET_KEY
from typing import Optional
import logging

logger = logging.getLogger(__name__)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class AuthService:

    @staticmethod
    async def validate_user_credentials(login: str, password: str):
        db_user = await user_repository.user_crud.get_user_by_email(login=login)
        if not db_user:
            raise HTTPException(status_code=401, detail='Not authenticated')
        if not bcrypt_context.verify(password, db_user.hashed_password):
            raise HTTPException(status_code=401, detail='Not authenticated')
        return {'status': 'authenticated'}

    @staticmethod
    async def generate_jwt(login: str, expiration: timedelta):
        encode = {'sub': login}
        expires = datetime.utcnow() + expiration
        encode.update({'exp': expires})
        return jwt.encode(encode, SECRET, 'HS256')

    @staticmethod
    async def validate_jwt_token(token) -> bool:
        token_from_db = await user_repository.get_expired_token(token)
        if token_from_db:
            return False
        try:
            payload = jwt.decode(token, SECRET, 'HS256')
            logging.info('token decoded for validation')
            expiration_date = payload.get('exp')
            if expiration_date is None:
                return False
            if datetime.utcnow().timestamp() > expiration_date:
                await user_repository.add_expired_token(token, expired=expiration_date)
                logging.info('expired token added to db')
                return False
            return True
        except:
            return False

    @staticmethod
    async def get_current_user(auth_token: Optional[str] = Cookie(alias='authToken', default=None)):
        if not authToken:
            raise HTTPException(status_code=401, detail='Not authenticated')
        if not await validate_jwt_token(authToken):
            raise HTTPException(status_code=401, detail='Not authenticated')
        token_from_db = await user_repository.get_expired_token(auth_token)
        try:
            user_credentials = jwt.decode(authToken, SECRET, 'HS256')
            return user_credentials
        except JWTError as e:
            return {'status': 'Error in token processing', 'error': e}