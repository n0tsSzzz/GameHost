from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.db.base import get_session
from gamehost_api.domain.lifecycle import ServerNotFound, get_task
from gamehost_api.schemas.servers import TaskResponse

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(task_id: UUID, session: SessionDep) -> object:
    try:
        return await get_task(session, task_id)
    except ServerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
