from functools import wraps
from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth.db.postgres import get_session
from auth.db.redis_db import get_redis
from auth.services.token_service import TokenService

oauth2_scheme = HTTPBearer()


def validate_roles(required_roles: Optional[List[str]] = None):
    async def validate_token(
            credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
            token_service: TokenService = Depends(lambda: TokenService(get_redis(), get_session()))
    ):
        try:
            user = await token_service.get_current_user(credentials.credentials)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )

            # Если роли не указаны, просто проверяем токен
            if not required_roles:
                return user

            # Проверяем наличие требуемых ролей
            user_roles = set(user.get('roles', []))
            if not user_roles.intersection(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )

            return user

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )

    return validate_token