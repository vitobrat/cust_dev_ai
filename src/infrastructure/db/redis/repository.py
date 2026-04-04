"""Base Redis repository with low-level list operations."""

from __future__ import annotations

from redis.asyncio import Redis

from src.configs.log.logger import get_logger
from src.infrastructure.db.redis.client import RedisClient


class BaseRedisRepository:
    """Base repository providing low-level Redis list operations.

    Subclass this to build domain-specific queue repositories.

    Attributes:
        _redis: Async Redis client instance.
        _logger: Logger scoped to the concrete subclass name.
    """

    def __init__(self, redis_client: RedisClient) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._redis_client: RedisClient = redis_client
        self._redis: Redis[str] = self._redis_client.client

    @property
    def redis_client(self) -> RedisClient:
        """Return the underlying ``RedisClient`` instance."""
        return self._redis_client

    async def delete(self, redis_key: str) -> None:
        """Delete a key. No-op if the key does not exist."""
        await self._redis.delete(redis_key)

    async def exists(self, redis_key: str) -> bool:
        """Return ``True`` if *redis_key* exists in Redis."""
        return bool(await self._redis.exists(redis_key))

    async def _lpush(self, redis_key: str, redis_value: str) -> int:
        """``LPUSH`` — insert *redis_value* at the head of the list.

        Returns:
            Length of the list after the push.
        """
        return await self._redis.lpush(redis_key, redis_value)

    async def _brpop(
        self,
        redis_key: str,
        timeout: int = 0,
    ) -> tuple[str, str] | None:
        """``BRPOP`` — blocking pop from the tail of the list.

        Waits up to *timeout* seconds for an element to appear.
        ``timeout=0`` means block indefinitely.

        Returns:
            A ``(key, value)`` tuple, or ``None`` if the timeout
            elapsed with no element available.
        """
        return await self._redis.brpop(redis_key, timeout=timeout)

    async def _llen(self, redis_key: str) -> int:
        """``LLEN`` — return the number of elements in the list."""
        return await self._redis.llen(redis_key)
