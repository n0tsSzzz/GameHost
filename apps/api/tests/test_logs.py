from collections.abc import AsyncIterator

from fastapi import FastAPI
from gamehost_api.clients.logs import get_logs_client
from gamehost_api.core.security import hash_password
from gamehost_api.db.models import GameTemplate, Server, User
from gamehost_shared.enums import ServerStatus
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class FakeLogsClient:
    async def tail(self, container_id: str, limit: int) -> list[str]:
        return [f"{container_id}: line 1", f"tail={limit}"]

    async def stream(self, container_id: str) -> AsyncIterator[str]:
        yield f"{container_id}: line 1"


async def test_server_logs_tail_requires_server_access(
    app: FastAPI,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    app.dependency_overrides[get_logs_client] = lambda: FakeLogsClient()
    async with session_factory() as session:
        user = User(
            email="player@example.com",
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
        session.add_all([user, template])
        await session.flush()
        server = Server(
            owner_id=user.id,
            name="Friday Minecraft",
            template_id=template.id,
            container_id="container-123",
            status=ServerStatus.RUNNING,
        )
        session.add(server)
        await session.commit()
        server_id = server.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
        )
        access = login_response.json()["access"]
        logs_response = await client.get(
            f"/api/v1/servers/{server_id}/logs?tail=25",
            headers={"Authorization": f"Bearer {access}"},
        )

    assert logs_response.status_code == 200
    assert logs_response.json() == {"lines": ["container-123: line 1", "tail=25"]}
