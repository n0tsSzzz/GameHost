from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sse_starlette.sse import EventSourceResponse

from gamehost_node.deps import DockerOpsDep
from gamehost_node.logs import LogPublisher, get_log_publisher
from gamehost_node.schemas import (
    ContainerCreateRequest,
    ContainerResponse,
    ExecRequest,
    LogsResponse,
)
from gamehost_node.security import require_api_key

router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@protected_router.post(
    "/containers",
    response_model=ContainerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_container(
    payload: ContainerCreateRequest,
    docker_ops: DockerOpsDep,
) -> ContainerResponse:
    return await docker_ops.create_container(payload)


@protected_router.post("/containers/{container_id}/start", response_model=ContainerResponse)
async def start_container(container_id: str, docker_ops: DockerOpsDep) -> ContainerResponse:
    return await docker_ops.start_container(container_id)


@protected_router.post("/containers/{container_id}/stop", response_model=ContainerResponse)
async def stop_container(container_id: str, docker_ops: DockerOpsDep) -> ContainerResponse:
    return await docker_ops.stop_container(container_id)


@protected_router.post("/containers/{container_id}/restart", response_model=ContainerResponse)
async def restart_container(container_id: str, docker_ops: DockerOpsDep) -> ContainerResponse:
    return await docker_ops.restart_container(container_id)


@protected_router.delete("/containers/{container_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_container(container_id: str, docker_ops: DockerOpsDep) -> Response:
    await docker_ops.delete_container(container_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@protected_router.get("/containers/{container_id}", response_model=ContainerResponse)
async def inspect_container(container_id: str, docker_ops: DockerOpsDep) -> ContainerResponse:
    return await docker_ops.inspect_container(container_id)


@protected_router.get("/containers/{container_id}/logs", response_model=LogsResponse)
async def tail_container_logs(
    container_id: str,
    docker_ops: DockerOpsDep,
    tail: int = Query(default=200, ge=1, le=1000),
) -> LogsResponse:
    return LogsResponse(lines=await docker_ops.tail_logs(container_id, tail))


@protected_router.get("/containers/{container_id}/logs/stream")
async def stream_container_logs(
    container_id: str,
    docker_ops: DockerOpsDep,
    log_publisher: Annotated[LogPublisher, Depends(get_log_publisher)],
) -> EventSourceResponse:
    async def events() -> AsyncIterator[dict[str, str]]:
        async for line in docker_ops.stream_logs(container_id):
            await log_publisher.publish(container_id, line)
            yield {"event": "log", "data": line}

    return EventSourceResponse(events())


@protected_router.post("/containers/{container_id}/exec")
async def exec_container(
    container_id: str,
    payload: ExecRequest,
    docker_ops: DockerOpsDep,
) -> dict[str, str]:
    return {"output": await docker_ops.exec_container(container_id, payload.command)}


router.include_router(protected_router)
