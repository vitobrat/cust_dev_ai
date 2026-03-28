"""Base Redis repository with common key-value operations."""

from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from src.configs.log.logger import get_logger
from src.infrastructure.db.redis.client import RedisClient
from src.infrastructure.exceptions import RedisRepositoryError


class BaseRedisRepository:
    """Base repository providing common Redis key-value operations.

    Subclass this to build domain-specific Redis repositories.
    JSON methods wrap low-level ``_get`` / ``_set`` with serialization.

    Attributes:
        _redis: Async Redis client instance.
        _logger: Logger scoped to the concrete subclass name.
    """

    def __init__(self, redis_client: RedisClient) -> None:
        """Initialize repository with a Redis client.

        Args:
            redis_client: RedisClient instance providing the connection pool.
        """
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._redis: Redis[str] = redis_client.client

    async def get_json(self, redis_key: str) -> dict[str, Any] | None:
        """Read a key and deserialize its value from JSON.

        Args:
            redis_key: Redis key to look up.

        Returns:
            Parsed dict, or None if the key does not exist.

        Raises:
            RedisRepositoryError: If the stored value is not valid JSON.
        """
        raw_value = await self._get(redis_key)

        if raw_value is None:
            return None

        try:
            return json.loads(raw_value)
        except (json.JSONDecodeError, TypeError) as exc:
            self._logger.error("Invalid JSON in Redis key: %s", redis_key)
            raise RedisRepositoryError(f"Invalid JSON for key '{redis_key}'") from exc

    async def set_json(
        self,
        redis_key: str,
        payload: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Serialize a dict to JSON and store it under the given key.

        Args:
            redis_key: Redis key.
            payload: Dict to serialize and store.
            ttl: Time to live in seconds. None means no expiration.

        Raises:
            RedisRepositoryError: If the payload cannot be serialized to JSON.
        """
        try:
            serialized = json.dumps(payload)
        except (TypeError, ValueError) as exc:
            self._logger.error("Failed to serialize payload for Redis key: %s", redis_key)
            raise RedisRepositoryError(f"Cannot serialize payload for key '{redis_key}'") from exc

        await self._set(redis_key, serialized, ttl)

    async def delete(self, redis_key: str) -> None:
        """Delete a key.

        Args:
            redis_key: Redis key to delete. No-op if key does not exist.
        """
        await self._redis.delete(redis_key)

    async def exists(self, redis_key: str) -> bool:
        """Check if a key exists.

        Args:
            redis_key: Redis key to check.

        Returns:
            True if the key exists in Redis.
        """
        return bool(await self._redis.exists(redis_key))

    async def _get(self, redis_key: str) -> str | None:
        """Get raw string value by key.

        Args:
            redis_key: Redis key to look up.

        Returns:
            The stored string value, or None if key does not exist.
        """
        return await self._redis.get(redis_key)

    async def _set(
        self,
        redis_key: str,
        redis_value: str,
        ttl: int | None = None,
    ) -> None:
        """Set key-value pair with optional expiration.

        Args:
            redis_key: Redis key.
            redis_value: String value to store.
            ttl: Time to live in seconds. None means no expiration.
        """
        await self._redis.set(redis_key, redis_value, ex=ttl)
