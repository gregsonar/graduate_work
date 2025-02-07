from datetime import datetime, timedelta
from typing import Dict, Any, Type
from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db.postgres import get_session
from auth.db.redis_db import get_redis
from auth.services.auth_service import AuthService
from auth.services.oauth.base_oauth import BaseOAuthService
from auth.core.decorators import validate_roles
from auth.schemas.auth_schema import TokenResponse
from auth.schemas.oauth.base_schema import (
    SocialAccountResponse,
    SocialAccountList,
    AuthUrlResponse
)
from auth.services.oauth.vk_oauth_service import VKOAuthService
from auth.services.oauth.ya_oauth_service import YandexOAuthService

class OAuthRouter:
    """Base router for OAuth providers"""

    def __init__(
            self,
            prefix: str,
            tags: list[str],
            oauth_service_class: Type[BaseOAuthService]
    ):
        self.router = APIRouter(
            prefix=prefix,
            tags=tags,
            responses={
                status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
                status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
                status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
                status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
            }
        )
        self.oauth_service_class = oauth_service_class
        self._setup_routes()

    async def get_oauth_service(
            self,
            session: AsyncSession = Depends(get_session),
            redis: Redis = Depends(get_redis)
    ) -> BaseOAuthService:
        auth_service = AuthService(session, redis)
        return self.oauth_service_class(session, redis, auth_service)

    async def get_auth_service(
            self,
            session: AsyncSession = Depends(get_session),
            redis: Redis = Depends(get_redis)
    ) -> AuthService:
        return AuthService(session, redis)

    def _setup_routes(self):
        """Set up all OAuth routes"""

        @self.router.get("/login", response_model=AuthUrlResponse)
        async def login(
                request: Request,
                oauth_service: BaseOAuthService = Depends(self.get_oauth_service)
        ) -> AuthUrlResponse:
            try:
                auth_data = await oauth_service.get_auth_url()

                # Store request metadata
                if 'state' in auth_data:
                    request_data = {
                        'ip': request.client.host,
                        'user_agent': request.headers.get('user-agent', 'unknown')
                    }
                    request_key = f"oauth:request:{auth_data['state']}"
                    await oauth_service.redis.setex(request_key, 600, str(request_data))

                return AuthUrlResponse(**auth_data)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate auth URL: {str(e)}"
                )

        @self.router.get("/callback", response_model=TokenResponse)
        async def callback(
                request: Request,
                code: str,
                state: str | None = None,
                error: str | None = None,
                error_description: str | None = None,
                device_id: str | None = None,
                oauth_service: BaseOAuthService = Depends(self.get_oauth_service)
        ) -> TokenResponse:
            if error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"OAuth error: {error_description or error}"
                )

            try:
                metadata = None
                if state:
                    request_key = f"oauth:request:{state}"
                    request_data = await oauth_service.redis.get(request_key)
                    if request_data:
                        metadata = eval(request_data.decode())
                        await oauth_service.redis.delete(request_key)

                tokens = await oauth_service.authenticate(
                    code=code,
                    state=state,
                    device_id=device_id,
                    metadata=metadata
                )
                return TokenResponse(**tokens)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Authentication failed: {str(e)}"
                )

        @self.router.get("/accounts", response_model=SocialAccountList)
        async def get_accounts(
                current_user = Depends(validate_roles()),
                oauth_service: BaseOAuthService = Depends(self.get_oauth_service)
        ) -> SocialAccountList:
            try:
                provider = await oauth_service.get_provider()
                accounts = await oauth_service.auth_service.social_repository.get_user_accounts(
                    user_id=current_user['id'],
                    provider=provider
                )
                return SocialAccountList(accounts=accounts)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to get accounts: {str(e)}"
                )

        @self.router.delete(
            "/unlink/{social_id}",
            status_code=status.HTTP_204_NO_CONTENT
        )
        async def unlink_account(
                social_id: str,
                current_user = Depends(validate_roles()),
                oauth_service: BaseOAuthService = Depends(self.get_oauth_service)
        ):
            try:
                provider = await oauth_service.get_provider()
                social_account = await oauth_service.auth_service.social_repository.get_by_provider_and_social_id(
                    provider,
                    social_id
                )

                if not social_account or social_account.user_id != current_user['id']:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Social account not found"
                    )

                if social_account.access_token:
                    await oauth_service.revoke_access(social_account.access_token)

                await oauth_service.auth_service.unlink_social_account(
                    user_id=current_user['id'],
                    provider=provider,
                    social_id=social_id
                )

                return Response(status_code=status.HTTP_204_NO_CONTENT)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to unlink account: {str(e)}"
                )

        @self.router.post(
            "/refresh/{social_id}",
            response_model=SocialAccountResponse
        )
        async def refresh_token(
                social_id: str,
                current_user = Depends(validate_roles()),
                oauth_service: BaseOAuthService = Depends(self.get_oauth_service)
        ) -> SocialAccountResponse:
            try:
                provider = await oauth_service.get_provider()
                social_account = await oauth_service.auth_service.social_repository.get_by_provider_and_social_id(
                    provider,
                    social_id
                )

                if not social_account or social_account.user_id != current_user['id']:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Social account not found"
                    )

                if not social_account.refresh_token:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No refresh token available"
                    )

                token_data = await oauth_service.refresh_token(social_account.refresh_token)
                updated_account = await oauth_service.auth_service.social_repository.update(
                    social_account.id,
                    {
                        'access_token': token_data['access_token'],
                        'refresh_token': token_data.get('refresh_token'),
                        'token_expires_at': (
                            datetime.now() + timedelta(seconds=token_data['expires_in'])
                            if 'expires_in' in token_data else None
                        )
                    }
                )

                return SocialAccountResponse.model_validate(updated_account)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to refresh token: {str(e)}"
                )


vk_router = OAuthRouter(
    prefix="/vk",
    tags=["vk_oauth"],
    oauth_service_class=VKOAuthService
).router


yandex_router = OAuthRouter(
    prefix="/yandex",
    tags=["yandex_oauth"],
    oauth_service_class=YandexOAuthService
).router