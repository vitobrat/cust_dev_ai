"""Unit tests for BaseRedisRepository list operations."""

from typing import Any


async def test_lpush_returns_list_length(mock_redis_repository: Any) -> None:
    """_lpush() returns the list length after the push."""
    mock_redis_repository._redis.lpush.return_value = 3

    lpush_result = await mock_redis_repository._lpush("queue:tasks", "payload")

    assert lpush_result == 3
    mock_redis_repository._redis.lpush.assert_awaited_once_with("queue:tasks", "payload")


async def test_brpop_returns_key_value_tuple(mock_redis_repository: Any) -> None:
    """_brpop() returns (key, value) tuple when an element is available."""
    mock_redis_repository._redis.brpop.return_value = ("queue:tasks", "payload")

    brpop_result = await mock_redis_repository._brpop("queue:tasks", timeout=1)

    assert brpop_result == ("queue:tasks", "payload")
    mock_redis_repository._redis.brpop.assert_awaited_once_with("queue:tasks", timeout=1)


async def test_brpop_returns_none_on_timeout(mock_redis_repository: Any) -> None:
    """_brpop() returns None when the timeout elapses with no element."""
    mock_redis_repository._redis.brpop.return_value = None

    brpop_result = await mock_redis_repository._brpop("queue:tasks", timeout=1)

    assert brpop_result is None


async def test_brpop_defaults_to_zero_timeout(mock_redis_repository: Any) -> None:
    """_brpop() passes timeout=0 by default (block indefinitely)."""
    mock_redis_repository._redis.brpop.return_value = None

    await mock_redis_repository._brpop("queue:tasks")

    mock_redis_repository._redis.brpop.assert_awaited_once_with("queue:tasks", timeout=0)


async def test_llen_returns_list_length(mock_redis_repository: Any) -> None:
    """_llen() returns the number of elements in the list."""
    mock_redis_repository._redis.llen.return_value = 5

    llen_result = await mock_redis_repository._llen("queue:tasks")

    assert llen_result == 5
    mock_redis_repository._redis.llen.assert_awaited_once_with("queue:tasks")


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
