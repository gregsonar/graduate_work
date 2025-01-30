from functools import wraps
from typing import Callable

def circuit_protected(func: Callable):
    """Декоратор для интеграции метода с Circuit Breaker"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if hasattr(self, 'circuit_breaker'):
            return await self.circuit_breaker(func)(self, *args, **kwargs)
        return await func(self, *args, **kwargs)
    return wrapper