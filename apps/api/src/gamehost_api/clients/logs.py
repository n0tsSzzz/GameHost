from collections.abc import AsyncIterator
from typing import Protocol

from redis.asyncio import Redis

from gamehost_api.core.config import Settings, get_settings


class LogsClientProtocol(Protocol):
    async def tail(self, container_id: str, limit: int) -> list[str]:
        raise NotImplementedError

    def stream(self, container_id: str) -> AsyncIterator[str]:
        raise NotImplementedError


class RedisLogsClient:
    def __init__(self, settings: Settings) -> None:
        self._redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def tail(self, container_id: str, limit: int) -> list[str]:
        values = await self._redis.lrange(_list_key(container_id), max(-limit, -1), -1)
        return [str(value) for value in values]

    async def stream(self, container_id: str) -> AsyncIterator[str]:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(_channel(container_id))
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield str(message["data"])
        finally:
            await pubsub.unsubscribe(_channel(container_id))
            await pubsub.aclose()


def get_logs_client() -> LogsClientProtocol:
    return RedisLogsClient(get_settings())


def _list_key(container_id: str) -> str:
    return f"logs:tail:{container_id}"


def _channel(container_id: str) -> str:
    return f"logs:{container_id}"
