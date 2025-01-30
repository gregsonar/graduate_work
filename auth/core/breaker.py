from functools import wraps
from typing import Optional, Callable
import asyncio
from enum import Enum
import json
from redis.asyncio import Redis
import logging
from uuid import UUID
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class AsyncCircuitBreaker:
    def __init__(
            self,
            redis: Redis,
            service_name: str = "auth",
            failure_threshold: int = 5,
            recovery_timeout: int = 60,
            half_open_max_tries: int = 3,
            cache_ttl: int = 300
    ):
        self.redis = redis
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_tries = half_open_max_tries
        self.cache_ttl = cache_ttl

        self._prefix = f"circuit_breaker:{service_name}"
        self.state_key = f"{self._prefix}:state"
        self.failures_key = f"{self._prefix}:failures"
        self.last_failure_key = f"{self._prefix}:last_failure"
        self.half_open_tries_key = f"{self._prefix}:half_open_tries"

    async def get_state(self) -> CircuitState:
        """Получение текущего состояния"""
        state = await self.redis.get(self.state_key)
        return CircuitState(state.decode()) if state else CircuitState.CLOSED

    async def _get_cached_token(self, user_id: str) -> Optional[dict]:
        """Получение токена из кэша"""
        cache_key = f"auth_token_cache:{user_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Using cached token for user {user_id}")
            return json.loads(cached)
        return None

    async def _cache_token(self, user_id: str, token_data: dict):
        """Кэширование токена"""
        cache_key = f"auth_token_cache:{user_id}"
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(token_data)
        )
        logger.debug(f"Cached token for user {user_id}")

    async def _record_failure(self):
        """Запись информации о сбое"""
        current_time = asyncio.get_event_loop().time()

        failures = await self.redis.get(self.failures_key)
        current_failures = int(failures.decode()) if failures else 0
        current_failures += 1

        await self.redis.set(self.failures_key, str(current_failures))

        if current_failures >= self.failure_threshold:
            await self.redis.set(self.state_key, CircuitState.OPEN.value)
            await self.redis.set(self.last_failure_key, str(current_time))
            logger.warning(f"Circuit breaker opened after {current_failures} failures")

    async def _get_validate_token_fallback(self) -> dict:
        """Fallback для метода validate_token"""
        return {
            "user_id": str(UUID('00000000-0000-0000-0000-000000000000')),
            "username": "guest",
            "is_superuser": False,
            "roles": ["guest"],
            "exp": (datetime.now(UTC).timestamp() + 3600),  # 1 час
            "iat": datetime.now(UTC).timestamp(),
            "jti": str(UUID('00000000-0000-0000-0000-000000000000')),
            "token_type": "access"
        }

    async def _get_create_tokens_fallback(self):
        """Fallback для метода create_tokens_for_user"""
        return {
            "access_token": "guest_token",
            "refresh_token": None,
            "exp": (datetime.now(UTC).timestamp() + 3600),
            "token_type": "access"
        }

    async def _get_authenticate_fallback(self) -> dict:
        """Fallback для метода authenticate_user"""
        return {
            "access_token": "guest_token",
            "refresh_token": None,
            "user": {
                "id": str(UUID('00000000-0000-0000-0000-000000000000')),
                "username": "guest",
                "is_superuser": False,
                "roles": ["guest"]
            }
        }

    async def _get_refresh_token_fallback(self) -> dict:
        """Fallback для метода refresh_token"""
        return {
            "access_token": "guest_token",
            "refresh_token": None,
            "exp": (datetime.now(UTC).timestamp() + 3600),
            "token_type": "access"
        }

    async def _handle_fallback(self, method_name: str, user_id: Optional[str] = None) -> dict:
        """Обработка fallback сценария в зависимости от метода"""
        if user_id:
            cached_token = await self._get_cached_token(user_id)
            if cached_token:
                logger.info(f"Using cached token for user {user_id} in {method_name} fallback")
                return cached_token

        fallback_handlers = {
            "validate_token": self._get_validate_token_fallback,
            "create_tokens_for_user": self._get_create_tokens_fallback,
            "authenticate_user": self._get_authenticate_fallback,
            "refresh_token": self._get_refresh_token_fallback
        }

        handler = fallback_handlers.get(method_name)
        if handler:
            logger.info(f"Using fallback handler for method {method_name}")
            return await handler()

        # Дефолтный fallback, если метод не определен
        logger.warning(f"No specific fallback handler for method {method_name}, using default")
        return {
            "access_token": "guest_token",
            "refresh_token": None,
            "permissions": ["read_basic"]
        }

    def __call__(self, func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_state = await self.get_state()

            if current_state == CircuitState.OPEN:
                last_failure_bytes = await self.redis.get(self.last_failure_key)
                last_failure = float(last_failure_bytes.decode()) if last_failure_bytes else 0

                if asyncio.get_event_loop().time() - last_failure > self.recovery_timeout:
                    await self.redis.set(self.state_key, CircuitState.HALF_OPEN.value)
                    await self.redis.set(self.half_open_tries_key, "0")
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    method_name = func.__name__
                    user_id = kwargs.get('user_id')
                    if not user_id and len(args) > 1:
                        user_id = str(args[1])
                    return await self._handle_fallback(method_name, user_id)

            try:
                result = await func(*args, **kwargs)

                if current_state == CircuitState.HALF_OPEN:
                    tries = int(await self.redis.incr(self.half_open_tries_key))

                    if tries >= self.half_open_max_tries:
                        await self.redis.set(self.state_key, CircuitState.CLOSED.value)
                        await self.redis.delete(self.failures_key)
                        logger.info("Circuit breaker closed after successful recovery")
                    else:
                        logger.info(f"Circuit breaker remains in HALF-OPEN state, successful tries: {tries}")

                if 'user_id' in kwargs:
                    await self._cache_token(kwargs['user_id'], result)

                return result

            except Exception as e:
                await self._record_failure()
                logger.error(f"Operation failed: {str(e)}")
                raise e

        return wrapper