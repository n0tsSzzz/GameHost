from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from gamehost_api.core.deps import AdminUser
from gamehost_api.db.base import get_session
from gamehost_api.db.models import Node
from gamehost_api.domain.catalog import (
    NodeNotFound,
    create_node,
    delete_node,
    list_nodes,
    update_node,
)
from gamehost_api.schemas.nodes import NodeCreate, NodeCreateResponse, NodeResponse, NodeUpdate

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("", response_model=list[NodeResponse])
async def get_nodes(session: SessionDep, _admin: AdminUser) -> list[Node]:
    return await list_nodes(session)


@router.post("", response_model=NodeCreateResponse, status_code=status.HTTP_201_CREATED)
async def post_node(
    payload: NodeCreate,
    session: SessionDep,
    _admin: AdminUser,
) -> NodeCreateResponse:
    node, api_key = await create_node(session, payload)
    node_response = NodeResponse.model_validate(node, from_attributes=True)
    return NodeCreateResponse(**node_response.model_dump(), api_key=api_key)


@router.patch("/{node_id}", response_model=NodeResponse)
async def patch_node(
    node_id: UUID,
    payload: NodeUpdate,
    session: SessionDep,
    _admin: AdminUser,
) -> object:
    try:
        return await update_node(session, node_id, payload)
    except NodeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_node(node_id: UUID, session: SessionDep, _admin: AdminUser) -> Response:
    try:
        await delete_node(session, node_id)
    except NodeNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
