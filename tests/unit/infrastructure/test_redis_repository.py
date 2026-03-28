"""Unit tests for BaseRedisRepository key-value operations."""

from typing import Any

import pytest

from src.infrastructure.exceptions import RedisRepositoryError


async def test_get_returns_value(mock_redis_repository: Any) -> None:
    """_get() returns the stored string value."""
    mock_redis_repository._redis.get.return_value = "cached_value"

    get_result = await mock_redis_repository._get("user:123")

    assert get_result == "cached_value"
    mock_redis_repository._redis.get.assert_awaited_once_with("user:123")


async def test_get_returns_none_for_missing_key(mock_redis_repository: Any) -> None:
    """_get() returns None when the key does not exist."""
    mock_redis_repository._redis.get.return_value = None

    get_result = await mock_redis_repository._get("nonexistent")

    assert get_result is None


async def test_set_without_ttl(mock_redis_repository: Any) -> None:
    """_set() stores a value without expiration when ttl is None."""
    await mock_redis_repository._set("cache:item", "payload")

    mock_redis_repository._redis.set.assert_awaited_once_with("cache:item", "payload", ex=None)


async def test_set_with_ttl(mock_redis_repository: Any) -> None:
    """_set() stores a value with expiration in seconds."""
    await mock_redis_repository._set("cache:item", "payload", ttl=60)

    mock_redis_repository._redis.set.assert_awaited_once_with("cache:item", "payload", ex=60)


async def test_delete_calls_redis_delete(mock_redis_repository: Any) -> None:
    """delete() delegates to the underlying Redis delete."""
    await mock_redis_repository.delete("cache:item")

    mock_redis_repository._redis.delete.assert_awaited_once_with("cache:item")


async def test_exists_returns_true_when_key_present(mock_redis_repository: Any) -> None:
    """exists() returns True when Redis reports the key exists."""
    mock_redis_repository._redis.exists.return_value = 1

    assert await mock_redis_repository.exists("cache:item") is True
    mock_redis_repository._redis.exists.assert_awaited_once_with("cache:item")


async def test_exists_returns_false_when_key_missing(mock_redis_repository: Any) -> None:
    """exists() returns False when Redis reports the key does not exist."""
    mock_redis_repository._redis.exists.return_value = 0

    assert await mock_redis_repository.exists("cache:item") is False


async def test_get_json_returns_parsed_dict(mock_redis_repository: Any) -> None:
    """get_json() deserializes stored JSON string into a dict."""
    mock_redis_repository._redis.get.return_value = '{"name": "Alice", "age": 30}'

    get_json_result = await mock_redis_repository.get_json("persona:123")

    assert get_json_result == {"name": "Alice", "age": 30}


async def test_get_json_returns_none_for_missing_key(mock_redis_repository: Any) -> None:
    """get_json() returns None when the key does not exist."""
    mock_redis_repository._redis.get.return_value = None

    assert await mock_redis_repository.get_json("nonexistent") is None


async def test_get_json_raises_on_invalid_json(mock_redis_repository: Any) -> None:
    """get_json() raises RedisRepositoryError for malformed JSON."""
    mock_redis_repository._redis.get.return_value = "not-valid-json{{"

    with pytest.raises(RedisRepositoryError, match="Invalid JSON"):
        await mock_redis_repository.get_json("broken:key")


async def test_set_json_serializes_and_stores(mock_redis_repository: Any) -> None:
    """set_json() serializes dict to JSON and delegates to _set."""
    payload = {"name": "Alice", "age": 30}

    await mock_redis_repository.set_json("persona:123", payload, ttl=120)

    mock_redis_repository._redis.set.assert_awaited_once()
    call_args = mock_redis_repository._redis.set.call_args
    assert call_args.args[0] == "persona:123"
    assert '"name"' in call_args.args[1]
    assert call_args.kwargs["ex"] == 120


async def test_set_json_raises_on_unserializable_payload(mock_redis_repository: Any) -> None:
    """set_json() raises RedisRepositoryError if payload is not JSON-serializable."""
    unserializable = {"callback": lambda: None}

    with pytest.raises(RedisRepositoryError, match="Cannot serialize"):
        await mock_redis_repository.set_json("bad:key", unserializable)
