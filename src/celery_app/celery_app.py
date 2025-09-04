import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = f"redis://:{os.getenv('REDIS_PASSWORD', '@1234ABC')}@redis:6379/0"

celery = Celery("src", broker=REDIS_URL, backend=REDIS_URL, include=["src.user.tasks"])

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

if os.getenv("ENVIRONMENT") == "development":
    celery.conf.update(
        task_always_eager=False,
        task_eager_propagates=True,
    )

celery.autodiscover_tasks(["src.user"])


@celery.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
    return "Debug task completed"
