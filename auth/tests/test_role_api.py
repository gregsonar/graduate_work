from datetime import datetime

import pytest
from fastapi import HTTPException
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

from auth.schemas.role_schema import UpdateRoleRequest, UserRoleAssignment, RoleResponse
from auth.services.role_service import RoleService
from auth.api.v1.role_api import get_current_user_roles
from auth.api.v1.role_api import get_roles, get_role, update_role, delete_role, assign_users_to_role, create_role


# Tests for get_roles endpoint
async def test_get_roles_success(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    test_uuid = uuid.uuid4()
    test_datetime = datetime(2024, 11, 8, 7, 36, 26, 540880)

    mock_roles = [
        RoleResponse(
            id=test_uuid,
            name="TEST",
            description="ROLE",
            is_active=True,
            is_deleted=False,
            created_at=test_datetime,
            updated_at=test_datetime,
            users=[]
        )
    ]
    role_service.get_all = AsyncMock(return_value=mock_roles)
    role_service.count = AsyncMock(return_value=1)

    # Act
    result = await get_roles(page=1, size=10, role_service=role_service)

    # Assert
    assert len(result.items) == len(mock_roles)
    assert result.items[0].id == mock_roles[0].id
    assert result.items[0].name == mock_roles[0].name
    assert result.items[0].description == mock_roles[0].description
    assert result.items[0].is_active == mock_roles[0].is_active
    assert result.items[0].is_deleted == mock_roles[0].is_deleted
    assert result.total == 1
    assert result.page == 1
    assert result.size == 10
    role_service.get_all.assert_called_once_with(skip=0, limit=10)


async def test_get_roles_empty_list(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_all = AsyncMock(return_value=[])
    role_service.count = AsyncMock(return_value=0)

    # Act
    result = await get_roles(page=1, size=10, role_service=role_service)

    # Assert
    assert result.items == []
    assert result.total == 0


async def test_get_roles_database_error(mock_session, mock_db_error):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_all = AsyncMock(side_effect=mock_db_error)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_roles(page=1, size=10, role_service=role_service)
    assert exc_info.value.status_code == 500
    assert "Failed to retrieve roles" in str(exc_info.value.detail)


# Tests for get_role endpoint
async def test_get_role_success(mock_session, mock_role):
    # Arrange
    test_uuid = uuid.uuid4()
    test_datetime = datetime(2024, 11, 8, 7, 36, 26, 540880)

    mock_role = RoleResponse(
            id=test_uuid,
            name="TEST",
            description="ROLE",
            is_active=True,
            is_deleted=False,
            created_at=test_datetime,
            updated_at=test_datetime,
            users=[]
        )

    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=mock_role)

    # Act
    result = await get_role(role_id=mock_role.id, role_service=role_service)

    # Assert
    assert result.id == mock_role.id
    assert result.name == mock_role.name
    role_service.get_by_id.assert_called_once_with(mock_role.id)


async def test_get_role_not_found(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=None)
    role_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_role(role_id=role_id, role_service=role_service)
    assert exc_info.value.status_code == 404
    assert f"Role with ID {role_id} not found" in str(exc_info.value.detail)


# Tests for update_role endpoint
async def test_update_role_success(mock_session, mock_role):
    test_uuid = uuid.uuid4()
    test_datetime = datetime(2024, 11, 8, 7, 36, 26, 540880)

    mock_role = RoleResponse(
            id=test_uuid,
            name="TEST",
            description="ROLE",
            is_active=True,
            is_deleted=False,
            created_at=test_datetime,
            updated_at=test_datetime,
            users=[]
        )
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=mock_role)
    role_service.get_by_name = AsyncMock(return_value=None)
    role_service.update = AsyncMock(return_value=mock_role)

    update_data = UpdateRoleRequest(name="new_name", description="new_description")

    # Act
    result = await update_role(
        role_id=mock_role.id,
        role_update=update_data,
        role_service=role_service
    )

    # Assert
    assert result.id == mock_role.id
    role_service.update.assert_called_once()


async def test_update_role_name_conflict(mock_session, mock_role):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=mock_role)
    role_service.get_by_name = AsyncMock(return_value={"id": uuid.uuid4()})

    update_data = UpdateRoleRequest(name="existing_name", description="new_description")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_role(
            role_id=mock_role.id,
            role_update=update_data,
            role_service=role_service
        )
    assert exc_info.value.status_code == 409


# Tests for delete_role endpoint
async def test_delete_role_success(mock_session, mock_role):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=mock_role)
    role_service.delete = AsyncMock(return_value=True)

    # Act
    await delete_role(role_id=mock_role.id, role_service=role_service)

    # Assert
    role_service.delete.assert_called_once_with(mock_role.id)


async def test_delete_role_not_found(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=None)
    role_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_role(role_id=role_id, role_service=role_service)
    assert exc_info.value.status_code == 404


# Tests for assign_users_to_role endpoint
async def test_assign_users_to_role_success(mock_session, mock_role):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=mock_role)
    role_service.give_role_to_user = AsyncMock(return_value=True)

    user_ids = [uuid.uuid4(), uuid.uuid4()]
    assignment = UserRoleAssignment(user_ids=user_ids)

    # Act
    await assign_users_to_role(
        role_id=mock_role.id,
        assignment=assignment,
        role_service=role_service
    )

    # Assert
    assert role_service.give_role_to_user.call_count == len(user_ids)


async def test_assign_users_to_role_failure(mock_session, mock_role):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_id = AsyncMock(return_value=mock_role)
    role_service.give_role_to_user = AsyncMock(return_value=False)

    user_ids = [uuid.uuid4()]
    assignment = UserRoleAssignment(user_ids=user_ids)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await assign_users_to_role(
            role_id=mock_role.id,
            assignment=assignment,
            role_service=role_service
        )
    assert exc_info.value.status_code == 400


# Tests for create_role endpoint
async def test_create_role_success(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_name = AsyncMock(return_value=None)
    role_service.create = AsyncMock(return_value={"id": uuid.uuid4(), "name": "new_role"})

    role_data = UpdateRoleRequest(name="new_role", description="New role description")

    # Act
    result = await create_role(role=role_data, role_service=role_service)

    # Assert
    assert result.name == "new_role"
    role_service.create.assert_called_once()


async def test_create_role_name_exists(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_by_name = AsyncMock(return_value={"id": uuid.uuid4()})

    role_data = UpdateRoleRequest(name="existing_role", description="Description")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_role(role=role_data, role_service=role_service)

    assert exc_info.value.status_code == 409
    assert f"Role with name '{role_data.name}' already exists" in str(exc_info.value.detail)


# Tests for get_current_user_roles endpoint
async def test_get_current_user_roles_success(mock_session):
    # Arrange
    role_service = RoleService(mock_session)
    mock_roles = [{"id": uuid.uuid4(), "name": "user_role"}]
    role_service.get_user_roles = AsyncMock(return_value=mock_roles)

    # Act
    result = await get_current_user_roles(
        current_user={"id": "123e4567-e89"},
        role_service=role_service
    )

    # Assert
    assert result == mock_roles
    role_service.get_user_roles.assert_called_once_with("123e4567-e89")


async def test_get_current_user_roles_error(mock_session, mock_db_error):
    # Arrange
    role_service = RoleService(mock_session)
    role_service.get_user_roles = AsyncMock(side_effect=mock_db_error)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_roles(
            current_user={"id": "123e4567-e89"},
            role_service=role_service
        )
    assert exc_info.value.status_code == 500