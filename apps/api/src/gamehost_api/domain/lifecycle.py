from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from gamehost_api.clients.node_agent import NodeAgentClientProtocol
from gamehost_api.core.metrics import ARQ_JOBS_FAILED, TASK_DURATION
from gamehost_api.db.models import (
    AuditLog,
    Backup,
    GameTemplate,
    Node,
    Server,
    ServerMember,
    Task,
    User,
)
from gamehost_api.domain.members import has_operator_access
from gamehost_api.schemas.servers import ServerCreate, ServerUpdate
from gamehost_shared.enums import (
    BackupStatus,
    NodeStatus,
    ServerStatus,
    TaskKind,
    TaskStatus,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class LifecycleError(Exception):
    pass


class ServerNotFound(LifecycleError):
    pass


class TemplateNotFound(LifecycleError):
    pass


class NodeUnavailable(LifecycleError):
    pass


class InvalidServerState(LifecycleError):
    pass


async def list_accessible_servers(session: AsyncSession, user: User) -> list[Server]:
    member_server_ids = select(ServerMember.server_id).where(ServerMember.user_id == user.id)
    result = await session.execute(
        select(Server)
        .where((Server.owner_id == user.id) | (Server.id.in_(member_server_ids)))
        .order_by(Server.created_at.desc()),
    )
    return list(result.scalars())


async def get_accessible_server(session: AsyncSession, user: User, server_id: UUID) -> Server:
    result = await session.execute(
        select(Server)
        .outerjoin(ServerMember, ServerMember.server_id == Server.id)
        .where(
            Server.id == server_id,
            (Server.owner_id == user.id) | (ServerMember.user_id == user.id),
        )
    )
    server = result.scalar_one_or_none()
    if server is None:
        raise ServerNotFound
    return server


async def create_server(
    session: AsyncSession,
    owner: User,
    payload: ServerCreate,
    ip: str | None,
) -> tuple[Server, Task]:
    template = await session.get(GameTemplate, payload.template_id)
    if template is None:
        raise TemplateNotFound
    server = Server(
        owner_id=owner.id,
        name=payload.name,
        template_id=payload.template_id,
        status=ServerStatus.PENDING,
        env_overrides=payload.env_overrides,
        resources=payload.resources,
    )
    session.add(server)
    await session.flush()
    task = _task(server.id, TaskKind.PROVISION_SERVER, {"serverId": str(server.id)})
    session.add(task)
    await session.flush()
    _audit(session, owner.id, "server.create", "server", server.id, {"taskId": str(task.id)}, ip)
    await session.commit()
    await session.refresh(server)
    await session.refresh(task)
    return server, task


async def update_server_config(
    session: AsyncSession,
    user: User,
    server_id: UUID,
    payload: ServerUpdate,
    ip: str | None,
) -> Server:
    server = await get_accessible_server(session, user, server_id)
    if not await has_operator_access(session, user, server):
        raise InvalidServerState
    if server.status != ServerStatus.STOPPED:
        raise InvalidServerState
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(server, field, value)
    _audit(session, user.id, "server.update", "server", server.id, updates, ip)
    await session.commit()
    await session.refresh(server)
    return server


async def enqueue_lifecycle_task(
    session: AsyncSession,
    user: User,
    server_id: UUID,
    kind: TaskKind,
    ip: str | None,
) -> Task:
    server = await get_accessible_server(session, user, server_id)
    if not await has_operator_access(session, user, server):
        raise InvalidServerState
    _validate_transition(server, kind)
    if kind == TaskKind.DELETE_SERVER:
        server.status = ServerStatus.DELETING
    task = _task(server.id, kind, {"serverId": str(server.id)})
    session.add(task)
    await session.flush()
    _audit(
        session,
        user.id,
        f"server.{kind.value}",
        "server",
        server.id,
        {"taskId": str(task.id)},
        ip,
    )
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: UUID) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise ServerNotFound
    return task


async def run_task(
    session: AsyncSession,
    task_id: UUID,
    node_agent: NodeAgentClientProtocol,
) -> Task:
    started = perf_counter()
    task = await session.get(Task, task_id)
    if task is None:
        raise ServerNotFound
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now(UTC)
    await session.flush()
    try:
        if task.kind == TaskKind.PROVISION_SERVER:
            await _provision(session, task, node_agent)
        elif task.kind in {TaskKind.BACKUP_SERVER, TaskKind.RESTORE_BACKUP}:
            await _run_backup(session, task)
        else:
            await _run_lifecycle(session, task, node_agent)
        task.status = TaskStatus.SUCCEEDED
    except Exception as exc:
        ARQ_JOBS_FAILED.inc()
        task.status = TaskStatus.FAILED
        task.error = str(exc)
        server = await session.get(Server, task.server_id) if task.server_id else None
        if server is not None and task.kind == TaskKind.PROVISION_SERVER:
            server.status = ServerStatus.FAILED
    finally:
        task.finished_at = datetime.now(UTC)
        TASK_DURATION.labels(kind=task.kind.value).observe(perf_counter() - started)
        await session.commit()
        await session.refresh(task)
    return task


async def _provision(
    session: AsyncSession,
    task: Task,
    node_agent: NodeAgentClientProtocol,
) -> None:
    if task.server_id is None:
        raise ServerNotFound
    server = await session.get(Server, task.server_id)
    if server is None:
        raise ServerNotFound
    node = await _select_node(session)
    server.status = ServerStatus.PROVISIONING
    server.node_id = node.id
    await session.flush()
    await server.awaitable_attrs.template
    container_id, host, port = await node_agent.provision_server(node, server)
    server.container_id = container_id
    server.host = host
    server.port = port
    server.status = ServerStatus.RUNNING


async def _run_lifecycle(
    session: AsyncSession,
    task: Task,
    node_agent: NodeAgentClientProtocol,
) -> None:
    if task.server_id is None:
        raise ServerNotFound
    server = await session.get(Server, task.server_id)
    if server is None or server.node_id is None:
        raise ServerNotFound
    node = await session.get(Node, server.node_id)
    if node is None:
        raise NodeUnavailable
    await node_agent.run_lifecycle(node, server, task.kind)
    server.status = {
        TaskKind.START_SERVER: ServerStatus.RUNNING,
        TaskKind.STOP_SERVER: ServerStatus.STOPPED,
        TaskKind.RESTART_SERVER: ServerStatus.RUNNING,
        TaskKind.DELETE_SERVER: ServerStatus.DELETING,
    }[task.kind]


async def _run_backup(session: AsyncSession, task: Task) -> None:
    backup_id = task.payload.get("backupId")
    if not isinstance(backup_id, str):
        raise ValueError("Missing backup id")
    backup = await session.get(Backup, UUID(backup_id))
    if backup is None:
        raise ValueError("Backup not found")
    backup.status = BackupStatus.RUNNING
    await session.flush()
    backup.status = BackupStatus.SUCCEEDED


async def _select_node(session: AsyncSession) -> Node:
    usage = (
        select(Server.node_id, func.count(Server.id).label("server_count"))
        .where(Server.node_id.is_not(None), Server.status != ServerStatus.DELETING)
        .group_by(Server.node_id)
        .subquery()
    )
    result = await session.execute(
        select(Node)
        .outerjoin(usage, usage.c.node_id == Node.id)
        .where(Node.status == NodeStatus.ONLINE)
        .order_by(func.coalesce(usage.c.server_count, 0), Node.name)
        .limit(1)
    )
    node = result.scalar_one_or_none()
    if node is None:
        raise NodeUnavailable
    return node


def _validate_transition(server: Server, kind: TaskKind) -> None:
    allowed = {
        TaskKind.START_SERVER: {ServerStatus.STOPPED, ServerStatus.FAILED},
        TaskKind.STOP_SERVER: {ServerStatus.RUNNING},
        TaskKind.RESTART_SERVER: {ServerStatus.RUNNING},
        TaskKind.DELETE_SERVER: {
            ServerStatus.PENDING,
            ServerStatus.RUNNING,
            ServerStatus.STOPPED,
            ServerStatus.FAILED,
        },
    }
    if kind in allowed and server.status not in allowed[kind]:
        raise InvalidServerState


def _task(server_id: UUID | None, kind: TaskKind, payload: dict[str, object]) -> Task:
    return Task(server_id=server_id, kind=kind, status=TaskStatus.QUEUED, payload=payload)


def _audit(
    session: AsyncSession,
    actor_id: UUID | None,
    action: str,
    target_type: str,
    target_id: UUID,
    meta: dict[str, object],
    ip: str | None,
) -> None:
    session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            meta=meta,
            ip=ip,
        )
    )
