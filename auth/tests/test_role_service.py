# auth/tests/test_role_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from auth.services.role_service import RoleService
from auth.models.user_role import UserRole

pytestmark = pytest.mark.asyncio


class TestRoleService:
    async def test_give_role_to_user_success(self, mock_session, mock_role, mock_user):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = mock_user.id
        role_id = mock_role.id

        # Mock get_by_id to return our mock role
        role_service.get_by_id = AsyncMock(return_value=mock_role)

        # Mock session.execute для user query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Mock user_role_repository methods
        role_service.user_role_repository.get_user_roles = AsyncMock(return_value=[])
        role_service.user_role_repository.assign_role = AsyncMock()

        # Act
        result = await role_service.give_role_to_user(user_id, role_id)

        # Assert
        assert result is True
        role_service.get_by_id.assert_awaited_once_with(role_id)
        role_service.user_role_repository.assign_role.assert_awaited_once_with(user_id, role_id)

    async def test_give_role_to_user_role_not_found(self, mock_session):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        role_service.get_by_id = AsyncMock(return_value=None)

        # Act
        result = await role_service.give_role_to_user(user_id, role_id)

        # Assert
        assert result is False
        role_service.get_by_id.assert_awaited_once_with(role_id)

    async def test_get_all_users_with_roles_success(self, mock_session, mock_role, mock_user):
        # Arrange
        role_service = RoleService(mock_session)
        role_id = mock_role.id
        expected_users = [mock_user]

        role_service.get_by_id = AsyncMock(return_value=mock_role)

        # Правильная настройка мока для scalars()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = expected_users

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await role_service.get_all_users_with_roles(role_id)

        # Assert
        assert result == expected_users
        role_service.get_by_id.assert_awaited_once_with(role_id)

    async def test_delete_role_from_user_success(self, mock_session, mock_user_role):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = mock_user_role.user_id
        role_id = mock_user_role.role_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user_role
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await role_service.delete_role_from_user(user_id, role_id)

        # Assert
        assert result is True
        mock_session.delete.assert_awaited_once_with(mock_user_role)
        mock_session.commit.assert_awaited_once()

    async def test_delete_role_from_user_not_found(self, mock_session):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await role_service.delete_role_from_user(user_id, role_id)

        # Assert
        assert result is False

    async def test_give_role_to_user_already_has_role(self, mock_session, mock_role, mock_user, mock_user_role):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = mock_user.id
        role_id = mock_role.id

        role_service.get_by_id = AsyncMock(return_value=mock_role)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Создаем existing_user_role с теми же role_id и user_id
        existing_user_role = UserRole(
            user_id=user_id,
            role_id=role_id
        )
        role_service.user_role_repository.get_user_roles = AsyncMock(return_value=[existing_user_role])
        role_service.user_role_repository.assign_role = AsyncMock()

        # Act
        result = await role_service.give_role_to_user(user_id, role_id)

        # Assert
        assert result is True
        # Проверяем, что assign_role не вызывался
        role_service.user_role_repository.assign_role.assert_not_awaited()

    async def test_get_all_users_with_roles_success(self, mock_session, mock_role, mock_user):
        # Arrange
        role_service = RoleService(mock_session)
        role_id = mock_role.id
        expected_users = [mock_user]

        role_service.get_by_id = AsyncMock(return_value=mock_role)

        # Правильная настройка мока для scalars()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = expected_users

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await role_service.get_all_users_with_roles(role_id)

        # Assert
        assert result == expected_users
        role_service.get_by_id.assert_awaited_once_with(role_id)

    async def test_give_role_to_user_exception(self, mock_session, mock_role, mock_user):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = mock_user.id
        role_id = mock_role.id

        # Симулируем ошибку при выполнении операции
        role_service.get_by_id = AsyncMock(side_effect=Exception("Database error"))

        # Act
        result = await role_service.give_role_to_user(user_id, role_id)

        # Assert
        assert result is False
        mock_session.rollback.assert_awaited_once()

    async def test_delete_role_from_user_with_exception(self, mock_session):
        # Arrange
        role_service = RoleService(mock_session)
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()

        # Симулируем ошибку при выполнении операции
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))

        # Act
        result = await role_service.delete_role_from_user(user_id, role_id)

        # Assert
        assert result is False
        mock_session.rollback.assert_awaited_once()