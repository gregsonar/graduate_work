from datetime import datetime
from typing import List, Optional

from pydantic import UUID4, BaseModel, ConfigDict, IPvAnyAddress

from .entity import BaseResponse


class UserBrief(BaseResponse):
    id: UUID4
    username: str


class AccessLogResponse(BaseResponse):
    id: UUID4
    user_id: UUID4
    ip_address: IPvAnyAddress
    user_agent: str
    accessed_at: datetime
    created_at: datetime
    updated_at: datetime


class AccessLogWithUserResponse(AccessLogResponse):
    user: UserBrief


class AccessLogListResponse(BaseResponse):
    items: List[AccessLogResponse]
    total: int
    page: int
    size: int
