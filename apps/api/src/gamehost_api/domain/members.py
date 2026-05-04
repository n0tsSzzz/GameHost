from datetime import UTC, datetime
from secrets import token_urlsafe
from uuid import UUID

from gamehost_api.db.models import Server, ServerInvite, ServerMember, User
from gamehost_api.schemas.members import MemberInviteRequest
from gamehost_shared.enums import ServerMemberRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class MemberError(Exception):
    pass


class ServerNotFound(MemberError):
    pass


class Forbidden(MemberError):
    pass


class InviteNotFound(MemberError):
    pass


async def list_members(session: AsyncSession, actor: User, server_id: UUID) -> list[ServerMember]:
    server = await _require_owner(session, actor, server_id)
    result = await session.execute(
        select(ServerMember)
        .where(ServerMember.server_id == server.id)
        .order_by(ServerMember.created_at)
    )
    return list(result.scalars())


async def invite_member(
    session: AsyncSession,
    actor: User,
    server_id: UUID,
    payload: MemberInviteRequest,
) -> ServerMember | ServerInvite:
    server = await _require_owner(session, actor, server_id)
    email = payload.email.lower()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is not None:
        member = ServerMember(
            server_id=server.id,
            user_id=user.id,
            role=payload.role,
            invited_by=actor.id,
        )
        merged = await session.merge(member)
        await session.commit()
        await session.refresh(merged)
        return merged
    invite = ServerInvite(
        server_id=server.id,
        email=email,
        role=payload.role,
        token=token_urlsafe(32),
        invited_by=actor.id,
    )
    session.add(invite)
    await session.commit()
    await session.refresh(invite)
    return invite


async def remove_member(session: AsyncSession, actor: User, server_id: UUID, user_id: UUID) -> None:
    server = await _require_owner(session, actor, server_id)
    member = await session.get(ServerMember, {"server_id": server.id, "user_id": user_id})
    if member is not None:
        await session.delete(member)
        await session.commit()


async def accept_invite(session: AsyncSession, actor: User, token: str) -> ServerMember:
    result = await session.execute(
        select(ServerInvite).where(ServerInvite.token == token, ServerInvite.accepted_at.is_(None))
    )
    invite = result.scalar_one_or_none()
    if invite is None:
        raise InviteNotFound
    if invite.email != actor.email:
        raise Forbidden
    member = ServerMember(
        server_id=invite.server_id,
        user_id=actor.id,
        role=invite.role,
        invited_by=invite.invited_by,
    )
    merged = await session.merge(member)
    invite.accepted_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(merged)
    return merged


async def has_operator_access(session: AsyncSession, actor: User, server: Server) -> bool:
    if server.owner_id == actor.id:
        return True
    member = await session.get(ServerMember, {"server_id": server.id, "user_id": actor.id})
    return member is not None and member.role == ServerMemberRole.OPERATOR


async def _require_owner(session: AsyncSession, actor: User, server_id: UUID) -> Server:
    server = await session.get(Server, server_id)
    if server is None:
        raise ServerNotFound
    if server.owner_id != actor.id:
        raise Forbidden
    return server
