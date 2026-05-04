from redis.asyncio import Redis

from gamehost_node.config import Settings, get_settings


class LogPublisher:
    def __init__(self, settings: Settings) -> None:
        self._redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def publish(self, container_id: str, line: str, tail_limit: int = 500) -> None:
        list_key = f"logs:tail:{container_id}"
        await self._redis.rpush(list_key, line)
        await self._redis.ltrim(list_key, -tail_limit, -1)
        await self._redis.publish(f"logs:{container_id}", line)


def get_log_publisher() -> LogPublisher:
    return LogPublisher(get_settings())
