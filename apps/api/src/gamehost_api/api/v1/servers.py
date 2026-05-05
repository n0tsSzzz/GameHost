from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from gamehost_shared.enums import TaskKind
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from gamehost_api.clients.logs import LogsClientProtocol, get_logs_client
from gamehost_api.clients.node_agent import NodeAgentClient
from gamehost_api.core.config import Settings, get_settings
from gamehost_api.core.deps import CurrentUser
from gamehost_api.core.jobs import enqueue_lifecycle_job
from gamehost_api.db.base import get_session
from gamehost_api.db.models import Node, Server, Task, User
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
LogsClientDep = Annotated[LogsClientProtocol, Depends(get_logs_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

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
    settings: SettingsDep,
) -> TaskAcceptedResponse:
    try:
        server, task = await create_server(session, user, payload, _client_ip(request))
    except TemplateNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        ) from exc
    await enqueue_lifecycle_job(settings, task.id)
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
            detail="Server cannot be configured while provisioning or deleting",
        ) from exc


@router.get("/{server_id}/logs")
async def get_server_logs(
    server_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    logs_client: LogsClientDep,
    settings: SettingsDep,
    tail: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> dict[str, list[str]]:
    server = await _get_server_or_404(session, user, server_id)
    if server.container_id is None:
        return {"lines": []}
    if server.node_id is not None:
        node = await session.get(Node, server.node_id)
        if node is not None:
            try:
                return {
                    "lines": await NodeAgentClient(settings).tail_logs(
                        node,
                        server.container_id,
                        tail,
                    )
                }
            except httpx.HTTPError:
                pass
    return {"lines": await logs_client.tail(server.container_id, tail)}


@router.get("/{server_id}/logs/stream")
async def stream_server_logs(
    server_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    logs_client: LogsClientDep,
) -> EventSourceResponse:
    server = await _get_server_or_404(session, user, server_id)
    if server.container_id is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Server has no container")
    container_id = server.container_id

    async def events() -> AsyncIterator[dict[str, str]]:
        async for line in logs_client.stream(container_id):
            yield {"event": "log", "data": line}

    return EventSourceResponse(events())


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
    settings: SettingsDep,
) -> TaskAcceptedResponse:
    return await _enqueue(
        session,
        user,
        server_id,
        TaskKind.START_SERVER,
        _client_ip(request),
        settings,
    )


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
    settings: SettingsDep,
) -> TaskAcceptedResponse:
    return await _enqueue(
        session,
        user,
        server_id,
        TaskKind.STOP_SERVER,
        _client_ip(request),
        settings,
    )


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
    settings: SettingsDep,
) -> TaskAcceptedResponse:
    return await _enqueue(
        session,
        user,
        server_id,
        TaskKind.RESTART_SERVER,
        _client_ip(request),
        settings,
    )


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
    settings: SettingsDep,
) -> TaskAcceptedResponse:
    return await _enqueue(
        session,
        user,
        server_id,
        TaskKind.DELETE_SERVER,
        _client_ip(request),
        settings,
    )


async def _enqueue(
    session: AsyncSession,
    user: User,
    server_id: UUID,
    kind: TaskKind,
    ip: str | None,
    settings: Settings,
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
    await enqueue_lifecycle_job(settings, task.id)
    return _accepted(task, server_id)


def _accepted(task: Task, server_id: UUID | None) -> TaskAcceptedResponse:
    return TaskAcceptedResponse(task_id=task.id, server_id=server_id, status=task.status)


async def _get_server_or_404(session: AsyncSession, user: User, server_id: UUID) -> Server:
    try:
        return await get_accessible_server(session, user, server_id)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
