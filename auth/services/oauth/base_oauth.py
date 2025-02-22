from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import secrets
import base64
import hashlib
import aiohttp
from redis.asyncio import Redis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.core.config import OAuthProviderSettings
from auth.models.base_models import SocialProvider
from auth.services.auth_service import AuthService


class OAuthFlowStrategy(ABC):
    """Base strategy for OAuth flow implementation"""

    @abstractmethod
    async def generate_auth_params(self) -> Dict[str, str]:
        """Generate parameters for authorization URL"""
        pass

    @abstractmethod
    async def exchange_code_for_token(
        self,
        code: str,
        state: Optional[str] = None,
        device_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        pass


class PKCEFlowStrategy(OAuthFlowStrategy):
    """PKCE OAuth flow implementation"""

    def __init__(self, settings: OAuthProviderSettings, redis: Redis):
        self.settings = settings
        self.redis = redis

    async def generate_code_verifier(self, length: int = 64) -> str:
        """Generate PKCE code verifier"""
        import string

        alphabet = string.ascii_letters + string.digits + "-._~"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code challenge"""
        sha256_hash = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(sha256_hash).decode().rstrip("=")

    async def generate_auth_params(self) -> Dict[str, str]:
        """Generate parameters for PKCE authorization"""
        code_verifier = await self.generate_code_verifier()
        code_challenge = await self.generate_code_challenge(code_verifier)
        state = secrets.token_urlsafe(32)

        # Store code_verifier for later use
        verifier_key = f"oauth:verifier:{state}"
        await self.redis.setex(verifier_key, 600, code_verifier)  # 10 minute TTL

        return {
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

    async def exchange_code_for_token(
        self,
        code: str,
        state: Optional[str] = None,
        device_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens using PKCE flow"""
        if not state:
            raise ValueError("State parameter is required for PKCE flow")

        # Get stored code_verifier
        verifier_key = f"oauth:verifier:{state}"
        code_verifier = await self.redis.get(verifier_key)

        if not code_verifier:
            raise ValueError("Invalid or expired state parameter")

        params = {
            "grant_type": "authorization_code",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "redirect_uri": self.settings.redirect_url,
            "code": code,
            "code_verifier": code_verifier.decode(),
            "device_id": device_id,
        }

        # Add any additional parameters
        params.update(kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.settings.token_url, data=params, ssl=False
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to exchange code: HTTP {response.status}, {error_text}",
                    )

                data = await response.json()
                if "error" in data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"OAuth error: {data.get('error_description', data['error'])}",
                    )

                # Delete used code_verifier
                await self.redis.delete(verifier_key)

                return data


class SimpleOAuthFlowStrategy(OAuthFlowStrategy):
    """Simple OAuth flow implementation"""

    def __init__(self, settings: OAuthProviderSettings):
        self.settings = settings

    async def generate_auth_params(self) -> Dict[str, str]:
        """Generate parameters for simple OAuth flow"""
        return {"state": secrets.token_urlsafe(32)}

    async def exchange_code_for_token(
        self, code: str, state: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens using simple OAuth flow"""
        params = {
            "grant_type": "authorization_code",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret,
            "redirect_uri": self.settings.redirect_url,
            "code": code,
        }

        # Add any additional parameters
        params.update(kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(self.settings.token_url, data=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to exchange code: HTTP {response.status}, {error_text}",
                    )

                data = await response.json()
                if "error" in data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"OAuth error: {data.get('error_description', data['error'])}",
                    )

                return data


class BaseOAuthService(ABC):
    """Base class for OAuth services"""

    def __init__(
        self,
        session: AsyncSession,
        redis: Redis,
        auth_service: AuthService,
        settings: OAuthProviderSettings,
        flow_strategy: OAuthFlowStrategy,
    ):
        self.session = session
        self.redis = redis
        self.auth_service = auth_service
        self.settings = settings
        self.flow_strategy = flow_strategy
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def get_http_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session

    async def close(self):
        """Close HTTP session"""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

    @abstractmethod
    async def get_provider(self) -> SocialProvider:
        """Get OAuth provider type"""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from provider"""
        pass

    async def get_auth_url(self) -> Dict[str, str]:
        """Generate authorization URL with parameters"""
        auth_params = await self.flow_strategy.generate_auth_params()
        params = {
            "client_id": self.settings.client_id,
            "redirect_uri": self.settings.redirect_url,
            "response_type": "code",
            **auth_params,
        }

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return {
            "auth_url": f"{self.settings.auth_url}?{query}",
            "state": auth_params.get("state"),
        }

    @abstractmethod
    async def process_user_info(
        self, user_info: Dict[str, Any], token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user information into standard format"""
        pass

    async def authenticate(
        self,
        code: str,
        state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, str]:
        """Complete authentication flow"""
        # Exchange code for token
        token_data = await self.flow_strategy.exchange_code_for_token(
            code, state, device_id, **kwargs
        )

        # Get user information
        user_info = await self.get_user_info(token_data["access_token"])

        # Process user data
        social_data = await self.process_user_info(user_info, token_data)

        # Authenticate using auth service
        return await self.auth_service.authenticate_social_user(
            provider=await self.get_provider(),
            social_id=str(user_info.get("user_id")),
            social_data=social_data,
            metadata=metadata,
        )
