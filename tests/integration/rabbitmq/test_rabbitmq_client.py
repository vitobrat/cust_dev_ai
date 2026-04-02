"""Integration tests for RabbitMQClient.

Tests cover connect/close lifecycle, publish/consume round-trip,
publish_reply, and RPC call with a real RabbitMQ broker via testcontainers.
"""

import asyncio
import uuid
from typing import Any

import pytest

from src.configs.config import RabbitMQConfigs
from src.infrastructure.rabbitmq.client import RabbitMQClient

_QUEUE_ID_LENGTH = 12
_CONSUME_TIMEOUT_SEC = 5.0
_BATCH_CONSUME_TIMEOUT_SEC = 10.0
_BATCH_MESSAGE_COUNT = 5


def _unique_queue() -> str:
    """Generate a unique queue name to isolate tests."""
    return f"test-queue-{uuid.uuid4().hex[:_QUEUE_ID_LENGTH]}"


class _PayloadCapture:
    """Capture the payload from a consumed message into an asyncio.Future."""

    def __init__(self, future: asyncio.Future[dict[str, Any]]) -> None:
        self._future = future

    async def __call__(
        self,
        reply_to: str | None,
        correlation_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        self._future.set_result(payload)


class _ReplyToCapture:
    """Capture reply_to from a consumed message into an asyncio.Future."""

    def __init__(self, future: asyncio.Future[str | None]) -> None:
        self._future = future

    async def __call__(
        self,
        reply_to: str | None,
        correlation_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        self._future.set_result(reply_to)


class _CorrelationIdCapture:
    """Capture correlation_id from a consumed message into an asyncio.Future."""

    def __init__(self, future: asyncio.Future[str | None]) -> None:
        self._future = future

    async def __call__(
        self,
        reply_to: str | None,
        correlation_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        self._future.set_result(correlation_id)


class _BatchCapture:
    """Collect payloads from multiple consumed messages."""

    def __init__(
        self,
        collected: list[dict[str, Any]],
        done_event: asyncio.Event,
        expected_count: int,
    ) -> None:
        self._collected = collected
        self._done_event = done_event
        self._expected_count = expected_count

    async def __call__(
        self,
        reply_to: str | None,
        correlation_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        self._collected.append(payload)
        if len(self._collected) >= self._expected_count:
            self._done_event.set()


class TestRabbitMQClientConnection:
    """Tests for connect() and close() lifecycle."""

    async def test_connect_establishes_connection(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that connect() sets _connection to a non-None value."""
        assert rabbitmq_client._connection is not None

    async def test_connect_creates_channel(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that connect() sets _channel to a non-None value."""
        assert rabbitmq_client._channel is not None

    async def test_close_releases_connection(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that close() sets _connection to None."""
        await rabbitmq_client.close()
        assert rabbitmq_client._connection is None

    async def test_close_releases_channel(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that close() sets _channel to None."""
        await rabbitmq_client.close()
        assert rabbitmq_client._channel is None

    async def test_close_without_connect_does_not_raise(
        self,
        rabbitmq_configs: RabbitMQConfigs,
    ) -> None:
        """Verify that close() without connect() does not raise."""
        client = RabbitMQClient(configs=rabbitmq_configs)
        await client.close()


class TestRabbitMQClientPublishConsume:
    """Tests for publish() and consume() round-trip."""

    async def test_publish_and_consume_receives_correct_payload(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that a published message is received with correct payload."""
        queue_name = _unique_queue()
        expected_payload = {"action": "test", "value": 42}
        received: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()

        await rabbitmq_client.consume(queue_name, _PayloadCapture(received))
        await rabbitmq_client.publish(queue_name, expected_payload)

        actual_payload = await asyncio.wait_for(received, timeout=_CONSUME_TIMEOUT_SEC)
        assert actual_payload == expected_payload

    async def test_publish_and_consume_reply_to_is_none_by_default(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that reply_to is None for a regular published message."""
        queue_name = _unique_queue()
        received: asyncio.Future[str | None] = asyncio.get_event_loop().create_future()

        await rabbitmq_client.consume(queue_name, _ReplyToCapture(received))
        await rabbitmq_client.publish(queue_name, {"ping": True})

        captured_reply_to = await asyncio.wait_for(received, timeout=_CONSUME_TIMEOUT_SEC)
        assert captured_reply_to is None

    async def test_publish_and_consume_correlation_id_is_none_by_default(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that correlation_id is None for a regular published message."""
        queue_name = _unique_queue()
        received: asyncio.Future[str | None] = asyncio.get_event_loop().create_future()

        await rabbitmq_client.consume(queue_name, _CorrelationIdCapture(received))
        await rabbitmq_client.publish(queue_name, {"ping": True})

        captured_corr_id = await asyncio.wait_for(received, timeout=_CONSUME_TIMEOUT_SEC)
        assert captured_corr_id is None

    async def test_publish_multiple_messages_all_consumed(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that multiple published messages are all consumed."""
        queue_name = _unique_queue()
        collected: list[dict[str, Any]] = []
        all_received = asyncio.Event()

        capture = _BatchCapture(collected, all_received, _BATCH_MESSAGE_COUNT)
        await rabbitmq_client.consume(queue_name, capture)

        for idx in range(_BATCH_MESSAGE_COUNT):
            await rabbitmq_client.publish(queue_name, {"index": idx})

        await asyncio.wait_for(all_received.wait(), timeout=_BATCH_CONSUME_TIMEOUT_SEC)
        assert len(collected) == _BATCH_MESSAGE_COUNT

    async def test_publish_to_nonexistent_queue_creates_it(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that publishing to a non-existent queue creates it automatically."""
        queue_name = _unique_queue()
        await rabbitmq_client.publish(queue_name, {"auto": "create"})

        received: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()

        await rabbitmq_client.consume(queue_name, _PayloadCapture(received))

        actual_payload = await asyncio.wait_for(received, timeout=_CONSUME_TIMEOUT_SEC)
        assert actual_payload == {"auto": "create"}


class TestRabbitMQClientPublishReplyIntegration:
    """Tests for publish_reply() with real broker."""

    async def test_publish_reply_delivers_to_reply_queue(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that publish_reply() delivers a message to the reply queue."""
        reply_queue = _unique_queue()
        expected_payload = {"result": "success"}
        received: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()

        await rabbitmq_client.consume(reply_queue, _PayloadCapture(received))
        await rabbitmq_client.publish_reply(reply_queue, "corr-abc", expected_payload)

        actual_payload = await asyncio.wait_for(received, timeout=_CONSUME_TIMEOUT_SEC)
        assert actual_payload == expected_payload

    async def test_publish_reply_preserves_correlation_id(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that publish_reply() preserves the correlation_id."""
        reply_queue = _unique_queue()
        expected_corr_id = "unique-corr-id-999"
        received: asyncio.Future[str | None] = asyncio.get_event_loop().create_future()

        await rabbitmq_client.consume(reply_queue, _CorrelationIdCapture(received))
        await rabbitmq_client.publish_reply(reply_queue, expected_corr_id, {"ok": True})

        actual_corr_id = await asyncio.wait_for(received, timeout=_CONSUME_TIMEOUT_SEC)
        assert actual_corr_id == expected_corr_id


class _EchoHandler:
    """Simulate a remote RPC server: consume a request and reply with transformed payload."""

    def __init__(self, client: RabbitMQClient) -> None:
        self._client = client

    async def __call__(
        self,
        reply_to: str | None,
        correlation_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        if reply_to is None or correlation_id is None:
            return
        response = {"echo": payload, "status": "ok"}
        await self._client.publish_reply(reply_to, correlation_id, response)


class TestRabbitMQClientRpcCall:
    """Tests for rpc_call() RPC round-trip."""

    async def test_rpc_call_returns_reply_payload(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that rpc_call() sends a request and receives the correct reply."""
        queue_name = _unique_queue()
        await rabbitmq_client.consume(queue_name, _EchoHandler(rabbitmq_client))

        reply_payload = await rabbitmq_client.rpc_call(queue_name, {"question": "ping"})

        assert reply_payload == {"echo": {"question": "ping"}, "status": "ok"}

    async def test_rpc_call_sets_reply_to_on_message(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that rpc_call() sets reply_to property on the outgoing message."""
        queue_name = _unique_queue()
        captured_reply_to: asyncio.Future[str | None] = asyncio.get_running_loop().create_future()

        await rabbitmq_client.consume(queue_name, _ReplyToCapture(captured_reply_to))
        # Fire rpc_call but don't await reply (no echo handler), use short timeout.
        with pytest.raises(asyncio.TimeoutError):
            await rabbitmq_client.rpc_call(queue_name, {"check": "reply_to"}, timeout=1.0)

        reply_to = await asyncio.wait_for(captured_reply_to, timeout=_CONSUME_TIMEOUT_SEC)
        assert reply_to is not None
        assert len(reply_to) > 0

    async def test_rpc_call_sets_correlation_id_on_message(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that rpc_call() sets correlation_id property on the outgoing message."""
        queue_name = _unique_queue()
        captured_corr_id: asyncio.Future[str | None] = asyncio.get_running_loop().create_future()

        await rabbitmq_client.consume(queue_name, _CorrelationIdCapture(captured_corr_id))
        with pytest.raises(asyncio.TimeoutError):
            await rabbitmq_client.rpc_call(queue_name, {"check": "corr_id"}, timeout=1.0)

        corr_id = await asyncio.wait_for(captured_corr_id, timeout=_CONSUME_TIMEOUT_SEC)
        assert corr_id is not None
        assert len(corr_id) > 0

    async def test_rpc_call_timeout_raises(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that rpc_call() raises TimeoutError when no reply arrives."""
        queue_name = _unique_queue()

        with pytest.raises(asyncio.TimeoutError):
            await rabbitmq_client.rpc_call(queue_name, {"waiting": "forever"}, timeout=0.5)

    async def test_rpc_call_timeout_cleans_up_pending(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that a timed-out rpc_call removes its future from _pending_rpcs."""
        queue_name = _unique_queue()

        with pytest.raises(asyncio.TimeoutError):
            await rabbitmq_client.rpc_call(queue_name, {"stale": True}, timeout=0.5)

        assert len(rabbitmq_client._pending_rpcs) == 0

    async def test_rpc_call_multiple_parallel(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that multiple concurrent rpc_call() invocations resolve independently."""
        queue_name = _unique_queue()
        await rabbitmq_client.consume(queue_name, _EchoHandler(rabbitmq_client))

        replies = await asyncio.gather(
            rabbitmq_client.rpc_call(queue_name, {"idx": 1}),
            rabbitmq_client.rpc_call(queue_name, {"idx": 2}),
            rabbitmq_client.rpc_call(queue_name, {"idx": 3}),
        )

        echoed_indices = sorted(reply["echo"]["idx"] for reply in replies)
        assert echoed_indices == [1, 2, 3]

    async def test_rpc_call_reuses_reply_queue(
        self,
        rabbitmq_client: RabbitMQClient,
    ) -> None:
        """Verify that consecutive rpc_call() invocations reuse the same reply queue."""
        queue_name = _unique_queue()
        await rabbitmq_client.consume(queue_name, _EchoHandler(rabbitmq_client))

        await rabbitmq_client.rpc_call(queue_name, {"first": True})
        first_queue = rabbitmq_client._reply_queue_name

        await rabbitmq_client.rpc_call(queue_name, {"second": True})
        second_queue = rabbitmq_client._reply_queue_name

        assert first_queue == second_queue
