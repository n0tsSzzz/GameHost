from uuid import UUID

from gamehost_api.db.models import Backup, Server, Task, User
from gamehost_api.domain.lifecycle import ServerNotFound, get_accessible_server
from gamehost_api.domain.members import has_operator_access
from gamehost_shared.enums import BackupStatus, TaskKind, TaskStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BackupNotFound(Exception):
    pass


class BackupForbidden(Exception):
    pass


async def list_backups(session: AsyncSession, user: User, server_id: UUID) -> list[Backup]:
    server = await get_accessible_server(session, user, server_id)
    result = await session.execute(
        select(Backup).where(Backup.server_id == server.id).order_by(Backup.created_at.desc())
    )
    return list(result.scalars())


async def create_backup_task(
    session: AsyncSession,
    user: User,
    server_id: UUID,
) -> tuple[Backup, Task]:
    server = await get_accessible_server(session, user, server_id)
    if not await has_operator_access(session, user, server):
        raise BackupForbidden
    backup = Backup(
        server_id=server.id,
        s3_key=f"servers/{server.id}/backups/pending",
        created_by=user.id,
        status=BackupStatus.PENDING,
    )
    session.add(backup)
    await session.flush()
    backup.s3_key = f"servers/{server.id}/backups/{backup.id}.tar"
    task = Task(
        server_id=server.id,
        kind=TaskKind.BACKUP_SERVER,
        status=TaskStatus.QUEUED,
        payload={"serverId": str(server.id), "backupId": str(backup.id)},
    )
    session.add(task)
    await session.commit()
    await session.refresh(backup)
    await session.refresh(task)
    return backup, task


async def restore_backup_task(session: AsyncSession, user: User, backup_id: UUID) -> Task:
    backup = await session.get(Backup, backup_id)
    if backup is None:
        raise BackupNotFound
    server = await session.get(Server, backup.server_id)
    if server is None:
        raise ServerNotFound
    if not await has_operator_access(session, user, server):
        raise BackupForbidden
    task = Task(
        server_id=server.id,
        kind=TaskKind.RESTORE_BACKUP,
        status=TaskStatus.QUEUED,
        payload={"serverId": str(server.id), "backupId": str(backup.id)},
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task
