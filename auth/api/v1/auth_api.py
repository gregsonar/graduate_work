from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.api.v1.oauth.base_oauth_router import vk_router, yandex_router
from auth.db.postgres import get_session
from auth.db.redis_db import get_redis
from auth.services.auth_service import AuthService
from auth.services.token_service import TokenService
from auth.schemas.auth_schema import AuthRequest, TokenResponse, LogoutResponse, CurrentUserResponse
from auth.schemas.password_schema import PasswordChangeRequest, PasswordChangeResponse
from auth.schemas.entity import UserCreate
from auth.core.decorators import validate_roles
from typing import Dict, Any

from auth.db.crud import AccessLogRepository

router = APIRouter(
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    }
)

# Security scheme для авторизации через Bearer token
oauth2_scheme = HTTPBearer()

async def get_auth_service(session: AsyncSession = Depends(get_session),
                         redis_cli: Redis = Depends(get_redis)) -> AuthService:
    return AuthService(session, redis_cli)

async def get_token_service(session: AsyncSession = Depends(get_session),
                          redis_cli: Redis = Depends(get_redis)) -> TokenService:
    return TokenService(redis_cli, session)

@router.post("/login", response_model=TokenResponse)
async def login(
        auth_request: AuthRequest,
        request: Request,
        auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        client_host = request.client.host
        user_agent = request.headers.get('user-agent', 'unknown')

        tokens = await auth_service.authenticate_user(
            auth_request.username,
            auth_request.password,
            {'ip': client_host, 'user_agent': user_agent}
        )

        return TokenResponse(**tokens)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[Depends(oauth2_scheme)]
)
async def logout(
        credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    try:
        access_token = credentials.credentials
        # В этом случае мы не требуем refresh token для логаута
        await auth_service.logout_user(access_token, None)
        return {"detail": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error during logout: " + str(e)
        )

@router.post(
    "/refresh",
    response_model=TokenResponse
)
async def refresh(
        credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        tokens = await auth_service.refresh_token(credentials.credentials)
        return TokenResponse(**tokens)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token: " + str(e)
        )

@router.post(
    "/register",
    response_model=TokenResponse
)
async def register(
        auth_request: UserCreate,
        auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        await auth_service.register_user(
            auth_request.username,
            auth_request.password,
            auth_request.email,
            auth_request.is_superuser
        )

        tokens = await auth_service.authenticate_user(
            auth_request.username,
            auth_request.password
        )
        return TokenResponse(**tokens)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed: " + str(e)
        )

@router.get(
    "/me",
    response_model=CurrentUserResponse
)
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
        token_service: TokenService = Depends(get_token_service)
) -> CurrentUserResponse:
    try:
        user_data = await token_service.get_current_user(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return CurrentUserResponse(**user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to retrieve current user: " + str(e)
        )

@router.patch(
    "/change_password",
    response_model=PasswordChangeResponse,
    dependencies=[Depends(oauth2_scheme)]
)
async def change_password(
        change_password_request: PasswordChangeRequest,
        auth_service: AuthService = Depends(get_auth_service),
        current_user = validate_roles()
):
    try:
        await auth_service.change_password(
            current_user['id'],
            old_password=change_password_request.current_password,
            new_password=change_password_request.new_password
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to change password. " + str(e)
        )

@router.get(
    "/access_logs",
    dependencies=[Depends(oauth2_scheme)]
)
async def get_access_logs(
        page: int,
        access_log: AccessLogRepository = Depends(get_session),
        current_user=validate_roles()
):
    try:
        return await access_log.get_user_logs(current_user['id'], page)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get logs. " + str(e)
        )