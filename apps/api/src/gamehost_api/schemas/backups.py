from datetime import datetime
from uuid import UUID

from gamehost_shared.enums import BackupStatus
from gamehost_shared.schemas import CamelModel


class BackupResponse(CamelModel):
    id: UUID
    server_id: UUID
    s3_key: str
    size_bytes: int
    created_by: UUID | None
    created_at: datetime
    status: BackupStatus
