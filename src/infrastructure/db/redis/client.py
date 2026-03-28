"""Redis client with async connection pooling."""

from __future__ import annotations

from redis import asyncio as redis


class RedisClient:
    """Async Redis client with built-in connection pooling.

    Wraps ``redis.asyncio.Redis`` and manages the connection pool lifecycle.
    A single instance should be shared across the application via DI.

    Attributes:
        _client: Underlying async Redis client with connection pool.
    """

    def __init__(
        self,
        redis_url: str,
        max_connections: int = 10,
        decode_responses: bool = True,
    ) -> None:
        """Initialize Redis client with connection pool.

        Args:
            redis_url: Redis connection URL (e.g., ``redis://:password@host:6379/0``).
            max_connections: Maximum number of connections in the pool. Defaults to 10.
            decode_responses: If True, decode byte responses to strings. Defaults to True.
        """
        self._client: redis.Redis[str] = redis.from_url(
            url=redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
        )

    @property
    def client(self) -> redis.Redis[str]:
        """Return the underlying async Redis instance."""
        return self._client

    async def ping(self) -> bool:
        """Check if Redis server is reachable.

        Returns:
            True if server responds to PING.

        Raises:
            redis.ConnectionError: If connection to Redis fails.
        """
        return await self._client.ping()

    async def close(self) -> None:
        """Close all connections in the pool.

        Should be called during application shutdown to ensure graceful cleanup.
        """
        await self._client.aclose()  # type: ignore[attr-defined]
