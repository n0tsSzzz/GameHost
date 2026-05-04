from uuid import UUID

from gamehost_shared.enums import ServerStatus, TaskKind, TaskStatus
from gamehost_shared.schemas import CamelModel
from pydantic import Field


class ServerCreate(CamelModel):
    name: str
    template_id: UUID
    env_overrides: dict[str, object] = Field(default_factory=dict)
    resources: dict[str, object] = Field(default_factory=dict)


class ServerUpdate(CamelModel):
    env_overrides: dict[str, object] | None = None
    resources: dict[str, object] | None = None


class ServerResponse(CamelModel):
    id: UUID
    owner_id: UUID
    name: str
    template_id: UUID
    node_id: UUID | None
    container_id: str | None
    status: ServerStatus
    host: str | None
    port: int | None
    env_overrides: dict[str, object]
    resources: dict[str, object]


class TaskAcceptedResponse(CamelModel):
    task_id: UUID
    server_id: UUID | None
    status: TaskStatus


class TaskResponse(CamelModel):
    id: UUID
    server_id: UUID | None
    kind: TaskKind
    status: TaskStatus
    payload: dict[str, object]
    error: str | None
