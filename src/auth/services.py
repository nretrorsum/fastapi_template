from datetime import UTC, datetime, timedelta
from logging import getLogger
from time import perf_counter

from fastapi import Cookie, HTTPException, Response
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import ACCESS_TOKEN_LIVE, SECRET_KEY
from src.auth.schemas import UserLogin
from src.database.connection import db_dependency
from src.user.models import BlackedRefreshTokens, UserRefreshTokens
from src.user.services import UserService


logger = getLogger(__name__)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    async def validate_user_credentials(login: str, password: str, session: db_dependency):
        db_user = await UserService.get_user_by_email(email=login, session=session)
        if not db_user:
            return False

        if not bcrypt_context.verify(password, db_user.password_hash):
            return False
        return db_user

    @staticmethod
    async def generate_jwt(login: str, expiration: timedelta, **kwargs):
        time_start = perf_counter()
        encode = {
            "sub": login,
            **kwargs,
        }
        expires = datetime.now(UTC).replace(tzinfo=None) + expiration
        encode.update({"exp": expires})
        result = jwt.encode(encode, SECRET_KEY, "HS256")
        time_end = perf_counter()
        print(f'Time to generate JWT: {time_end - time_start} ms')
        return result

    @staticmethod
    async def validate_jwt_token(session: db_dependency, token) -> bool:
        try:
            if not token:
                return False
            payload = jwt.decode(token, SECRET_KEY, "HS256")
            expiration_date = payload.get("exp")
            user_id = payload.get("user_id")
            if payload.get('token_type') == 'refresh':
                if await BlackedRefreshTokens.get_by_field(session, 'token', token):
                    return False

            if expiration_date is None:
                return False

            if datetime.now(UTC).replace(tzinfo=None).timestamp() > expiration_date:
                await BlackedRefreshTokens.create({
                    'token': token,
                    'user_id': user_id,
                },
                session)
                return False
            return True
        except JWTError:
            return False

    @staticmethod
    async def get_current_user(
        response: Response,
        session: db_dependency,
        auth_token: str | None = Cookie(alias="auth_token", default=None),
        refresh_token: str | None = Cookie(alias="refresh_token", default=None),
    ):
        if not auth_token and not refresh_token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        if (not await AuthService.validate_jwt_token(session, token=auth_token)
            and not await AuthService.validate_jwt_token(session, refresh_token)):
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            if not auth_token and await AuthService.validate_jwt_token(session, refresh_token):
                auth_token = await AuthService.generate_jwt(
                    login=jwt.decode(refresh_token, SECRET_KEY, "HS256")['sub'],
                    expiration=timedelta(minutes=int(ACCESS_TOKEN_LIVE)),
                    user_id=jwt.decode(refresh_token, SECRET_KEY, "HS256")['user_id'],
                )
                response.set_cookie(
                    key="auth_token",
                    value=auth_token,
                    httponly=False,
                    secure=False,
                    samesite="lax",
                    max_age=int(ACCESS_TOKEN_LIVE) * 60,
                )
            user_credentials = jwt.decode(auth_token, SECRET_KEY, "HS256")
            return await UserService.get_user_by_email(user_credentials['sub'], session=session)

        except JWTError as e:
            return {"status": "Error in token processing", "error": e}

    @staticmethod
    async def login_user(user_creds: UserLogin, session: db_dependency) -> dict | None:
        #time_validate_user_creds = perf_counter() # start time of user validation
        user = await AuthService.validate_user_credentials(user_creds.email, user_creds.password, session=session)

        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        #time_end_validate_user_creds = perf_counter() #end time of user validation

        #time_start_token_generation = perf_counter() # start time of token generation
        access_token = await AuthService.generate_jwt(
            login=user_creds.email,
            expiration=timedelta(minutes=int(ACCESS_TOKEN_LIVE)),
            user_id=str(user.id)
        )

        refresh_token_from_db = await UserRefreshTokens.get_by_field(session, 'user_id', user.id)
        logger.debug(f"refresh_token_from_db: {refresh_token_from_db}")
        if refresh_token_from_db:
            refresh_token = refresh_token_from_db.token
        else:
            refresh_token = await AuthService.generate_jwt(
                user_creds.email, timedelta(days=30), user_id=str(user.id), token_type='refresh'
            )
            await UserRefreshTokens.create(
                {
                    'user_id': user.id,
                    'token': refresh_token,
                },
                session=session,
            )
        #time_end_token_generation = perf_counter() # end time of token generation
        #print(f'Time to validate user credentials: {time_end_validate_user_creds - time_validate_user_creds} ms')
        #print(f'Time to generate tokens: {time_end_token_generation - time_start_token_generation} ms')
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
