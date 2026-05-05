from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings

from gamehost_api.core.config import Settings


async def enqueue_lifecycle_job(settings: Settings, task_id: UUID) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await redis.enqueue_job("run_lifecycle_task", str(task_id))
    finally:
        await redis.aclose()
