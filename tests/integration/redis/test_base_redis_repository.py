"""Integration tests for BaseRedisRepository.

Tests cover all key-value operations with real Redis via testcontainers.
Each test runs against a clean database — flushdb is called after every test.
"""

import pytest

from src.infrastructure.db.redis.repository import BaseRedisRepository
from src.infrastructure.exceptions import RedisRepositoryError


class TestBaseRedisRepositorySet:
    """Tests for BaseRedisRepository._set()."""

    async def test_set_persists_value(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _set() stores a value retrievable by _get()."""
        # Arrange
        redis_key = "test:set:basic"
        expected_value = "hello_redis"

        # Act
        await redis_repository._set(redis_key, expected_value)
        stored_value = await redis_repository._get(redis_key)

        # Assert
        assert stored_value == expected_value

    async def test_set_with_ttl_persists_value(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _set() with TTL stores a value and the key exists."""
        # Arrange
        redis_key = "test:set:ttl"
        expected_value = "expiring_value"

        # Act
        await redis_repository._set(redis_key, expected_value, ttl=300)

        # Assert
        stored_value = await redis_repository._get(redis_key)
        assert stored_value == expected_value
        assert await redis_repository.exists(redis_key) is True

    async def test_set_overwrites_existing_value(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _set() overwrites a previously stored value."""
        # Arrange
        redis_key = "test:set:overwrite"
        await redis_repository._set(redis_key, "original")

        # Act
        await redis_repository._set(redis_key, "updated")
        stored_value = await redis_repository._get(redis_key)

        # Assert
        assert stored_value == "updated"


class TestBaseRedisRepositoryGet:
    """Tests for BaseRedisRepository._get()."""

    async def test_get_returns_none_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _get() returns None when the key does not exist."""
        # Act
        stored_value = await redis_repository._get("test:get:nonexistent")

        # Assert
        assert stored_value is None

    async def test_get_returns_stored_value(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _get() returns the exact value that was stored."""
        # Arrange
        redis_key = "test:get:existing"
        expected_value = "stored_data_123"
        await redis_repository._set(redis_key, expected_value)

        # Act
        stored_value = await redis_repository._get(redis_key)

        # Assert
        assert stored_value == expected_value


class TestBaseRedisRepositoryDelete:
    """Tests for BaseRedisRepository.delete()."""

    async def test_delete_removes_existing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that delete() removes a key from Redis."""
        # Arrange
        redis_key = "test:delete:existing"
        await redis_repository._set(redis_key, "to_be_deleted")

        # Act
        await redis_repository.delete(redis_key)

        # Assert
        assert await redis_repository.exists(redis_key) is False
        assert await redis_repository._get(redis_key) is None

    async def test_delete_does_not_raise_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that delete() is a no-op for a non-existent key."""
        # Act & Assert — should not raise
        await redis_repository.delete("test:delete:nonexistent")


class TestBaseRedisRepositoryExists:
    """Tests for BaseRedisRepository.exists()."""

    async def test_exists_returns_false_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that exists() returns False when the key is absent."""
        # Act & Assert
        assert await redis_repository.exists("test:exists:missing") is False

    async def test_exists_returns_true_for_present_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that exists() returns True when the key is present."""
        # Arrange
        redis_key = "test:exists:present"
        await redis_repository._set(redis_key, "some_value")

        # Act & Assert
        assert await redis_repository.exists(redis_key) is True


class TestBaseRedisRepositorySetJson:
    """Tests for BaseRedisRepository.set_json() and get_json()."""

    async def test_set_json_and_get_json_round_trip(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that set_json() stores a dict retrievable by get_json()."""
        # Arrange
        redis_key = "test:json:roundtrip"
        payload = {
            "name": "Alice",
            "age": 30,
            "tags": ["developer", "python"],
            "active": True,
        }

        # Act
        await redis_repository.set_json(redis_key, payload)
        restored = await redis_repository.get_json(redis_key)

        # Assert
        assert restored == payload

    async def test_set_json_with_ttl(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that set_json() with TTL stores a retrievable value."""
        # Arrange
        redis_key = "test:json:ttl"
        payload = {"status": "cached"}

        # Act
        await redis_repository.set_json(redis_key, payload, ttl=300)

        # Assert
        assert await redis_repository.exists(redis_key) is True
        assert await redis_repository.get_json(redis_key) == payload

    async def test_get_json_returns_none_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that get_json() returns None for a non-existent key."""
        # Act & Assert
        assert await redis_repository.get_json("test:json:missing") is None

    async def test_get_json_raises_on_invalid_json(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that get_json() raises RedisRepositoryError for malformed JSON."""
        # Arrange — write raw invalid JSON bypassing set_json
        redis_key = "test:json:invalid"
        await redis_repository._set(redis_key, "not-valid-json{{")

        # Act & Assert
        with pytest.raises(RedisRepositoryError, match="Invalid JSON"):
            await redis_repository.get_json(redis_key)

    async def test_set_json_raises_on_unserializable_payload(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that set_json() raises RedisRepositoryError for non-serializable data."""
        # Arrange
        unserializable = {"callback": lambda: None}

        # Act & Assert
        with pytest.raises(RedisRepositoryError, match="Cannot serialize"):
            await redis_repository.set_json("test:json:bad", unserializable)
