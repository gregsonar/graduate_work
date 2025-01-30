import uuid
from pydantic import BaseModel, UUID4, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
from .entity import BaseResponse

class UserBrief(BaseResponse):
    """Brief user information for nested responses."""
    id: UUID4 = Field(..., description="User's unique identifier")
    username: str = Field(..., description="Username", min_length=1, max_length=50)

class RoleResponse(BaseResponse):
    """Complete role information response model."""
    id: UUID4 = Field(..., description="Role's unique identifier")
    name: str = Field(..., description="Role name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Role description")
    is_active: bool = Field(..., description="Role activity status")
    is_deleted: bool = Field(..., description="Role deletion status")
    created_at: datetime = Field(..., description="Role creation timestamp")
    updated_at: datetime = Field(..., description="Role last update timestamp")
    users: List[UserBrief] = Field(default=[], description="Users with this role")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "987fcdeb-51a2-43d7-9012-345678901234",
                "name": "admin",
                "description": "System administrator with full access",
                "is_active": True,
                "is_deleted": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "users": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "john_doe"
                    }
                ]
            }
        }

class RoleListResponse(BaseResponse):
    """Paginated role list response."""
    items: List[RoleResponse] = Field(..., description="List of roles")
    total: int = Field(..., description="Total record count", ge=0)
    page: int = Field(..., description="Current page number", ge=1)
    size: int = Field(..., description="Page size", ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "987fcdeb-51a2-43d7-9012-345678901234",
                        "name": "admin",
                        "description": "System administrator with full access",
                        "is_active": True,
                        "is_deleted": False,
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00",
                        "users": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "username": "john_doe"
                            }
                        ]
                    }
                ],
                "total": 100,
                "page": 1,
                "size": 10
            }
        }

class UserRoleAssignment(BaseModel):
    """Role assignment schema."""
    user_ids: List[uuid.UUID] = Field(..., description="User UUIDs for role assignment/removal")

class UpdateRoleRequest(BaseModel):
    """Role update schema."""
    name: str = Field(..., description="New role name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="New role description")

class CreateRoleResponse(BaseModel):
    """Role creation response schema."""
    id: uuid.UUID = Field(description="Role unique identifier")
    name: str = Field(description="Role name")
    description: str | None = Field(default=None, description="Role description")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "admin",
                "description": "Administrator role with full access"
            }
        }