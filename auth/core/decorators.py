from functools import wraps
from typing import Callable
from fastapi import HTTPException, status
from typing_extensions import Optional

from auth.db.postgres import get_session
from auth.db.redis_db import get_redis
from auth.services.token_service import TokenService


def validate_roles(roles: list=Optional[list], is_public: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            token = kwargs.get('access_token')
            if not is_public and not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not provided"
                )
            tokenservice = TokenService(redis_client=get_redis(), session=get_session())
            user = await tokenservice.get_current_user(token)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            if any(role in user['roles'] for role in roles):
                kwargs['current_user'] = user
                return await func(*args, **kwargs)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return wrapper
    return decorator
