from typing import Optional

from uuid import UUID

from models import User


def find_user_by_id(uuid: UUID) -> Optional[User]:
    user = User.query.filter_by(id=uuid).first()
    return user
