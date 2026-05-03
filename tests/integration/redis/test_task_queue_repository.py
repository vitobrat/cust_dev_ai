"""Integration tests for TaskQueueRepository.

Tests cover enqueue/dequeue operations and queue management
with real Redis via testcontainers. Each test runs against a clean
database — flushdb is called after every test.
"""

import uuid

import pytest

from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.db.redis.repository import TaskQueueRepository
from src.domains.task.exceptions import TaskQueueError
from src.schemas.interview import FinalReportGenerationTaskInputData
from src.schemas.persona import GeneratePersonasTaskInputData
from src.schemas.task import TaskSchema


def _build_task(**overrides: object) -> TaskSchema:
    """Build a TaskSchema with sensible defaults, overridable by kwargs."""
    defaults: dict[str, object] = {
        "task_id": uuid.uuid4(),
        "type": TaskType.PERSONAS_GENERATION,
        "status": TaskStatus.PENDING,
        "progress": 0,
        "error_log": None,
        "input_params": GeneratePersonasTaskInputData(
            segment_name="developers",
            segment_description="Software developers segment",
            person_count=3,
            interview_id=uuid.uuid4(),
        ),
        "user_id": uuid.uuid4(),
    }
    defaults.update(overrides)
    return TaskSchema(**defaults)


class TestTaskQueueRepositoryEnqueue:
    """Tests for TaskQueueRepository.enqueue()."""

    async def test_enqueue_returns_queue_length(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that enqueue() returns the queue length after insertion."""
        # Arrange
        task = _build_task()

        # Act
        length = await task_queue_repository.enqueue(task)

        # Assert
        assert length == 1

    async def test_enqueue_increments_length(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that successive enqueue() calls increment queue length."""
        # Arrange & Act
        first = await task_queue_repository.enqueue(_build_task())
        second = await task_queue_repository.enqueue(_build_task())
        third = await task_queue_repository.enqueue(_build_task())

        # Assert
        assert first == 1
        assert second == 2
        assert third == 3

    async def test_enqueue_makes_queue_non_empty(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that after enqueue() the queue size is positive."""
        # Act
        await task_queue_repository.enqueue(_build_task())

        # Assert
        assert await task_queue_repository.queue_size() > 0


class TestTaskQueueRepositoryDequeue:
    """Tests for TaskQueueRepository.dequeue()."""

    async def test_dequeue_returns_enqueued_task(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that dequeue() returns the same task that was enqueued."""
        # Arrange
        task = _build_task()
        await task_queue_repository.enqueue(task)

        # Act
        dequeued = await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert dequeued is not None
        assert dequeued.task_id == task.task_id
        assert dequeued.type == task.type
        assert dequeued.user_id == task.user_id
        assert dequeued.input_params == task.input_params

    async def test_dequeue_preserves_all_fields(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify full round-trip fidelity for all TaskSchema fields."""
        # Arrange
        task = _build_task(
            type=TaskType.REPORT_GENERATION,
            status=TaskStatus.IN_PROGRESS,
            progress=0.5,
            error_log="partial failure",
            input_params=FinalReportGenerationTaskInputData(interview_id=uuid.uuid4()),
        )
        await task_queue_repository.enqueue(task)

        # Act
        dequeued = await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert dequeued is not None
        assert dequeued.type == TaskType.REPORT_GENERATION
        assert dequeued.status == TaskStatus.IN_PROGRESS
        assert str(dequeued.progress) == "0.5"
        assert dequeued.error_log == "partial failure"
        assert dequeued.input_params == task.input_params

    async def test_dequeue_returns_none_on_empty_queue(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that dequeue() returns None when queue is empty and timeout expires."""
        # Act
        dequeued = await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert dequeued is None

    async def test_dequeue_fifo_order(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify FIFO ordering: first enqueued task is dequeued first."""
        # Arrange
        first_task = _build_task()
        second_task = _build_task()
        third_task = _build_task()

        await task_queue_repository.enqueue(first_task)
        await task_queue_repository.enqueue(second_task)
        await task_queue_repository.enqueue(third_task)

        # Act
        d1 = await task_queue_repository.dequeue(timeout=1)
        d2 = await task_queue_repository.dequeue(timeout=1)
        d3 = await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert d1 is not None and d1.task_id == first_task.task_id
        assert d2 is not None and d2.task_id == second_task.task_id
        assert d3 is not None and d3.task_id == third_task.task_id

    async def test_dequeue_removes_task_from_queue(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that dequeue() decreases the queue size by one."""
        # Arrange
        await task_queue_repository.enqueue(_build_task())
        await task_queue_repository.enqueue(_build_task())

        # Act
        await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert await task_queue_repository.queue_size() == 1

    async def test_dequeue_raises_on_corrupted_payload(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that dequeue() raises TaskQueueError for corrupted data."""
        # Arrange — push raw invalid JSON bypassing enqueue()
        await task_queue_repository._lpush("queue:tasks", "not-valid-json{{{")

        # Act & Assert
        with pytest.raises(TaskQueueError, match="Corrupted task payload"):
            await task_queue_repository.dequeue(timeout=1)


class TestTaskQueueRepositoryQueueSize:
    """Tests for TaskQueueRepository.queue_size()."""

    async def test_queue_size_returns_zero_for_empty_queue(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that queue_size() returns 0 on a fresh queue."""
        # Act & Assert
        assert await task_queue_repository.queue_size() == 0

    async def test_queue_size_reflects_enqueue(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that queue_size() grows with each enqueue()."""
        # Act
        await task_queue_repository.enqueue(_build_task())
        await task_queue_repository.enqueue(_build_task())

        # Assert
        assert await task_queue_repository.queue_size() == 2

    async def test_queue_size_reflects_dequeue(
        self,
        task_queue_repository: TaskQueueRepository,
    ) -> None:
        """Verify that queue_size() decreases after dequeue()."""
        # Arrange
        await task_queue_repository.enqueue(_build_task())
        await task_queue_repository.enqueue(_build_task())
        await task_queue_repository.enqueue(_build_task())

        # Act
        await task_queue_repository.dequeue(timeout=1)

        # Assert
        assert await task_queue_repository.queue_size() == 2
