from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.deps import CurrentUser
from gamehost_api.db.base import get_session
from gamehost_api.db.models import ServerMember
from gamehost_api.domain.members import (
    Forbidden,
    InviteNotFound,
    ServerNotFound,
    accept_invite,
    invite_member,
    list_members,
    remove_member,
)
from gamehost_api.schemas.members import InviteResponse, MemberInviteRequest, MemberResponse

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(tags=["members"])


@router.get("/servers/{server_id}/members", response_model=list[MemberResponse])
async def get_members(
    server_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> list[ServerMember]:
    try:
        return await list_members(session, user, server_id)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
    except Forbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from exc


@router.post("/servers/{server_id}/members", response_model=MemberResponse | InviteResponse)
async def post_member(
    server_id: UUID,
    payload: MemberInviteRequest,
    session: SessionDep,
    user: CurrentUser,
) -> object:
    try:
        return await invite_member(session, user, server_id, payload)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
    except Forbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from exc


@router.delete("/servers/{server_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    server_id: UUID,
    user_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> Response:
    try:
        await remove_member(session, user, server_id, user_id)
    except ServerNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found",
        ) from exc
    except Forbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/invites/{token}/accept", response_model=MemberResponse)
async def accept_member_invite(token: str, session: SessionDep, user: CurrentUser) -> object:
    try:
        return await accept_invite(session, user, token)
    except InviteNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        ) from exc
    except Forbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") from exc
