"""Unit tests for TaskQueueRepository.

Tests verify serialization, deserialization, error handling,
and correct delegation to base Redis operations — all with mocked Redis.
"""

from typing import Any

import pytest

from src.domains.task.exceptions import TaskQueueError
from src.schemas.task import TaskSchema

_QUEUE_KEY = "queue:tasks"


class TestTaskQueueRepositoryEnqueue:
    """Tests for TaskQueueRepository.enqueue()."""

    async def test_enqueue_calls_lpush_with_serialized_task(
        self,
        task_queue_repository: Any,
        sample_task: TaskSchema,
    ) -> None:
        """Verify that enqueue() pushes the JSON-serialized task to the list."""
        # Arrange
        task_queue_repository._redis.lpush.return_value = 1

        # Act
        await task_queue_repository.enqueue(sample_task)

        # Assert
        task_queue_repository._redis.lpush.assert_awaited_once_with(
            _QUEUE_KEY,
            sample_task.model_dump_json(),
        )

    async def test_enqueue_returns_queue_length(
        self,
        task_queue_repository: Any,
        sample_task: TaskSchema,
    ) -> None:
        """Verify that enqueue() returns the list length after push."""
        # Arrange
        task_queue_repository._redis.lpush.return_value = 5

        # Act
        length = await task_queue_repository.enqueue(sample_task)

        # Assert
        assert length == 5

    async def test_enqueue_preserves_task_fields_in_payload(
        self,
        task_queue_repository: Any,
        sample_task: TaskSchema,
    ) -> None:
        """Verify that the serialized payload contains all task fields."""
        # Arrange
        task_queue_repository._redis.lpush.return_value = 1

        # Act
        await task_queue_repository.enqueue(sample_task)

        # Assert
        call_args = task_queue_repository._redis.lpush.call_args
        raw_payload = call_args.args[1]
        restored = TaskSchema.model_validate_json(raw_payload)
        assert restored.task_id == sample_task.task_id
        assert restored.type == sample_task.type
        assert restored.user_id == sample_task.user_id
        assert restored.input_params == sample_task.input_params


class TestTaskQueueRepositoryDequeue:
    """Tests for TaskQueueRepository.dequeue()."""

    async def test_dequeue_returns_none_on_timeout(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that dequeue() returns None when brpop times out."""
        # Arrange
        task_queue_repository._redis.brpop.return_value = None

        # Act
        dequeue_result = await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert dequeue_result is None

    async def test_dequeue_calls_brpop_with_correct_args(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that dequeue() delegates to brpop with queue key and timeout."""
        # Arrange
        task_queue_repository._redis.brpop.return_value = None

        # Act
        await task_queue_repository.dequeue(timeout=10)

        # Assert
        task_queue_repository._redis.brpop.assert_awaited_once_with(
            _QUEUE_KEY,
            timeout=10,
        )

    async def test_dequeue_returns_deserialized_task(
        self,
        task_queue_repository: Any,
        sample_task: TaskSchema,
    ) -> None:
        """Verify that dequeue() deserializes the payload into TaskSchema."""
        # Arrange
        raw_json = sample_task.model_dump_json()
        task_queue_repository._redis.brpop.return_value = (_QUEUE_KEY, raw_json)

        # Act
        dequeue_result = await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert dequeue_result is not None
        assert isinstance(dequeue_result, TaskSchema)
        assert dequeue_result.task_id == sample_task.task_id
        assert dequeue_result.type == sample_task.type
        assert dequeue_result.user_id == sample_task.user_id

    async def test_dequeue_raises_task_queue_error_on_invalid_payload(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that dequeue() raises TaskQueueError for corrupted JSON."""
        # Arrange
        task_queue_repository._redis.brpop.return_value = (
            _QUEUE_KEY,
            "not-a-valid-json{{{",
        )

        # Act & Assert
        with pytest.raises(TaskQueueError, match="Corrupted task payload"):
            await task_queue_repository.dequeue(timeout=1)

    async def test_dequeue_raises_task_queue_error_on_missing_fields(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that dequeue() raises TaskQueueError when fields are missing."""
        # Arrange — valid JSON but not a valid TaskSchema
        task_queue_repository._redis.brpop.return_value = (
            _QUEUE_KEY,
            '{"task_id": "not-a-uuid"}',
        )

        # Act & Assert
        with pytest.raises(TaskQueueError, match="Corrupted task payload"):
            await task_queue_repository.dequeue(timeout=1)

    async def test_dequeue_uses_zero_timeout_by_default(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that dequeue() defaults to timeout=0 (block indefinitely)."""
        # Arrange
        task_queue_repository._redis.brpop.return_value = None

        # Act
        await task_queue_repository.dequeue()

        # Assert
        task_queue_repository._redis.brpop.assert_awaited_once_with(
            _QUEUE_KEY,
            timeout=0,
        )


class TestTaskQueueRepositoryQueueSize:
    """Tests for TaskQueueRepository.queue_size()."""

    async def test_queue_size_delegates_to_llen(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that queue_size() calls llen with the correct key."""
        # Arrange
        task_queue_repository._redis.llen.return_value = 42

        # Act
        size = await task_queue_repository.queue_size()

        # Assert
        assert size == 42
        task_queue_repository._redis.llen.assert_awaited_once_with(_QUEUE_KEY)

    async def test_queue_size_returns_zero_for_empty_queue(
        self,
        task_queue_repository: Any,
    ) -> None:
        """Verify that queue_size() returns 0 when the queue is empty."""
        # Arrange
        task_queue_repository._redis.llen.return_value = 0

        # Act
        size = await task_queue_repository.queue_size()

        # Assert
        assert size == 0
