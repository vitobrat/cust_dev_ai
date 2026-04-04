"""Task handler protocol for the Redis worker."""

from typing import Protocol

from src.schemas.task import TaskSchema


class TaskHandler(Protocol):
    """Protocol that all task handlers must satisfy.

    Each concrete handler implements domain-specific logic
    for a particular ``TaskType``.
    """

    async def execute(self, task: TaskSchema) -> None:
        """Execute the task.

        Args:
            task: Dequeued task payload.

        Raises:
            Exception: Any domain error; the worker will catch it
                and mark the task as ``FAILED``.
        """
        ...
