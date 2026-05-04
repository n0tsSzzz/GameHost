from typing import ClassVar

from arq.connections import RedisSettings
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAMEHOST_", env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"


async def health_check(_ctx: dict[str, object]) -> str:
    return "ok"


class WorkerSettings:
    functions: ClassVar[list[object]] = [health_check]
    redis_settings = RedisSettings.from_dsn(Settings().redis_url)
