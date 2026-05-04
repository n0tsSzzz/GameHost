from uuid import UUID

from gamehost_api.core.security import hash_password
from gamehost_api.db.models import GameTemplate, Server, User
from gamehost_shared.enums import ServerStatus
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def _seed_server(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, UUID, UUID]:
    async with session_factory() as session:
        owner = User(
            email="owner@example.com",
            password_hash=hash_password("correct-horse-battery-staple"),
        )
        operator = User(
            email="operator@example.com",
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
        session.add_all([owner, operator, template])
        await session.flush()
        server = Server(
            owner_id=owner.id,
            name="Friday Minecraft",
            template_id=template.id,
            container_id="container-123",
            status=ServerStatus.STOPPED,
        )
        session.add(server)
        await session.commit()
        return server.id, owner.id, operator.id


async def _login(api_client: AsyncClient, email: str) -> str:
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    return str(response.json()["access"])


async def test_owner_invites_existing_operator_and_operator_can_start(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    server_id, _owner_id, operator_id = await _seed_server(session_factory)
    owner_access = await _login(api_client, "owner@example.com")

    invite_response = await api_client.post(
        f"/api/v1/servers/{server_id}/members",
        headers={"Authorization": f"Bearer {owner_access}"},
        json={"email": "operator@example.com", "role": "operator"},
    )
    assert invite_response.status_code == 200
    assert invite_response.json()["userId"] == str(operator_id)

    operator_access = await _login(api_client, "operator@example.com")
    start_response = await api_client.post(
        f"/api/v1/servers/{server_id}/start",
        headers={"Authorization": f"Bearer {operator_access}"},
    )
    assert start_response.status_code == 202


async def test_invite_token_accepts_unknown_user_after_registration(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    server_id, _owner_id, _operator_id = await _seed_server(session_factory)
    owner_access = await _login(api_client, "owner@example.com")

    invite_response = await api_client.post(
        f"/api/v1/servers/{server_id}/members",
        headers={"Authorization": f"Bearer {owner_access}"},
        json={"email": "friend@example.com", "role": "viewer"},
    )
    token = invite_response.json()["token"]

    await api_client.post(
        "/api/v1/auth/register",
        json={"email": "friend@example.com", "password": "correct-horse-battery-staple"},
    )
    friend_access = await _login(api_client, "friend@example.com")
    accept_response = await api_client.post(
        f"/api/v1/invites/{token}/accept",
        headers={"Authorization": f"Bearer {friend_access}"},
    )

    assert accept_response.status_code == 200
    assert accept_response.json()["role"] == "viewer"
