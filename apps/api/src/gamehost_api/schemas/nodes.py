from datetime import datetime
from uuid import UUID

from gamehost_shared.enums import NodeStatus
from gamehost_shared.schemas import CamelModel


class NodeCreate(CamelModel):
    name: str
    endpoint_url: str
    public_host: str = "localhost"
    capacity_cpu: int
    capacity_mem_mb: int


class NodeUpdate(CamelModel):
    status: NodeStatus


class NodeResponse(CamelModel):
    id: UUID
    name: str
    endpoint_url: str
    public_host: str
    capacity_cpu: int
    capacity_mem_mb: int
    status: NodeStatus
    last_seen_at: datetime | None


class NodeCreateResponse(NodeResponse):
    api_key: str
