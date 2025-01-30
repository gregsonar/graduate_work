# db/redis_db.py
from contextlib import asynccontextmanager
from typing import Optional
from redis.asyncio import Redis

from auth.core.config import RedisSettings

redis: Optional[Redis] = None

db_settings = RedisSettings()
DSN = db_settings.model_dump()


def get_redis() -> Redis:
    """Redis клиент."""
    if redis is None:
        return Redis(**DSN)
    return redis

# @asynccontextmanager
# async def get_redis() -> Redis:
#     """Контекстный менеджер для Redis клиента."""
#     global redis
#     if redis is None:
#         redis = Redis(**DSN)
#     try:
#         yield redis
#     finally:
#         await redis.aclose()
#         redis = None


# await redis.set('key', 'value')  # Положить значение по ключу
# await redis.expire('key', 10)  # Установить время жизни ключа в секундах
#
# # А можно последние две операции сделать за один запрос к Redis.
# await redis.setex('key', 15, 'value')  # Положить значение по ключу с ограничением времени жизни в секундах
# value = await redis.get('key')  # Получить значение по ключу