from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from gamehost_shared.enums import UserRole
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.deps import AdminUser, CurrentUser
from gamehost_api.db.base import get_session
from gamehost_api.db.models import GameTemplate
from gamehost_api.domain.catalog import (
    TemplateNotFound,
    create_template,
    list_templates,
    update_template,
)
from gamehost_api.schemas.templates import TemplateCreate, TemplateResponse, TemplateUpdate

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateResponse])
async def get_templates(session: SessionDep, user: CurrentUser) -> list[GameTemplate]:
    include_private = user.role == UserRole.ADMIN
    return await list_templates(session, include_private=include_private)


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def post_template(
    payload: TemplateCreate,
    session: SessionDep,
    _admin: AdminUser,
) -> object:
    return await create_template(session, payload)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def patch_template(
    template_id: UUID,
    payload: TemplateUpdate,
    session: SessionDep,
    _admin: AdminUser,
) -> object:
    try:
        return await update_template(session, template_id, payload)
    except TemplateNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        ) from exc
