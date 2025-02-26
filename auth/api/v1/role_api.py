import uuid
from typing import List

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    status
)

from auth.core.decorators import validate_roles
from auth.schemas.role_schema import (
    CreateRoleResponse,
    RoleListResponse,
    RoleResponse,
    UpdateRoleRequest,
    UserRoleAssignment
)
from auth.services.role_service import RoleService, logger

router = APIRouter(
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal Server Error"},
    }
)


@router.get("/", response_model=RoleListResponse)
async def get_roles(
    current_user=Depends(validate_roles(["admin"])),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Количество элементов на странице"),
    role_service: RoleService = Depends(),
) -> RoleListResponse:
    try:
        roles = await role_service.get_all(skip=(page - 1) * size, limit=size)
        total = await role_service.count()

        return RoleListResponse(items=roles, total=total, page=page, size=size)
    except Exception as e:
        logger.error(f"Failed to retrieve roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve roles: {str(e)}",
        )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    current_user=Depends(validate_roles(["admin"])),
    role_id: uuid.UUID = Path(..., description="UUID роли"),
    role_service: RoleService = Depends(),
) -> RoleResponse:
    try:
        role = await role_service.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )
        return RoleResponse.model_validate(role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve role: {str(e)}",
        )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    current_user=Depends(validate_roles(["admin"])),
    role_id: uuid.UUID = Path(..., description="UUID роли для обновления"),
    role_update: UpdateRoleRequest = Body(
        ..., description="Данные для обновления роли"
    ),
    role_service: RoleService = Depends(),
) -> RoleResponse:
    try:
        existing_role = await role_service.get_by_id(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )

        if role_update.name != existing_role.name:
            name_exists = await role_service.get_by_name(role_update.name)
            if name_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{role_update.name}' already exists",
                )

        update_data = {"name": role_update.name, "description": role_update.description}
        updated_role = await role_service.update(existing_role.id, update_data)

        return RoleResponse.model_validate(updated_role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}",
        )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Роль успешно удалена"},
        status.HTTP_404_NOT_FOUND: {"description": "Роль не найдена"},
    },
)
async def delete_role(
    current_user=Depends(validate_roles(["admin"])),
    role_id: uuid.UUID = Path(..., description="UUID роли для удаления"),
    role_service: RoleService = Depends(),
):
    try:
        existing_role = await role_service.get_by_id(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )

        success = await role_service.delete(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}",
        )


@router.post(
    "/{role_id}/users",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Назначить роль пользователям",
    description="Назначает роль списку пользователей по их идентификаторам.",
)
async def assign_users_to_role(
    current_user=Depends(validate_roles(["admin"])),
    role_id: uuid.UUID = Path(..., description="UUID роли"),
    assignment: UserRoleAssignment = Body(..., description="Список UUID пользователей"),
    role_service: RoleService = Depends(),
):
    try:
        role = await role_service.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )

        for user_id in assignment.user_ids:
            success = await role_service.give_role_to_user(user_id, role_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to assign role to user {user_id}",
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign users to role: {str(e)}",
        )


@router.delete(
    "/{role_id}/users",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить роль у пользователей",
    description="Удаляет роль у списка пользователей по их идентификаторам.",
)
async def remove_users_from_role(
    current_user=Depends(validate_roles(["admin"])),
    role_id: uuid.UUID = Path(..., description="UUID роли"),
    assignment: UserRoleAssignment = Body(..., description="Список UUID пользователей"),
    role_service: RoleService = Depends(),
):
    try:
        role = await role_service.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )

        for user_id in assignment.user_ids:
            success = await role_service.delete_role_from_user(user_id, role_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to remove role from user {user_id}",
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove users from role: {str(e)}",
        )


@router.post(
    "/",
    response_model=CreateRoleResponse,
    summary="Создать роль",
    description="Создает новую роль",
)
async def create_role(
    current_user=Depends(validate_roles(["admin"])),
    role: UpdateRoleRequest = Body(..., description="Данные для создания роли"),
    role_service: RoleService = Depends(),
):
    try:
        name_exists = await role_service.get_by_name(role.name)
        if name_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{role.name}' already exists",
            )

        role_data = role.model_dump()
        role = await role_service.create(role_data)
        return CreateRoleResponse.model_validate(role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}",
        )


@router.get("/{role_id}/users", response_model=UserRoleAssignment)
async def get_users_by_role(
    current_user=Depends(validate_roles(["admin"])),
    role_id: uuid.UUID = Path(..., description="UUID роли"),
    role_service: RoleService = Depends(),
):
    try:
        role = await role_service.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found",
            )

        users = await role_service.get_users_by_role(role_id)
        return [user["id"] for user in users]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users for role: {str(e)}",
        )


@router.get("/me/roles", response_model=RoleListResponse)
async def get_current_user_roles(
    current_user=Depends(validate_roles()), role_service: RoleService = Depends()
):
    try:
        roles = await role_service.get_user_roles(current_user["id"])
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve roles: {str(e)}",
        )


@router.get("/users/{user_id}/roles", response_model=RoleListResponse)
async def get_user_roles(
    current_user=Depends(validate_roles(["admin"])),
    user_id: uuid.UUID = Path(..., description="UUID пользователя"),
    role_service: RoleService = Depends(),
) -> List[RoleResponse]:
    try:
        roles = await role_service.get_user_roles(user_id)
        if not roles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found or has no roles",
            )
        return roles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving roles",
        )
