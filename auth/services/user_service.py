import logging
from typing import Any, Dict, List, Type

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from auth.db.crud import UserRepository


class UserService(UserRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
