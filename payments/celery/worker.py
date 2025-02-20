# todo: Возможно, для воркера целесообразно создать отдельное синхронное подключение к БД, если задачи остаются синхронными.

"""
Точка входа для запуска Celery worker.

Celery можно запустить как celery -A payments.celery.tasks worker --loglevel=info
или как python -m payments.celery.worker
"""

from .tasks import celery  # Импортируем наш экземпляр Celery из tasks.py

if __name__ == "__main__":
    celery.start()
