from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from gamehost_api.api.v1 import servers
from gamehost_api.db.base import Base, get_session
from gamehost_api.main import create_app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

SessionFactory = async_sessionmaker[AsyncSession]


@pytest.fixture
async def test_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(test_engine: AsyncEngine) -> SessionFactory:
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch, session_factory: SessionFactory) -> FastAPI:
    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def enqueue_noop(_settings: object, _task_id: object) -> None:
        return None

    monkeypatch.setattr(servers, "enqueue_lifecycle_job", enqueue_noop)

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    return app


@pytest.fixture
async def api_client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as client:
        yield client
