from typing import Annotated

from fastapi import Depends, HTTPException, status
from gamehost_shared.enums import UserRole

from gamehost_api.api.v1.auth import get_current_user
from gamehost_api.db.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
