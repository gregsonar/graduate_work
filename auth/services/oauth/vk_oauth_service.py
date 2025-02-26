from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import HTTPException, status

from auth.core.config import oauth_config
from auth.models.base_models import SocialProvider

from .base_oauth import BaseOAuthService, PKCEFlowStrategy


class VKOAuthService(BaseOAuthService):
    """VK OAuth service implementation"""

    def __init__(self, session, redis, auth_service):
        settings = oauth_config.vk
        flow_strategy = PKCEFlowStrategy(settings, redis)
        super().__init__(session, redis, auth_service, settings, flow_strategy)

    async def get_provider(self) -> SocialProvider:
        return SocialProvider.VK

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from VK"""
        params = {"client_id": self.settings.client_id, "access_token": access_token}

        async with await self.get_http_session() as session:
            async with session.post(
                self.settings.user_info_url, data=params, ssl=False
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to get user info: HTTP {response.status}",
                    )

                data = await response.json()
                if "error" in data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"API error: {data.get('error_description', data['error'])}",
                    )

                return data["user"]

    async def process_user_info(
        self, user_info: Dict[str, Any], token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process VK user information into standard format"""
        return {
            "social_id": str(user_info.get("user_id")),
            "social_username": None,
            "social_email": user_info.get("email"),
            "first_name": user_info.get("first_name"),
            "last_name": user_info.get("last_name"),
            "avatar_url": user_info.get("avatar"),
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": (
                datetime.now() + timedelta(seconds=token_data["expires_in"])
                if "expires_in" in token_data
                else None
            ),
            "metadata": {
                "verified": user_info.get("verified", False),
                "sex": user_info.get("sex"),
                "birthday": user_info.get("birthday"),
                "scope": token_data.get("scope"),
                "raw_data": user_info,
            },
        }

    async def revoke_access(self, access_token: str) -> bool:
        """Revoke VK access token"""
        params = {"client_id": self.settings.client_id, "access_token": access_token}

        async with await self.get_http_session() as session:
            async with session.post(
                "https://id.vk.com/oauth2/revoke", data=params, ssl=False
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()
                return data.get("response") == 1
