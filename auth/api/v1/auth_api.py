from fastapi import APIRouter, Depends, HTTPException, status, Request
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
from auth.tests.conftest import token_service


router = APIRouter(
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    }
)


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
)-> TokenResponse:
    try:
        # Получаем IP адрес клиента
        client_host = request.client.host
        user_agent = request.headers.get('user-agent', 'unknown')  # Получаем User-Agent

        # await auth_service.log_access(auth_request.username, client_host, user_agent)
        # Аутентификация пользователя и получение токенов
        tokens = await auth_service.authenticate_user(
            auth_request.username, auth_request.password, {'ip': client_host, 'user_agent': user_agent}
        )



        return TokenResponse(**tokens)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post(
    "/logout",
    response_model=LogoutResponse
)
async def logout(
        access_token: str,
        refresh_token: str,
        auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    try:
        # Аннулирование токенов
        await auth_service.logout_user(access_token, refresh_token)
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
        refresh_token: str,
        auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    try:
        # Обновление токенов
        tokens = await auth_service.refresh_token(refresh_token)
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
        print(auth_request)
        print("AHAHAH" * 100)
        # Регистрация пользователя
        await auth_service.register_user(
            auth_request.username,
            auth_request.password,
            auth_request.email,
            auth_request.is_superuser
        )

        # После регистрации сразу создаем токены
        tokens = await auth_service.authenticate_user(
            auth_request.username, auth_request.password
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
        token: str,
        token_service: TokenService = Depends(get_token_service)
) -> CurrentUserResponse:
    try:
        # Получение данных о текущем пользователе
        user_data = await token_service.get_current_user(token)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return CurrentUserResponse(**user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to retrieve current user: " + str(e)
        )


@router.patch(
    "/change_password",
    response_model=PasswordChangeResponse
)
async def change_password(
        change_password_request: PasswordChangeRequest,
        auth_service: AuthService = Depends(get_auth_service),
        current_user = validate_roles()
):
    try:
        await auth_service.change_password(current_user['id'],
                                       old_password=change_password_request.current_password,
                                       new_password=change_password_request.new_password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to change password. " + str(e)
        )

@router.get(
    "/access_logs"
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