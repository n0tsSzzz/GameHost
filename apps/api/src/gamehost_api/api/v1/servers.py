from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from gamehost_shared.enums import TaskKind
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.deps import CurrentUser
from gamehost_api.db.base import get_session
from gamehost_api.db.models import Server, Task, User
from gamehost_api.domain.lifecycle import (
    InvalidServerState,
    ServerNotFound,
    TemplateNotFound,
    create_server,
    enqueue_lifecycle_task,
    get_accessible_server,
    list_accessible_servers,
    update_server_config,
)
from gamehost_api.schemas.servers import (
    ServerCreate,
    ServerResponse,
    ServerUpdate,
    TaskAcceptedResponse,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/servers", tags=["servers"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client is not None else None


@router.get("", response_model=list[ServerResponse])
async def get_servers(session: SessionDep, user: CurrentUser) -> list[Server]:
    return await list_accessible_servers(session, user)


@router.post("", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def post_server(
    payload: ServerCreate,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    try:
        server, task = await create_server(session, user, payload, _client_ip(request))
    except TemplateNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        ) from exc
    return _accepted(task, server.id)


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(server_id: UUID, session: SessionDep, user: CurrentUser) -> Server:
    try:
        return await get_accessible_server(session, user, server_id)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc


@router.patch("/{server_id}", response_model=ServerResponse)
async def patch_server(
    server_id: UUID,
    payload: ServerUpdate,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> Server:
    try:
        return await update_server_config(session, user, server_id, payload, _client_ip(request))
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
    except InvalidServerState as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Server must be stopped before updating config",
        ) from exc


@router.post(
    "/{server_id}/start",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_server(
    server_id: UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    return await _enqueue(session, user, server_id, TaskKind.START_SERVER, _client_ip(request))


@router.post(
    "/{server_id}/stop",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def stop_server(
    server_id: UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    return await _enqueue(session, user, server_id, TaskKind.STOP_SERVER, _client_ip(request))


@router.post(
    "/{server_id}/restart",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def restart_server(
    server_id: UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    return await _enqueue(session, user, server_id, TaskKind.RESTART_SERVER, _client_ip(request))


@router.delete(
    "/{server_id}",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def delete_server(
    server_id: UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUser,
) -> TaskAcceptedResponse:
    return await _enqueue(session, user, server_id, TaskKind.DELETE_SERVER, _client_ip(request))


async def _enqueue(
    session: AsyncSession,
    user: User,
    server_id: UUID,
    kind: TaskKind,
    ip: str | None,
) -> TaskAcceptedResponse:
    try:
        task = await enqueue_lifecycle_task(session, user, server_id, kind, ip)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
    except InvalidServerState as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invalid server state",
        ) from exc
    return _accepted(task, server_id)


def _accepted(task: Task, server_id: UUID | None) -> TaskAcceptedResponse:
    return TaskAcceptedResponse(task_id=task.id, server_id=server_id, status=task.status)
