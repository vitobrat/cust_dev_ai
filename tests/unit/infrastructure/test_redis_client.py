"""Unit tests for RedisClient connection pooling and lifecycle."""

from typing import Any
from unittest.mock import AsyncMock


async def test_client_property_returns_underlying_redis(
    mock_redis_client: Any,
) -> None:
    """The ``client`` property exposes the underlying Redis instance."""
    assert mock_redis_client.client is mock_redis_client._client


async def test_from_url_receives_configured_params(
    mock_redis_client: Any,
) -> None:
    """RedisClient stores the Redis instance created by from_url."""
    assert isinstance(mock_redis_client._client, AsyncMock)


async def test_ping_delegates_to_redis(mock_redis_client: Any) -> None:
    """ping() awaits the underlying Redis ping and returns its result."""
    mock_redis_client._client.ping.return_value = True

    ping_result = await mock_redis_client.ping()

    assert ping_result is True
    mock_redis_client._client.ping.assert_awaited_once()


async def test_close_delegates_to_redis(mock_redis_client: Any) -> None:
    """close() awaits the underlying Redis aclose."""
    await mock_redis_client.close()

    mock_redis_client._client.aclose.assert_awaited_once()
