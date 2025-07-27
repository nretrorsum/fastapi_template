from celery import shared_task
import time
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def test_task(self, duration=10):
    """
    Тестове завдання для перевірки роботи Celery
    """
    logger.info(f"Starting test task for {duration} seconds")
    for i in range(duration):
        time.sleep(1)
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': duration, 'status': f'Processing step {i + 1}/{duration}'}
        )
        logger.info(f"Test task progress: {i + 1}/{duration}")

    logger.info("Test task completed")
    return {'status': 'completed', 'result': f'Task completed in {duration} seconds'}


@shared_task
def send_email_task(email_data):
    """
    Завдання для відправки email (приклад)
    """
    logger.info(f"Sending email to: {email_data.get('to', 'unknown')}")
    # Тут буде логіка відправки email
    time.sleep(2)  # Симуляція обробки
    logger.info("Email sent successfully")
    return {'status': 'sent', 'email': email_data.get('to')}


@shared_task
def process_data_task(data):
    """
    Завдання для обробки даних (приклад)
    """
    logger.info(f"Processing data: {len(data) if isinstance(data, (list, dict)) else 'N/A'} items")
    # Тут буде логіка обробки даних
    time.sleep(1)
    logger.info("Data processing completed")
    return {'status': 'processed', 'items_count': len(data) if isinstance(data, (list, dict)) else 0}


@shared_task(bind=True, max_retries=3)
def retry_task(self, data):
    """
    Завдання з повторними спробами у разі помилки
    """
    try:
        logger.info(f"Processing retry task with data: {data}")
        # Симуляція можливої помилки
        if data.get('should_fail', False):
            raise Exception("Simulated failure")

        time.sleep(1)
        logger.info("Retry task completed successfully")
        return {'status': 'success', 'data': data}

    except Exception as exc:
        logger.error(f"Retry task failed: {str(exc)}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task in 60 seconds... (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=60, exc=exc)
        else:
            logger.error("Max retries exceeded")
            return {'status': 'failed', 'error': str(exc)}