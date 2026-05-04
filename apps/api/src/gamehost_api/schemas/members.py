from datetime import datetime
from uuid import UUID

from gamehost_shared.enums import ServerMemberRole
from gamehost_shared.schemas import CamelModel


class MemberInviteRequest(CamelModel):
    email: str
    role: ServerMemberRole


class MemberResponse(CamelModel):
    server_id: UUID
    user_id: UUID
    role: ServerMemberRole
    invited_by: UUID
    created_at: datetime


class InviteResponse(CamelModel):
    id: UUID
    server_id: UUID
    email: str
    role: ServerMemberRole
    token: str
    accepted_at: datetime | None
