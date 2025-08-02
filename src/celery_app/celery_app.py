from celery import Celery
import os
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

# Налаштування Redis URL - використовуємо ім'я сервісу з docker-compose
REDIS_URL = f"redis://:{os.getenv('REDIS_PASSWORD', '@1234ABC')}@redis:6379/0"

# Створюємо екземпляр Celery
celery = Celery(
    'src',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['src.user.tasks']  # Імпортуємо tasks
)

# Налаштування Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 хвилин
    task_soft_time_limit=60,   # 1 хвилина
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Налаштування для розробки
if os.getenv('ENVIRONMENT') == 'development':
    celery.conf.update(
        task_always_eager=False,  # Встановіть True для синхронного виконання в розробці
        task_eager_propagates=True,
    )

# Автоматичне виявлення tasks
celery.autodiscover_tasks(['src.user'])

@celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return 'Debug task completed'