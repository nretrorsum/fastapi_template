# src/locust_tests/auth_login_locust.py

import random
import string
from locust import HttpUser, task, between
from faker import Faker
import uuid

#fake = Faker()


class AuthenticationUser(HttpUser):
    """
    Клас для тестування навантаження на endpoints аутентифікації
    """
    wait_time = between(1, 3)  # Пауза між запитами 1-3 секунди

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = None
        self.refresh_token = None
        self.test_users = []
        self.current_user_credentials = None

    def on_start(self):
        """Виконується один раз при старті користувача"""
        # Створюємо декілька тестових користувачів для використання
        self.create_test_users(count=5)

    def generate_random_user_data(self):
        """Генерує випадкові дані користувача"""
        return {
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "name": fake.first_name(),
            "surname": fake.last_name(),
            "email": fake.email(),
            "password": "TestPassword123!"
        }

    def create_test_users(self, count=5):
        """Створює тестових користувачів для подальшого використання"""
        for _ in range(count):
            user_data = self.generate_random_user_data()

            with self.client.post(
                    "/user/create",
                    json=user_data,
                    catch_response=True,
                    name="Setup: Create test user"
            ) as response:
                if response.status_code == 200:
                    self.test_users.append({
                        "email": user_data["email"],
                        "password": user_data["password"]
                    })
                elif response.status_code == 400:
                    # Користувач уже існує, це нормально для тестів
                    self.test_users.append({
                        "email": user_data["email"],
                        "password": user_data["password"]
                    })

    @task(3)
    def test_create_user(self):
        """Тестує створення нового користувача"""
        user_data = self.generate_random_user_data()

        with self.client.post(
                "/user/create",
                json=user_data,
                catch_response=True,
                name="POST /user/create"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Додаємо створеного користувача до списку для логіну
                self.test_users.append({
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
            elif response.status_code == 400:
                # Можливо користувач уже існує
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(5)
    def test_login_user(self):
        """Тестує логін користувача"""
        if not self.test_users:
            return

        # Вибираємо випадкового користувача зі створених
        user_creds = random.choice(self.test_users)

        login_data = {
            "email": user_creds["email"],
            "password": user_creds["password"]
        }

        with self.client.post(
                "/auth/login",
                json=login_data,
                catch_response=True,
                name="POST /auth/login"
        ) as response:
            if response.status_code == 200:
                response.success()

                # Зберігаємо токени з cookies
                cookies = response.cookies
                self.auth_token = cookies.get('auth_token')
                self.refresh_token = cookies.get('refresh_token')
                self.current_user_credentials = user_creds

                # Перевіряємо наявність токенів у відповіді
                try:
                    json_response = response.json()
                    if 'access_token' not in json_response:
                        response.failure("Access token not in response")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Login failed with status: {response.status_code}")

    @task(2)
    def test_authenticated_endpoint(self):
        """Тестує захищений endpoint (потребує авторизації)"""
        if not self.auth_token:
            # Спочатку логінимось
            self.test_login_user()
            return

        cookies = {
            'auth_token': self.auth_token,
            'refresh_token': self.refresh_token
        }

        with self.client.get(
                "/auth/me",  # або будь-який інший захищений endpoint
                cookies=cookies,
                catch_response=True,
                name="GET /auth/me (protected)"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Токен застарів, очищаємо і пробуємо залогінитись знову
                self.auth_token = None
                self.refresh_token = None
                response.failure("Token expired")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def test_logout(self):
        """Тестує вихід користувача"""
        if not self.auth_token:
            return

        cookies = {
            'auth_token': self.auth_token,
            'refresh_token': self.refresh_token
        }

        with self.client.post(
                "/auth/logout",
                cookies=cookies,
                catch_response=True,
                name="POST /auth/logout"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Очищаємо токени після успішного виходу
                self.auth_token = None
                self.refresh_token = None
            else:
                response.failure(f"Logout failed with status: {response.status_code}")


class HighLoadAuthUser(HttpUser):
    """
    Спеціальний клас для тестування високого навантаження
    з мінімальними паузами та максимальною частотою запитів
    """
    wait_time = between(0.1, 0.5)  # Дуже короткі паузи

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_pool = []
        self.tokens_pool = []

    def on_start(self):
        """Створюємо пул користувачів для швидкого тестування"""
        # Створюємо 10 користувачів заздалегідь
        for i in range(10):
            user_data = {
                "username": f"loadtest_user_{i}_{uuid.uuid4().hex[:6]}",
                "name": f"LoadTest{i}",
                "surname": f"User{i}",
                "email": f"loadtest{i}_{uuid.uuid4().hex[:6]}@test.com",
                "password": "LoadTest123!"
            }

            response = self.client.post("/user/create", json=user_data)
            if response.status_code in [200, 400]:  # 400 якщо користувач уже існує
                self.user_pool.append({
                    "email": user_data["email"],
                    "password": user_data["password"]
                })

    @task(10)
    def rapid_login_test(self):
        """Швидкий тест логіну без перевірок"""
        if not self.user_pool:
            return

        user = random.choice(self.user_pool)
        self.client.post("/auth/login", json=user, name="Rapid Login")

    @task(5)
    def rapid_user_creation(self):
        """Швидке створення користувачів"""
        user_data = {
            "username": f"rapid_{uuid.uuid4().hex[:8]}",
            "name": fake.first_name(),
            "surname": fake.last_name(),
            "email": fake.email(),
            "password": "Rapid123!"
        }
        self.client.post("/user/create", json=user_data, name="Rapid Create User")


# Додатковий файл для тестування специфічних сценаріїв
class EdgeCaseUser(HttpUser):
    """
    Тестує граничні випадки та помилки
    """
    wait_time = between(0.5, 2)

    @task(3)
    def test_invalid_login(self):
        """Тест з неправильними даними логіну"""
        invalid_data = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }

        with self.client.post(
                "/auth/login",
                json=invalid_data,
                catch_response=True,
                name="Invalid Login Test"
        ) as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401, got {response.status_code}")

    @task(2)
    def test_malformed_data(self):
        """Тест з некоректними даними"""
        invalid_user_data = {
            "username": "",
            "name": "",
            "email": "invalid-email",
            "password": "123"  # Занадто короткий пароль
        }

        with self.client.post(
                "/user/create",
                json=invalid_user_data,
                catch_response=True,
                name="Malformed Data Test"
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(f"Expected 400, got {response.status_code}")

    @task(1)
    def test_missing_fields(self):
        """Тест з відсутніми полями"""
        incomplete_data = {
            "email": "test@test.com"
            # Відсутні інші обов'язкові поля
        }

        self.client.post("/user/create", json=incomplete_data, name="Missing Fields Test")


# Конфігурація для різних типів тестування
if __name__ == "__main__":
    """
    Для запуску тестів:

    1. Стандартне тестування:
    locust -f src/locust_tests/auth_login_locust.py --users 50 --spawn-rate 5 --host http://localhost:8000 --headless --html=report.html

    2. Тест високого навантаження:
    locust -f src/locust_tests/auth_login_locust.py --users 200 --spawn-rate 10 --user-class HighLoadAuthUser --host http://localhost:8000

    3. Тест граничних випадків:
    locust -f src/locust_tests/auth_login_locust.py --users 20 --spawn-rate 2 --user-class EdgeCaseUser --host http://localhost:8000

    4. Комбінований тест (всі типи користувачів):
    locust -f src/locust_tests/auth_login_locust.py --users 100 --spawn-rate 10 --host http://localhost:8000
    """
    pass