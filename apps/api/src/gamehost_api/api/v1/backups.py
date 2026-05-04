from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.deps import CurrentUser
from gamehost_api.db.base import get_session
from gamehost_api.db.models import Backup
from gamehost_api.domain.backups import (
    BackupForbidden,
    BackupNotFound,
    create_backup_task,
    list_backups,
    restore_backup_task,
)
from gamehost_api.domain.lifecycle import ServerNotFound
from gamehost_api.schemas.backups import BackupResponse
from gamehost_api.schemas.servers import TaskAcceptedResponse

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(tags=["backups"])


@router.get("/servers/{server_id}/backups", response_model=list[BackupResponse])
async def get_backups(server_id: UUID, session: SessionDep, user: CurrentUser) -> list[Backup]:
    try:
        return await list_backups(session, user, server_id)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc


@router.post(
    "/servers/{server_id}/backups",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_backup(
    server_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    try:
        backup, task = await create_backup_task(session, user, server_id)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
    except BackupForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from exc
    return TaskAcceptedResponse(task_id=task.id, server_id=backup.server_id, status=task.status)


@router.post(
    "/backups/{backup_id}/restore",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_restore(
    backup_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    try:
        task = await restore_backup_task(session, user, backup_id)
    except (BackupNotFound, ServerNotFound) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found",
        ) from exc
    except BackupForbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from exc
    return TaskAcceptedResponse(task_id=task.id, server_id=task.server_id, status=task.status)
