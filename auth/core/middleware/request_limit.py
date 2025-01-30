from typing import Callable, Optional
import time
from uuid import uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis


class RequestLimit:

    def __init__(self, redis_client: Redis, prefix: str = "rate_limit"):
        self.redis_client = redis_client
        self.prefix = prefix

    async def is_rate_limit(self, key: str, max_requests: int, window: int) -> tuple[bool, int]:
        current_time = int(time.time())

        window_key = f"{self.prefix}:{key}:{current_time // window}"

        async with self.redis_client.pipeline() as pipe:
            await pipe.incr(window_key)
            await pipe.expire(window_key, window)

            count, _ = await pipe.execute()

        remaining = max_requests - count

        return count > max_requests, remaining
