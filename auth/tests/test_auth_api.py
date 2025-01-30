import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status
from uuid import UUID

from auth.api.v1.auth_api import router, AuthRequest, TokenResponse, UserCreate, get_current_user, logout, login, \
    refresh, register
from auth.services.auth_service import AuthService
from auth.services.token_service import TokenService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_auth_service():
    service = AsyncMock(spec=AuthService)
    return service


@pytest.fixture
def mock_token_service():
    service = AsyncMock(spec=TokenService)
    return service


class TestAuthAPI:
    async def test_login_success(self, mock_auth_service):
        # Arrange
        auth_request = AuthRequest(username="newuser", password="SECUREpass")
        expected_tokens = {"access_token": "access123", "refresh_token": "refresh123"}
        mock_auth_service.authenticate_user.return_value = expected_tokens

        # Act
        response = await login(auth_request, mock_auth_service)

        # Assert
        assert isinstance(response, TokenResponse)
        assert response.access_token == expected_tokens["access_token"]
        assert response.refresh_token == expected_tokens["refresh_token"]
        mock_auth_service.authenticate_user.assert_awaited_once_with(
            auth_request.username, auth_request.password
        )

    async def test_login_invalid_credentials(self, mock_auth_service):
        # Arrange
        auth_request = AuthRequest(username="wrong", password="longbutwrong")
        mock_auth_service.authenticate_user.side_effect = Exception("Invalid credentials")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await login(auth_request, mock_auth_service)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in str(exc_info.value.detail)

    async def test_logout_success(self, mock_auth_service):
        # Arrange
        access_token = "access123"
        refresh_token = "refresh123"
        mock_auth_service.logout_user.return_value = None

        # Act
        response = await logout(access_token, refresh_token, mock_auth_service)

        # Assert
        assert response == {"detail": "Successfully logged out"}
        mock_auth_service.logout_user.assert_awaited_once_with(access_token, refresh_token)

    async def test_logout_failure(self, mock_auth_service):
        # Arrange
        access_token = "access123"
        refresh_token = "refresh123"
        mock_auth_service.logout_user.side_effect = Exception("Logout failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await logout(access_token, refresh_token, mock_auth_service)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Logout failed" in str(exc_info.value.detail)

    async def test_refresh_success(self, mock_auth_service):
        # Arrange
        refresh_token = "refresh123"
        expected_tokens = {"access_token": "newaccess123", "refresh_token": "newrefresh123"}
        mock_auth_service.refresh_token.return_value = expected_tokens

        # Act
        response = await refresh(refresh_token, mock_auth_service)

        # Assert
        assert isinstance(response, TokenResponse)
        assert response.access_token == expected_tokens["access_token"]
        assert response.refresh_token == expected_tokens["refresh_token"]
        mock_auth_service.refresh_token.assert_awaited_once_with(refresh_token)

    async def test_refresh_invalid_token(self, mock_auth_service):
        # Arrange
        refresh_token = "invalid123"
        mock_auth_service.refresh_token.side_effect = Exception("Invalid refresh token")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await refresh(refresh_token, mock_auth_service)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid refresh token" in str(exc_info.value.detail)

    async def test_register_success(self, mock_auth_service):
        # Arrange
        user_create = UserCreate(username="newuser", password="newSECUREpass")
        mock_user = MagicMock()
        mock_user.id = UUID("123e4567-e89b-12d3-a456-426614174000")
        expected_tokens = {"access_token": "access123", "refresh_token": "refresh123"}

        mock_auth_service.register_user.return_value = mock_user
        mock_auth_service.authenticate_user.return_value = expected_tokens

        # Act
        response = await register(user_create, mock_auth_service)

        # Assert
        assert isinstance(response, TokenResponse)
        assert response.access_token == expected_tokens["access_token"]
        assert response.refresh_token == expected_tokens["refresh_token"]
        mock_auth_service.register_user.assert_awaited_once_with(
            user_create.username, user_create.password
        )
        mock_auth_service.authenticate_user.assert_awaited_once_with(
            user_create.username, user_create.password
        )

    async def test_register_user_exists(self, mock_auth_service):
        # Arrange
        user_create = UserCreate(username="existinguser", password="longsecurepass")
        mock_auth_service.register_user.side_effect = Exception("User already exists")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await register(user_create, mock_auth_service)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "User already exists" in str(exc_info.value.detail)

    async def test_get_current_user_success(self, mock_token_service):
        # Arrange
        token = "validtoken123"
        expected_user_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "is_superuser": False,
            "roles": ["user"]
        }
        mock_token_service.get_current_user.return_value = expected_user_data

        # Act
        response = await get_current_user(token, mock_token_service)

        # Assert
        assert response == expected_user_data
        mock_token_service.get_current_user.assert_awaited_once_with(token)

    async def test_get_current_user_not_found(self, mock_token_service):
        # Arrange
        token = "validtoken123"
        mock_token_service.get_current_user.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_token_service)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in str(exc_info.value.detail)

    async def test_get_current_user_invalid_token(self, mock_token_service):
        # Arrange
        token = "invalidtoken123"
        mock_token_service.get_current_user.side_effect = Exception("Invalid token")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_token_service)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid token" in str(exc_info.value.detail)
