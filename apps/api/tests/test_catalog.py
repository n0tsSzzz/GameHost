from gamehost_api.core.security import hash_password
from gamehost_api.db.models import User
from gamehost_shared.enums import UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def _admin_token(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> str:
    async with session_factory() as session:
        session.add(
            User(
                email="admin@example.com",
                password_hash=hash_password("correct-horse-battery-staple"),
                role=UserRole.ADMIN,
            ),
        )
        await session.commit()

    response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-horse-battery-staple"},
    )
    return str(response.json()["access"])


async def test_templates_are_admin_mutable_and_readable(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    admin_access = await _admin_token(api_client, session_factory)

    create_response = await api_client.post(
        "/api/v1/templates",
        headers={"Authorization": f"Bearer {admin_access}"},
        json={
            "slug": "minecraft-vanilla",
            "displayName": "Minecraft Vanilla",
            "dockerImage": "itzg/minecraft-server:latest",
            "defaultEnv": {"EULA": "TRUE"},
            "defaultPorts": [{"containerPort": 25565, "protocol": "tcp"}],
            "minResources": {"cpu": 1, "memMb": 2048},
            "isPublic": True,
        },
    )
    assert create_response.status_code == 201
    template_id = create_response.json()["id"]

    patch_response = await api_client.patch(
        f"/api/v1/templates/{template_id}",
        headers={"Authorization": f"Bearer {admin_access}"},
        json={"displayName": "Minecraft"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["displayName"] == "Minecraft"

    list_response = await api_client.get(
        "/api/v1/templates",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["slug"] == "minecraft-vanilla"


async def test_nodes_are_admin_only_and_return_api_key_once(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )
    user_login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "player@example.com", "password": "correct-horse-battery-staple"},
    )
    user_access = user_login.json()["access"]

    forbidden_response = await api_client.get(
        "/api/v1/nodes",
        headers={"Authorization": f"Bearer {user_access}"},
    )
    assert forbidden_response.status_code == 403

    admin_access = await _admin_token(api_client, session_factory)
    create_response = await api_client.post(
        "/api/v1/nodes",
        headers={"Authorization": f"Bearer {admin_access}"},
        json={
            "name": "node-a",
            "endpointUrl": "http://node-a.internal:8010",
            "capacityCpu": 8,
            "capacityMemMb": 32768,
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["apiKey"]
    node_id = create_response.json()["id"]

    list_response = await api_client.get(
        "/api/v1/nodes",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert list_response.status_code == 200
    assert "apiKey" not in list_response.json()[0]

    patch_response = await api_client.patch(
        f"/api/v1/nodes/{node_id}",
        headers={"Authorization": f"Bearer {admin_access}"},
        json={"status": "drain"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "drain"
