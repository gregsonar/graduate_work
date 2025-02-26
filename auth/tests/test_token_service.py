import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from auth.core.config import TokenConfig
from auth.services.token_service import TokenService

pytestmark = pytest.mark.asyncio


class TestTokenService:
    async def test_create_access_token_success(self, token_service, mock_user):
        # Arrange
        user_id = mock_user.id
        username = mock_user.username
        is_superuser = mock_user.is_superuser
        roles = ["user"]

        # Act
        token = await token_service.create_access_token(
            user_id=user_id, username=username, is_superuser=is_superuser, roles=roles
        )

        # Assert
        assert token is not None
        payload = jwt.decode(
            token,
            token_service.config.secret_key,
            algorithms=[token_service.config.algorithm],
        )
        assert payload["user_id"] == str(user_id)
        assert payload["username"] == username
        assert payload["is_superuser"] == is_superuser
        assert payload["roles"] == roles
        assert payload["token_type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    async def test_create_refresh_token_success(self, token_service, mock_user):
        # Arrange
        user_id = mock_user.id

        # Act
        token = await token_service.create_refresh_token(user_id)

        # Assert
        assert token is not None
        payload = jwt.decode(
            token,
            token_service.config.secret_key,
            algorithms=[token_service.config.algorithm],
        )
        assert payload["user_id"] == str(user_id)
        assert payload["token_type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    async def test_validate_token_success(self, token_service, mock_user):
        # Arrange
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.is_token_blacklisted = AsyncMock(return_value=False)

        # Act
        payload = await token_service.validate_token(token)

        # Assert
        assert payload is not None
        assert payload["user_id"] == str(mock_user.id)
        assert payload["username"] == mock_user.username
        assert "jti" in payload

    async def test_validate_token_blacklisted(self, token_service, mock_user):
        # Arrange
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.is_token_blacklisted = AsyncMock(return_value=True)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await token_service.validate_token(token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token has been blacklisted"

    async def test_validate_token_expired(self, token_service, mock_user):
        # Arrange
        token_service.config.access_token_expire_minutes = -1  # Make token expired
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.is_token_blacklisted = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await token_service.validate_token(token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Token has expired"

    async def test_refresh_tokens_success(self, token_service, mock_user):
        token_service.is_token_blacklisted = AsyncMock(return_value=False)

        refresh_token = await token_service.create_refresh_token(mock_user.id)
        token_service.user_repository.get_with_roles = AsyncMock(return_value=mock_user)
        token_service.blacklist_token = AsyncMock()

        # Act
        new_access_token, new_refresh_token = await token_service.refresh_tokens(
            refresh_token
        )

        # Assert
        assert new_access_token is not None
        assert new_refresh_token is not None
        token_service.blacklist_token.assert_awaited_once_with(refresh_token)

    async def test_refresh_tokens_invalid_type(self, token_service, mock_user):
        # Arrange
        access_token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.is_token_blacklisted = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await token_service.refresh_tokens(access_token)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token type"

    async def test_blacklist_token_success(self, token_service, mock_user):
        # Arrange
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        payload = jwt.decode(
            token,
            token_service.config.secret_key,
            algorithms=[token_service.config.algorithm],
        )
        token_service.redis_client.setex = AsyncMock()

        # Act
        await token_service.blacklist_token(token)

        # Assert
        token_service.redis_client.setex.assert_awaited_once()
        call_args = token_service.redis_client.setex.call_args[0]
        assert call_args[0] == f"blacklist_token:{payload['jti']}"
        assert isinstance(call_args[1], int)
        assert call_args[2] == "1"

    async def test_is_token_blacklisted_true(self, token_service, mock_user):
        # Arrange
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.redis_client.exists = AsyncMock(return_value=1)

        # Act
        result = await token_service.is_token_blacklisted(token)

        # Assert
        assert result is True

    async def test_is_token_blacklisted_false(self, token_service, mock_user):
        # Arrange
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.redis_client.exists = AsyncMock(return_value=0)

        # Act
        result = await token_service.is_token_blacklisted(token)

        # Assert
        assert result is False

    async def test_create_tokens_for_user_success(self, token_service, mock_user):
        # Arrange
        token_service.user_repository.get_with_roles = AsyncMock(return_value=mock_user)

        # Act
        access_token, refresh_token = await token_service.create_tokens_for_user(
            mock_user.id
        )

        # Assert
        assert access_token is not None
        assert refresh_token is not None
        token_service.user_repository.get_with_roles.assert_awaited_once_with(
            mock_user.id
        )

    async def test_create_tokens_for_user_not_found(self, token_service):
        # Arrange
        user_id = uuid.uuid4()
        token_service.user_repository.get_with_roles = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await token_service.create_tokens_for_user(user_id)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"

    async def test_get_current_user_success(self, token_service, mock_user):
        # Arrange
        token_service.is_token_blacklisted = AsyncMock(return_value=False)

        # Сначала получаем роли от mock_user
        user_roles = [role.name for role in mock_user.roles]

        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=user_roles,  # Используем полученные роли
        )
        token_service.user_repository.get_with_roles = AsyncMock(return_value=mock_user)

        # Act
        user_data = await token_service.get_current_user(token)

        # Assert
        assert user_data is not None
        assert user_data["id"] == mock_user.id
        assert user_data["username"] == mock_user.username
        assert user_data["is_superuser"] == mock_user.is_superuser
        assert user_data["roles"] == user_roles

    async def test_get_current_user_not_found(self, token_service, mock_user):
        # Arrange
        token = await token_service.create_access_token(
            user_id=mock_user.id,
            username=mock_user.username,
            is_superuser=mock_user.is_superuser,
            roles=["user"],
        )
        token_service.user_repository.get_with_roles = AsyncMock(return_value=None)
        token_service.is_token_blacklisted = AsyncMock(return_value=False)
        # Act
        user_data = await token_service.get_current_user(token)

        # Assert
        assert user_data is None
