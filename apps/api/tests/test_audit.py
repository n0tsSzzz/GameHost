from gamehost_api.core.security import hash_password
from gamehost_api.db.models import AuditLog, User
from gamehost_shared.enums import UserRole
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def test_admin_can_filter_audit_logs(
    api_client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        admin = User(
            email="admin@example.com",
            password_hash=hash_password("correct-horse-battery-staple"),
            role=UserRole.ADMIN,
        )
        session.add(admin)
        await session.flush()
        session.add(
            AuditLog(
                actor_id=admin.id,
                action="server.create",
                target_type="server",
                target_id="server-1",
                meta={"taskId": "task-1"},
            )
        )
        await session.commit()

    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-horse-battery-staple"},
    )
    access = login_response.json()["access"]
    response = await api_client.get(
        "/api/v1/audit?targetType=server&targetId=server-1",
        headers={"Authorization": f"Bearer {access}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["action"] == "server.create"
