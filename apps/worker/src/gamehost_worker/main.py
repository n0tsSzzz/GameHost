from typing import ClassVar
from uuid import UUID

from arq.connections import RedisSettings
from gamehost_api.clients.node_agent import NodeAgentClient
from gamehost_api.core.config import get_settings
from gamehost_api.db.base import AsyncSessionFactory
from gamehost_api.domain.lifecycle import ServerNotFound, run_task
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAMEHOST_", env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"


async def health_check(_ctx: dict[str, object]) -> str:
    return "ok"


async def run_lifecycle_task(_ctx: dict[str, object], task_id: str) -> str:
    async with AsyncSessionFactory() as session:
        try:
            await run_task(session, UUID(task_id), NodeAgentClient(get_settings()))
        except ServerNotFound:
            return f"{task_id}: missing"
    return task_id


class WorkerSettings:
    functions: ClassVar[list[object]] = [health_check, run_lifecycle_task]
    redis_settings = RedisSettings.from_dsn(Settings().redis_url)
