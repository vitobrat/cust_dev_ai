"""Task queue repository — enqueue / dequeue operations."""

from __future__ import annotations

from pydantic import ValidationError

from src.domains.task.exceptions import TaskQueueError
from src.infrastructure.db.redis.repository import BaseRedisRepository
from src.schemas.task import TaskSchema

_QUEUE_KEY = "queue:tasks"


class TaskQueueRepository(BaseRedisRepository):
    """Redis-backed FIFO queue for task payloads.

    Uses a Redis list under the key ``queue:tasks``.
    New tasks are pushed to the head (``LPUSH``),
    workers consume from the tail (``BRPOP``).
    """

    async def enqueue(self, task: TaskSchema) -> int:
        """Add a task to the queue.

        Args:
            task: Validated task to enqueue.

        Returns:
            Current queue length after the push.
        """
        return await self._lpush(_QUEUE_KEY, task.model_dump_json())

    async def dequeue(self, timeout: int = 0) -> TaskSchema | None:
        """Wait for and return the next task from the queue.

        Args:
            timeout: Seconds to wait for a task.
                ``0`` means block indefinitely.

        Returns:
            Deserialized task, or ``None`` if the timeout elapsed.

        Raises:
            TaskQueueError: If the popped value cannot be parsed
                into a valid ``TaskSchema``.
        """
        pop_result = await self._brpop(_QUEUE_KEY, timeout=timeout)

        if pop_result is None:
            return None

        _, raw_payload = pop_result

        try:
            return TaskSchema.model_validate_json(raw_payload)
        except ValidationError as exc:
            self._logger.error(
                "Failed to validate task payload: %s",
                exc,
            )
            raise TaskQueueError(
                "Corrupted task payload in queue",
            ) from exc

    async def queue_size(self) -> int:
        """Return the number of tasks currently in the queue."""
        return await self._llen(_QUEUE_KEY)
