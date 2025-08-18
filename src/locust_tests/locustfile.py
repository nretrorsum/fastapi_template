#noqa: E722 B904 F841
import json
import logging
import random
import uuid

from locust import HttpUser, between, events, task


class AuthenticatedUserApiLoadTest(HttpUser):
    """
    Load test для User API endpoints з авторизацією через cookies
    Тестує всі CRUD операції з правильною cookie-авторизацією
    """
    wait_time = between(1, 3)
    weight = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id: str | None = None
        self.test_user_email: str | None = None
        self.is_authenticated = False
        self.created_users = []  # Список створених користувачів для cleanup

    def on_start(self):
        """Ініціалізація при старті користувача"""
        self.create_and_login_user()

    def create_and_login_user(self):
        """Створення тестового користувача та автентифікація через cookies"""
        self.test_user_email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        username = f"user_{uuid.uuid4().hex[:6]}"
        password = "SecurePass123!"

        # Створення користувача
        payload = {
            "username": username,
            "name": "LoadTest",
            "surname": "User",
            "email": self.test_user_email,
            "password": password
        }

        with self.client.post("/user/create", json=payload, catch_response=True, name="POST /user/create") as response:
            if response.status_code == 200:
                try:
                    user_data = response.json()
                    self.user_id = user_data.get("id")
                    self.created_users.append(self.user_id)

                    # Логін для встановлення cookies
                    self.login_user(self.test_user_email, password)
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed to create user: {response.status_code} - {response.text}")

    def login_user(self, email: str, password: str):
        """Автентифікація користувача через cookies"""
        login_payload = {
            "email": email,
            "password": password
        }

        with self.client.post("/login", json=login_payload, catch_response=True, name="POST /login") as response:
            if response.status_code == 200:
                try:
                    tokens = response.json()
                    # cookies автоматично встановлюються сервером і зберігаються в self.client
                    self.is_authenticated = True
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                self.is_authenticated = False
                response.failure(f"Failed to login: {response.status_code}")

    def check_authentication_and_retry(self, response):
        """Перевіряє статус авторизації і повторює логін при необхідності"""
        if response.status_code == 401:
            # Токен/cookie застарів, перелогінюємось
            self.create_and_login_user()
            return True
        return False

    @task(5)
    def get_all_users(self):
        """Отримання всіх користувачів - найчастіший запит"""
        with self.client.get("/user/get/all", catch_response=True,
                             name="GET /user/get/all") as response:
            if response.status_code == 200:
                try:
                    users = response.json()
                    if isinstance(users, list):
                        response.success()
                    else:
                        response.failure("Response is not a list")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif self.check_authentication_and_retry(response):
                response.success()  # Не рахуємо це як помилку
            else:
                response.failure(f"Failed to get users: {response.status_code}")

    @task(3)
    def get_user_by_email(self):
        """Отримання користувача за email"""
        if not self.test_user_email:
            return

        with self.client.get(f"/user/get/email/{self.test_user_email}",
                             catch_response=True,
                             name="GET /user/get/email/{email}") as response:
            if response.status_code == 200:
                try:
                    user = response.json()
                    if user.get("email") == self.test_user_email:
                        response.success()
                    else:
                        response.failure("Wrong user returned")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                # Користувач не знайдений
                response.success()  # 404 - це нормальна поведінка
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to get user: {response.status_code}")

    @task(2)
    def get_user_by_id(self):
        """Отримання користувача за ID"""
        if not self.user_id:
            return

        with self.client.get(f"/user/get/id/{self.user_id}",
                             catch_response=True,
                             name="GET /user/get/id/{user_id}") as response:
            if response.status_code == 200:
                try:
                    user = response.json()
                    if user.get("id") == self.user_id:
                        response.success()
                    else:
                        response.failure("Wrong user returned")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.success()
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to get user by ID: {response.status_code}")

    @task(2)
    def create_new_user(self):
        """Створення нового користувача"""
        email = f"new_user_{uuid.uuid4().hex[:8]}@example.com"
        username = f"newuser_{uuid.uuid4().hex[:6]}"

        payload = {
            "username": username,
            "name": f"TestUser{random.randint(1, 1000)}",
            "surname": f"TestSurname{random.randint(1, 1000)}",
            "email": email,
            "password": f"Password{random.randint(100, 999)}!"
        }

        with self.client.post("/user/create", json=payload,
                              catch_response=True,
                              name="POST /user/create (new)") as response:
            if response.status_code == 200:
                try:
                    user_data = response.json()
                    new_user_id = user_data.get("id")
                    if new_user_id:
                        self.created_users.append(new_user_id)
                        response.success()
                    else:
                        response.failure("No user ID in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed to create user: {response.status_code} - {response.text}")

    @task(2)
    def update_user(self):
        """Оновлення існуючого користувача"""
        if not self.user_id:
            return

        # Створюємо валідний payload згідно з схемою
        user_preferences = {
            "diet": random.choice(["vegetarian", "vegan", "keto"]),
            "disliked_ingredients": random.choice([["onions", "garlic"], ["nuts"]]),
            "allergies": random.choice([["dairy"], ["shellfish", "nuts"]])
        }

        payload = {
            "name": f"UpdatedName{random.randint(1, 1000)}",
            "surname": f"UpdatedSurname{random.randint(1, 1000)}",
            "user_preferences": user_preferences,
        }

        with self.client.patch(f"/user/update/{self.user_id}",
                               json=payload,
                               catch_response=True,
                               name="PATCH /user/update/{user_id}") as response:
            if response.status_code == 200:
                try:
                    updated_user = response.json()
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.success()  # Користувач не існує
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to update user: {response.status_code}")

    @task(1)
    def create_user_info(self):
        """Створення додаткової інформації користувача"""
        if not self.user_id:
            return

        user_preferences = {
            "diet": random.choice(["vegetarian", "vegan", "keto"]),
            "disliked_ingredients": ["onions", "garlic"],
            "allergies": ["dairy"]
        }

        payload = {
            "user_gender": "MALE",  # Використовуємо enum значення
            "user_birthday": "1990-01-01T00:00:00",
            "user_preferences": user_preferences,
            "user_avatar": f"avatar_{uuid.uuid4().hex[:8]}.jpg",
            "user_weight": "70.5",  # decimal як string
            "user_height": "175.0",
            "user_subscription": "FREE",  # Використовуємо enum значення
        }

        with self.client.post(f"/user/user_info/create/{self.user_id}",
                              json=payload,
                              catch_response=True,
                              name="POST /user/user_info/create/{user_id}") as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 400:
                # Можливо інформація вже існує
                response.success()
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to create user info: {response.status_code}")

    @task(1)
    def delete_user(self):
        """Видалення користувача"""
        if not self.user_id or len(self.created_users) < 2:  # Залишаємо принаймні одного
            return

        # Видаляємо не основного користувача
        user_to_delete = random.choice([u for u in self.created_users if u != self.user_id])

        with self.client.delete(f"/user/delete/{user_to_delete}",
                                catch_response=True,
                                name="DELETE /user/delete/{user_id}") as response:
            if response.status_code in [200, 204, 404]:
                if user_to_delete in self.created_users:
                    self.created_users.remove(user_to_delete)
                response.success()
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to delete user: {response.status_code}")

    @task(1)
    def test_batch_create_users(self):
        """Тест масового створення користувачів"""
        batch_size = random.randint(2, 5)
        users_batch = []

        for i in range(batch_size):
            user_data = {
                "username": f"batch_user_{uuid.uuid4().hex[:6]}",
                "name": f"BatchUser{i}",
                "surname": f"Test{i}",
                "email": f"batch_{i}_{uuid.uuid4().hex[:6]}@example.com",
                "password": f"BatchPass{i}123!"
            }
            users_batch.append(user_data)

        with self.client.post("/user/create-batch",
                              json=users_batch,
                              catch_response=True,
                              name="POST /user/create-batch") as response:
            if response.status_code == 200:
                try:
                    created_users = response.json()
                    for user in created_users:
                        self.created_users.append(user.get("id"))
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to create batch users: {response.status_code}")

    @task(1)
    def test_protected_endpoint(self):
        """Тест захищеного ендпоінту"""
        with self.client.get("/protected_root",
                             catch_response=True,
                             name="GET /protected_root") as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif self.check_authentication_and_retry(response):
                response.success()
            else:
                response.failure(f"Failed to access protected endpoint: {response.status_code}")

    @task(1)
    def test_logout_and_relogin(self):
        """Тест логауту та повторного логіну"""
        # Спершу робимо logout
        with self.client.post("/logout", catch_response=True, name="POST /logout") as response:
            if response.status_code == 200:
                self.is_authenticated = False
                response.success()
            else:
                response.failure(f"Failed to logout: {response.status_code}")

        # Потім знову логінимся
        if self.test_user_email:
            login_payload = {
                "email": self.test_user_email,
                "password": "SecurePass123!"
            }

            with self.client.post("/login", json=login_payload,
                                  catch_response=True,
                                  name="POST /login (after logout)") as response:
                if response.status_code == 200:
                    self.is_authenticated = True
                    response.success()
                else:
                    response.failure(f"Failed to re-login: {response.status_code}")

    def on_stop(self):
        """Очищення після завершення тестів"""
        # Логаут для очищення cookies
        try:
            self.client.post("/logout")
        except:
            pass

        # Спробуємо видалити створених користувачів
        for user_id in self.created_users[-3:]:  # Видаляємо останніх 3
            try:
                self.client.delete(f"/user/delete/{user_id}")
            except:
                pass


class UnauthorizedUserTest(HttpUser):
    """
    Тест для неавторизованих запитів
    Перевіряє правильність обробки помилок автентифікації при відсутності cookies
    """
    wait_time = between(2, 4)
    weight = 1

    def on_start(self):
        """Очищаємо всі cookies для гарантії неавторизованого стану"""
        self.client.cookies.clear()

    @task(3)
    def test_unauthorized_get_all_users(self):
        """Тест неавторизованого доступу до списку користувачів"""
        with self.client.get("/user/get/all",
                             catch_response=True,
                             name="UNAUTH: GET /user/get/all") as response:
            if response.status_code == 401:
                response.success()  # Очікуємо 401
            else:
                response.failure(f"Expected 401, got {response.status_code}")

    @task(2)
    def test_unauthorized_get_user_by_email(self):
        """Тест неавторизованого доступу до користувача за email"""
        test_email = "test@example.com"

        with self.client.get(f"/user/get/email/{test_email}",
                             catch_response=True,
                             name="UNAUTH: GET /user/get/email/{email}") as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401, got {response.status_code}")

    @task(2)
    def test_unauthorized_protected_endpoint(self):
        """Тест неавторизованого доступу до захищеного ендпоінту"""
        with self.client.get("/protected_root",
                             catch_response=True,
                             name="UNAUTH: GET /protected_root") as response:
            if response.status_code == 401:
                response.success()
            else:
                response.failure(f"Expected 401, got {response.status_code}")

    @task(1)
    def test_create_user_without_auth(self):
        """Створення користувача без автентифікації (має працювати)"""
        email = f"unauth_user_{uuid.uuid4().hex[:8]}@example.com"

        payload = {
            "username": f"unauth_{uuid.uuid4().hex[:6]}",
            "name": "Unauthorized",
            "surname": "User",
            "email": email,
            "password": "TestPass123!"
        }

        with self.client.post("/user/create",
                              json=payload,
                              catch_response=True,
                              name="UNAUTH: POST /user/create") as response:
            if response.status_code == 200:
                response.success()  # Створення має працювати без авторизації
            else:
                response.failure(f"Failed to create user: {response.status_code}")

    @task(1)
    def test_invalid_login_attempt(self):
        """Тест спроби входу з неправильними даними"""
        payload = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }

        with self.client.post("/login",
                              json=payload,
                              catch_response=True,
                              name="UNAUTH: POST /login (invalid)") as response:
            if response.status_code == 401:
                response.success()  # Очікуємо помилку авторизації
            else:
                response.failure(f"Expected 401, got {response.status_code}")


class CookieLifecycleTest(HttpUser):
    """
    Спеціальний тест для перевірки життєвого циклу cookies
    """
    wait_time = between(2, 5)
    weight = 1

    @task(1)
    def test_cookie_refresh_flow(self):
        """Тест автоматичного оновлення токенів через cookies"""
        # Створюємо користувача
        email = f"cookie_test_{uuid.uuid4().hex[:8]}@example.com"
        password = "CookieTest123!"

        user_payload = {
            "username": f"cookie_user_{uuid.uuid4().hex[:6]}",
            "name": "Cookie",
            "surname": "Test",
            "email": email,
            "password": password
        }

        # Створення користувача
        with self.client.post("/user/create", json=user_payload,
                              catch_response=True,
                              name="COOKIE: POST /user/create") as response:
            if response.status_code != 200:
                response.failure("Failed to create test user")
                return

        # Логін
        login_payload = {"email": email, "password": password}
        with self.client.post("/login", json=login_payload,
                              catch_response=True,
                              name="COOKIE: POST /login") as response:
            if response.status_code != 200:
                response.failure("Failed to login")
                return
            response.success()

        # Перевіряємо що cookies встановлено та працюють
        with self.client.get("/protected_root",
                             catch_response=True,
                             name="COOKIE: GET /protected_root (after login)") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Protected endpoint failed after login: {response.status_code}")

        # Логаут
        with self.client.post("/logout",
                              catch_response=True,
                              name="COOKIE: POST /logout") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Logout failed")

        # Перевіряємо що після логауту доступ заборонено
        with self.client.get("/protected_root",
                             catch_response=True,
                             name="COOKIE: GET /protected_root (after logout)") as response:
            if response.status_code == 401:
                response.success()  # Очікуємо 401 після логауту
            else:
                response.failure(f"Expected 401 after logout, got {response.status_code}")


# Події для кастомного логування та моніторингу
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logging.info("🍪 Starting Cookie-Based Authenticated User API Load Test")
    logging.info(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logging.info("✅ Cookie-Based User API Load Test completed")

    # Виводимо статистику
    stats = environment.stats
    logging.info(f"Total requests: {stats.total.num_requests}")
    logging.info(f"Failed requests: {stats.total.num_failures}")
    logging.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Логування запитів та помилок"""
    if exception:
        logging.error(f"Request failed: {request_type} {name} - {exception}")


# Налаштування для запуску:
#
# 1. Локальний веб-інтерфейс:
#    locust -f cookie_auth_locustfile.py --host=http://localhost:8000
#
# 2. Командний рядок (20 користувачів, 5 користувачів на секунду, 120 секунд):
#    locust -f src/locust_tests/locustfile.py --host=http://localhost:8000 -u 20 -r 5 -t 120s --headless --html=report.html
#
# 3. З HTML звітом та CSV логами:
#    locust -f src/locust_tests/locustfile.py --host=http://localhost:8000 -u 20 -r 5 -t 120s --headless --html=report.html
#
# 4. Тільки автентифіковані користувачі:
#    locust -f src/locust_tests/locustfile.py --host=http://localhost:8000 -u 15 -r 3 -t 60s --headless --tags authenticated
#
# 5. Стрес-тест з великою кількістю користувачів:
#    locust -f src/locust_tests/locustfile.py --host=http://localhost:8000 -u 100 -r 10 -t 300s --headless
#
# 6. Тест тільки cookie lifecycle:
#    locust -f src/locust_tests/locustfile.py --host=http://localhost:8000 -u 5 -r 1 -t 60s --headless CookieLifecycleTest
