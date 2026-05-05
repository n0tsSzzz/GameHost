from uuid import UUID

from gamehost_api.clients.node_agent import NodeAgentClientProtocol
from gamehost_api.core.security import hash_password
from gamehost_api.db.models import Backup, GameTemplate, Node, Server, User
from gamehost_api.domain.lifecycle import run_task
from gamehost_shared.enums import BackupStatus, ServerStatus, TaskKind
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class FakeNodeAgentClient(NodeAgentClientProtocol):
    async def provision_server(self, node: Node, server: Server) -> tuple[str, str, int]:
        return "container-123", "node-a.internal", 25565

    async def run_lifecycle(self, node: Node, server: Server, kind: TaskKind) -> None:
        return None

    async def tail_logs(self, node: Node, container_id: str, tail: int) -> list[str]:
        return []


async def _seed_server(session_factory: async_sessionmaker[AsyncSession]) -> UUID:
    async with session_factory() as session:
        owner = User(
            email="owner@example.com",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        template = GameTemplate(
            slug="minecraft-vanilla",
            display_name="Minecraft Vanilla",
            docker_image="itzg/minecraft-server:latest",
            default_env={},
            default_ports=[],
            default_volumes=[],
            min_resources={},
            is_public=True,
        )
        session.add_all([owner, template])
        await session.flush()
        server = Server(
            owner_id=owner.id,
            name="Friday Minecraft",
            template_id=template.id,
            container_id="container-123",
            status=ServerStatus.RUNNING,
        )
        session.add(server)
        await session.commit()
        return server.id


async def test_backup_create_list_restore_and_worker_completion(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    server_id = await _seed_server(session_factory)
    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com", "password": "correct-horse-battery-staple"},
    )
    access = login_response.json()["access"]

    backup_response = await api_client.post(
        f"/api/v1/servers/{server_id}/backups",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert backup_response.status_code == 202
    backup_task_id = UUID(backup_response.json()["taskId"])

    async with session_factory() as session:
        task = await run_task(session, backup_task_id, FakeNodeAgentClient())
        backup = await session.get(Backup, UUID(str(task.payload["backupId"])))

    assert backup is not None
    assert backup.status == BackupStatus.SUCCEEDED

    list_response = await api_client.get(
        f"/api/v1/servers/{server_id}/backups",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert list_response.status_code == 200
    backup_id = list_response.json()[0]["id"]

    restore_response = await api_client.post(
        f"/api/v1/backups/{backup_id}/restore",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert restore_response.status_code == 202
