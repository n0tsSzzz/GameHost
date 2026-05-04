from uuid import UUID

from gamehost_api.clients.node_agent import NodeAgentClientProtocol
from gamehost_api.db.models import GameTemplate, Node, Server, Task
from gamehost_api.domain.lifecycle import run_task
from gamehost_shared.enums import NodeStatus, ServerStatus, TaskKind, TaskStatus
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class FakeNodeAgentClient(NodeAgentClientProtocol):
    async def provision_server(self, node: Node, server: Server) -> tuple[str, str, int]:
        return "container-123", "node-a.internal", 25565

    async def run_lifecycle(self, node: Node, server: Server, kind: TaskKind) -> None:
        return None


async def _access_token(api_client: AsyncClient) -> str:
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )
    return str(response.json()["access"])


async def _seed_template_and_node(session_factory: async_sessionmaker[AsyncSession]) -> UUID:
    async with session_factory() as session:
        template = GameTemplate(
            slug="minecraft-vanilla",
            display_name="Minecraft Vanilla",
            docker_image="itzg/minecraft-server:latest",
            default_env={"EULA": "TRUE"},
            default_ports=[{"containerPort": 25565, "protocol": "tcp"}],
            default_volumes=[],
            min_resources={"cpu": 1, "memMb": 2048},
            is_public=True,
        )
        session.add(template)
        session.add(
            Node(
                name="node-a",
                endpoint_url="http://node-a.internal:8010",
                api_key_hash="hash",
                capacity_cpu=8,
                capacity_mem_mb=32768,
                status=NodeStatus.ONLINE,
            )
        )
        await session.commit()
        return template.id


async def test_create_server_and_worker_marks_it_running(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    template_id = await _seed_template_and_node(session_factory)
    access = await _access_token(api_client)

    create_response = await api_client.post(
        "/api/v1/servers",
        headers={"Authorization": f"Bearer {access}"},
        json={"name": "Friday Minecraft", "templateId": str(template_id)},
    )

    assert create_response.status_code == 202
    task_id = UUID(create_response.json()["taskId"])
    server_id = UUID(create_response.json()["serverId"])

    async with session_factory() as session:
        task = await run_task(session, task_id, FakeNodeAgentClient())

    assert task.status == TaskStatus.SUCCEEDED

    async with session_factory() as session:
        server = await session.get(Server, server_id)
        assert server is not None
        assert server.status == ServerStatus.RUNNING
        assert server.container_id == "container-123"
        result = await session.execute(select(Task).where(Task.id == task_id))
        assert result.scalar_one().status == TaskStatus.SUCCEEDED
