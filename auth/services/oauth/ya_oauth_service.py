from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import HTTPException, status

from auth.core.config import oauth_config
from auth.models.base_models import SocialProvider

from .base_oauth import BaseOAuthService, SimpleOAuthFlowStrategy


class YandexOAuthService(BaseOAuthService):
    """Yandex OAuth service implementation"""

    def __init__(self, session, redis, auth_service):
        settings = oauth_config.yandex
        flow_strategy = SimpleOAuthFlowStrategy(settings)
        super().__init__(session, redis, auth_service, settings, flow_strategy)

    async def get_provider(self) -> SocialProvider:
        return SocialProvider.YANDEX

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Yandex"""
        async with await self.get_http_session() as session:
            async with session.get(
                self.settings.user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to get user info: HTTP {response.status}",
                    )

                return await response.json()

    async def process_user_info(
        self, user_info: Dict[str, Any], token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process Yandex user information into standard format"""
        return {
            "social_id": str(user_info.get("id")),
            "social_username": user_info.get("login"),
            "social_email": user_info.get("default_email"),
            "first_name": user_info.get("first_name"),
            "last_name": user_info.get("last_name"),
            "avatar_url": user_info.get("default_avatar_id"),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": (
                datetime.now() + timedelta(seconds=token_data["expires_in"])
                if "expires_in" in token_data
                else None
            ),
            "metadata": {
                "verified": user_info.get("is_verified", False),
                "real_name": user_info.get("real_name"),
                "birthday": user_info.get("birthday"),
                "scope": token_data.get("scope"),
                "raw_data": user_info,
            },
        }

    async def revoke_access(self, access_token: str) -> None:
        """Revoke Yandex access token"""
        async with await self.get_http_session() as session:
            async with session.post(
                "https://oauth.yandex.ru/revoke_token",
                headers={"Authorization": f"Bearer {access_token}"},
                data={"token": access_token},
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to revoke access: {response.status}",
                    )
