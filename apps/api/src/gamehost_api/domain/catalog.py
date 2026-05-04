from secrets import token_urlsafe
from uuid import UUID

from gamehost_api.core.security import hash_refresh_token
from gamehost_api.db.models import GameTemplate, Node
from gamehost_api.schemas.nodes import NodeCreate, NodeUpdate
from gamehost_api.schemas.templates import TemplateCreate, TemplateUpdate
from gamehost_shared.enums import NodeStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CatalogError(Exception):
    pass


class TemplateNotFound(CatalogError):
    pass


class NodeNotFound(CatalogError):
    pass


async def list_templates(session: AsyncSession, include_private: bool) -> list[GameTemplate]:
    statement = select(GameTemplate).order_by(GameTemplate.display_name)
    if not include_private:
        statement = statement.where(GameTemplate.is_public.is_(True))
    result = await session.execute(statement)
    return list(result.scalars())


async def create_template(session: AsyncSession, payload: TemplateCreate) -> GameTemplate:
    template = GameTemplate(**payload.model_dump())
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def update_template(
    session: AsyncSession,
    template_id: UUID,
    payload: TemplateUpdate,
) -> GameTemplate:
    template = await session.get(GameTemplate, template_id)
    if template is None:
        raise TemplateNotFound
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await session.commit()
    await session.refresh(template)
    return template


async def list_nodes(session: AsyncSession) -> list[Node]:
    result = await session.execute(select(Node).order_by(Node.name))
    return list(result.scalars())


async def create_node(session: AsyncSession, payload: NodeCreate) -> tuple[Node, str]:
    api_key = token_urlsafe(40)
    node = Node(
        **payload.model_dump(),
        api_key_hash=hash_refresh_token(api_key),
        status=NodeStatus.OFFLINE,
    )
    session.add(node)
    await session.commit()
    await session.refresh(node)
    return node, api_key


async def update_node(session: AsyncSession, node_id: UUID, payload: NodeUpdate) -> Node:
    node = await session.get(Node, node_id)
    if node is None:
        raise NodeNotFound
    node.status = payload.status
    await session.commit()
    await session.refresh(node)
    return node


async def delete_node(session: AsyncSession, node_id: UUID) -> None:
    node = await session.get(Node, node_id)
    if node is None:
        raise NodeNotFound
    await session.delete(node)
    await session.commit()
