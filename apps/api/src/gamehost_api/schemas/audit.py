from datetime import datetime
from uuid import UUID

from gamehost_shared.schemas import CamelModel


class AuditLogResponse(CamelModel):
    id: UUID
    actor_id: UUID | None
    action: str
    target_type: str
    target_id: str
    meta: dict[str, object]
    ip: str | None
    created_at: datetime
