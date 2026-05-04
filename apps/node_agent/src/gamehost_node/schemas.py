from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel, Field


class ContainerCreateRequest(BaseModel):
    name: str
    image: str
    env: dict[str, str] = Field(default_factory=dict)
    ports: dict[str, int] = Field(default_factory=dict)
    volumes: dict[str, dict[str, str]] = Field(default_factory=dict)
    cpu_limit: float | None = None
    mem_limit_mb: int | None = None
    read_only: bool = False


class ContainerResponse(BaseModel):
    id: str
    name: str
    status: str


class ExecRequest(BaseModel):
    command: list[str]


class DockerOpsProtocol(Protocol):
    async def create_container(self, payload: ContainerCreateRequest) -> ContainerResponse:
        raise NotImplementedError

    async def start_container(self, container_id: str) -> ContainerResponse:
        raise NotImplementedError

    async def stop_container(self, container_id: str) -> ContainerResponse:
        raise NotImplementedError

    async def restart_container(self, container_id: str) -> ContainerResponse:
        raise NotImplementedError

    async def delete_container(self, container_id: str) -> None:
        raise NotImplementedError

    async def inspect_container(self, container_id: str) -> ContainerResponse:
        raise NotImplementedError

    def stream_logs(self, container_id: str) -> AsyncIterator[str]:
        raise NotImplementedError

    async def exec_container(self, container_id: str, command: list[str]) -> str:
        raise NotImplementedError
