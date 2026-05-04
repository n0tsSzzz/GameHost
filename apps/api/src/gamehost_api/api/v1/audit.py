from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.deps import AdminUser
from gamehost_api.db.base import get_session
from gamehost_api.db.models import AuditLog
from gamehost_api.domain.audit import list_audit_logs
from gamehost_api.schemas.audit import AuditLogResponse

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
async def get_audit_logs(
    session: SessionDep,
    _admin: AdminUser,
    target_type: Annotated[str | None, Query(alias="targetType")] = None,
    target_id: Annotated[str | None, Query(alias="targetId")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLog]:
    return await list_audit_logs(session, target_type, target_id, limit)
