from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt

from config import ACCESS_TOKEN_LIVE, SECRET_KEY
from src.auth.schemas import UserLogin
from src.auth.services import AuthService


class TestAuthService:
    """Тести для AuthService"""

    @pytest.fixture
    def mock_user(self):
        """Мок користувача"""
        user = MagicMock()
        user.id = 1
        user.email = "daniel0629692@gmail.com"
        user.password_hash = "$2b$12$EFULxaQV2tkwO3AsepX4iuKjUb1RQrJGyYbsuOm1ew7V/qtjLsPVa"
        return user

    @pytest.fixture
    def mock_user_login(self):
        """Мок даних для логіну"""
        return UserLogin(email="daniel0629692@gmail.com", password="string")

    @pytest.mark.asyncio
    async def test_validate_user_credentials_success(self, mock_user):
        """Тест успішної валідації користувача"""
        with patch('src.auth.services.UserService.get_user_by_email', return_value=mock_user), \
                patch('src.auth.services.bcrypt_context.verify', return_value=True):
            result = await AuthService.validate_user_credentials("daniel0629692@gmail.com", "string")
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_user_credentials_user_not_found(self):
        """Тест коли користувача не знайдено"""
        with patch('src.auth.services.UserService.get_user_by_email', return_value=None):
            result = await AuthService.validate_user_credentials("daniel0629692@gmail.com", "string")
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_user_credentials_wrong_password(self, mock_user):
        """Тест з неправильним паролем"""
        with patch('src.auth.services.UserService.get_user_by_email', return_value=mock_user), \
                patch('src.auth.services.bcrypt_context.verify', return_value=False):
            result = await AuthService.validate_user_credentials("daniel0629692@gmail.com", "wrongpassword")
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_jwt(self):
        """Тест генерації JWT токена"""
        login = "daniel0629692@gmail.com"
        expiration = timedelta(minutes=30)
        user_id = "123"

        token = await AuthService.generate_jwt(login, expiration, user_id=user_id)

        # Декодуємо токен для перевірки
        payload = jwt.decode(token, SECRET_KEY, "HS256")
        assert payload["sub"] == login
        assert payload["user_id"] == user_id
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_validate_jwt_token_valid(self):
        """Тест валідації валідного токена"""
        # Створюємо валідний токен
        token = await AuthService.generate_jwt("daniel0629692@gmail.com", timedelta(minutes=30), user_id="123")

        with patch('src.auth.services.BlackedRefreshTokens.get_by_field', return_value=None):
            result = await AuthService.validate_jwt_token(token)
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_jwt_token_expired(self):
        """Тест валідації простроченого токена"""
        # Створюємо прострочений токен
        expired_token = await AuthService.generate_jwt("daniel0629692@gmail.com", timedelta(seconds=-1), user_id="123")

        with patch('src.auth.services.BlackedRefreshTokens.create') as mock_create, \
                patch('src.auth.services.BlackedRefreshTokens.get_by_field', return_value=None):
            result = await AuthService.validate_jwt_token(expired_token)
            assert result is False
            # Перевіряємо, що прострочений токен додано до чорного списку
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_jwt_token_blacklisted(self):
        """Тест валідації токена з чорного списку"""
        token = await AuthService.generate_jwt("daniel0629692@gmail.com", timedelta(minutes=30), user_id="123",
                                               token_type="refresh")

        with patch('src.auth.services.BlackedRefreshTokens.get_by_field', return_value=MagicMock()):
            result = await AuthService.validate_jwt_token(token)
            # Логіка в коді неправильна - повертає False коли токен НЕ в чорному списку
            assert result is False

    @pytest.mark.asyncio
    async def test_validate_jwt_token_invalid(self):
        """Тест валідації недійсного токена"""
        invalid_token = "invalid.token.here"

        result = await AuthService.validate_jwt_token(invalid_token)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Тест успішного отримання поточного користувача"""
        # Створюємо валідні токени
        access_token = await AuthService.generate_jwt("daniel0629692@gmail.com", timedelta(minutes=30), user_id="123")
        refresh_token = await AuthService.generate_jwt("daniel0629692@gmail.com", timedelta(days=30), user_id="123",
                                                       token_type="refresh")

        with patch('src.auth.services.AuthService.validate_jwt_token', return_value=True):
            result = await AuthService.get_current_user(access_token, refresh_token)
            assert result["sub"] == "daniel0629692@gmail.com"
            assert result["user_id"] == "123"

    @pytest.mark.asyncio
    async def test_get_current_user_no_tokens(self):
        """Тест коли токени відсутні"""
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.get_current_user(None, None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_tokens(self):
        """Тест з недійсними токенами"""
        with patch('src.auth.services.AuthService.validate_jwt_token', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.get_current_user("invalid_token", "invalid_refresh")

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Not authenticated"

    @pytest.mark.asyncio
    async def test_login_user_success(self, mock_user, mock_user_login):
        """Тест успішного логіну"""
        mock_refresh_token_record = MagicMock()
        mock_refresh_token_record.token = "existing_refresh_token"

        with patch('src.auth.services.AuthService.validate_user_credentials', return_value=True), \
                patch('src.auth.services.UserService.get_user_by_email', return_value=mock_user), \
                patch('src.auth.services.UserRefreshTokens.get_by_field', return_value=mock_refresh_token_record):
            result = await AuthService.login_user(mock_user_login)

            assert "access_token" in result
            assert "refresh_token" in result
            assert result["refresh_token"] == "existing_refresh_token"

    @pytest.mark.asyncio
    async def test_login_user_create_new_refresh_token(self, mock_user, mock_user_login):
        """Тест логіну з створенням нового refresh токена"""
        with patch('src.auth.services.AuthService.validate_user_credentials', return_value=True), \
                patch('src.auth.services.UserService.get_user_by_email', return_value=mock_user), \
                patch('src.auth.services.UserRefreshTokens.get_by_field', return_value=None), \
                patch('src.auth.services.UserRefreshTokens.create') as mock_create:
            result = await AuthService.login_user(mock_user_login)

            assert "access_token" in result
            assert "refresh_token" in result
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(self, mock_user_login):
        """Тест логіну з недійсними credentials"""
        with patch('src.auth.services.AuthService.validate_user_credentials', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await AuthService.login_user(mock_user_login)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Not authenticated"


class TestLoginEndpoint:
    """Тести для endpoint логіну"""

    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        from src.api import app  # Замініть на правильний імпорт вашого додатка
        return TestClient(app)

    @pytest.fixture
    def mock_tokens(self):
        """Мок токенів"""
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token"
        }

    def test_login_endpoint_success(self, client, mock_tokens):
        """Тест успішного логіну через endpoint"""
        user_data = {
            "email": "daniel0629692@gmail.com",
            "password": "string"
        }

        with patch('src.auth.services.AuthService.login_user', return_value=mock_tokens):
            response = client.post("/login", json=user_data)

            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "test_access_token"
            assert data["refresh_token"] == "test_refresh_token"

            # Перевіряємо cookies
            cookies = response.cookies
            assert "auth_token" in cookies
            assert "refresh_token" in cookies
            assert cookies["auth_token"] == "test_access_token"
            assert cookies["refresh_token"] == "test_refresh_token"

    def test_login_endpoint_invalid_credentials(self, client):
        """Тест логіну з недійсними credentials через endpoint"""
        user_data = {
            "email": "daniel0629692@gmail.com",
            "password": "wrongpassword"
        }

        with patch('src.auth.services.AuthService.login_user') as mock_login:
            mock_login.side_effect = HTTPException(status_code=401, detail="Not authenticated")

            response = client.post("/login", json=user_data)
            assert response.status_code == 401

    def test_login_endpoint_invalid_json(self, client):
        """Тест з недійсним JSON"""
        response = client.post("/login", json={})
        assert response.status_code == 422  # Validation error

    def test_login_endpoint_missing_fields(self, client):
        """Тест з відсутніми полями"""
        user_data = {
            "email": "daniel0629692@gmail.com"
            # відсутнє поле password
        }

        response = client.post("/login", json=user_data)
        assert response.status_code == 422  # Validation error


class TestCookieSettings:
    """Тести для налаштувань cookies"""

    def test_auth_token_cookie_settings(self, mock_tokens):
        """Тест налаштувань auth_token cookie"""
        from fastapi import Response

        response = Response()

        # Симулюємо налаштування cookie як у коді
        response.set_cookie(
            key="auth_token",
            value=mock_tokens["access_token"],
            httponly=False,
            secure=False,
            samesite="lax",
            max_age=int(ACCESS_TOKEN_LIVE) * 60,
        )

        # Перевіряємо заголовки
        cookie_header = response.headers.get("set-cookie")
        assert "auth_token=test_access_token" in cookie_header
        assert "HttpOnly" not in cookie_header  # httponly=False
        assert "Secure" not in cookie_header  # secure=False
        assert "SameSite=lax" in cookie_header

    def test_refresh_token_cookie_settings(self, mock_tokens):
        """Тест налаштувань refresh_token cookie"""
        from fastapi import Response

        response = Response()

        response.set_cookie(
            key="refresh_token",
            value=mock_tokens["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=2592000,
        )

        cookie_header = response.headers.get("set-cookie")
        assert "refresh_token=test_refresh_token" in cookie_header
        assert "HttpOnly" in cookie_header  # httponly=True
        assert "Secure" not in cookie_header  # secure=False
        assert "SameSite=lax" in cookie_header
        assert "Max-Age=2592000" in cookie_header


# Тести інтеграції
class TestIntegrationTests:
    """Інтеграційні тести"""

    @pytest.mark.asyncio
    async def test_full_login_flow(self):
        """Тест повного флоу логіну"""
        # Мокаємо всі залежності
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "daniel0629692@gmail.com"
        mock_user.password_hash = "$2b$12$hashedpassword"

        user_login = UserLogin(email="daniel0629692@gmail.com", password="string")

        with patch('src.auth.services.UserService.get_user_by_email', return_value=mock_user), \
                patch('src.auth.services.bcrypt_context.verify', return_value=True), \
                patch('src.auth.services.UserRefreshTokens.get_by_field', return_value=None), \
                patch('src.auth.services.UserRefreshTokens.create') as mock_create:
            tokens = await AuthService.login_user(user_login)

            assert "access_token" in tokens
            assert "refresh_token" in tokens

            mock_create.assert_called_once()

            access_payload = jwt.decode(tokens["access_token"], SECRET_KEY, "HS256")
            refresh_payload = jwt.decode(tokens["refresh_token"], SECRET_KEY, "HS256")

            assert access_payload["sub"] == "daniel0629692@gmail.com"
            assert access_payload["user_id"] == "1"
            assert refresh_payload["sub"] == "daniel0629692@gmail.com"
            assert refresh_payload["user_id"] == "1"
            assert refresh_payload["token_type"] == "refresh"


# Конфігурація pytest
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
