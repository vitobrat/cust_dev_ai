"""Business logic service for the Task domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.task.db.postgres.repository import TaskRepository
from src.domains.task.exceptions import (
    TaskDeletionFailed,
    TaskGetFailed,
    TaskUpdateFailed,
)
from src.schemas.task import (
    CreateTaskSchema,
    TaskRelEntitySchema,
    UpdateTaskSchema,
)


class TaskService:
    """Service layer for task business logic.

    Encapsulates CRUD operations for task entities, acting as the boundary
    between the HTTP layer and the persistence layer.

    Attributes:
        _tasks_repository: Repository for task persistence operations.
    """

    def __init__(self, tasks_repository: TaskRepository) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._tasks_repository = tasks_repository

    async def create_task(self, create_task_data: CreateTaskSchema) -> TaskRelEntitySchema:
        """Persist a new task entity.

        Args:
            create_task_data: Validated creation payload.

        Returns:
            Newly created task entity with generated ID and timestamps.
        """
        return await self._tasks_repository.create(create_task_data)

    async def get_task(self, task_id: uuid.UUID) -> TaskRelEntitySchema:
        """Retrieve a single task by its identifier.

        Args:
            task_id: UUID of the task to retrieve.

        Returns:
            Task entity with loaded relations if found.

        Raises:
            TaskGetFailed: If no task with the given ID exists.
        """
        task = await self._tasks_repository.get_by_id(task_id)

        if task is None:
            self._logger.error("Task not found: %s", task_id)
            raise TaskGetFailed(f"Task with id={task_id} does not exist.")

        return task

    async def get_tasks(self, limit: int = 10, offset: int = 0) -> list[TaskRelEntitySchema]:
        """Retrieve a paginated list of tasks.

        Args:
            limit: Maximum number of records to return. Defaults to 10.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of task entities (may be empty).
        """
        return await self._tasks_repository.get_all(limit, offset)

    async def count_tasks(self) -> int:
        """Return the total number of stored tasks.

        Returns:
            Integer count of task records.
        """
        return await self._tasks_repository.get_count()

    async def update_task(
        self,
        task_id: uuid.UUID,
        update_task_data: UpdateTaskSchema,
    ) -> TaskRelEntitySchema:
        """Apply a partial update to an existing task.

        Args:
            task_id: UUID of the task to update.
            update_task_data: Partial schema; only set fields are applied.

        Returns:
            Updated task entity.

        Raises:
            TaskUpdateFailed: If no task with the given ID exists.
        """
        updated_task = await self._tasks_repository.update_by_id(task_id, update_task_data)

        if updated_task is None:
            self._logger.error("Task not found for update: %s", task_id)
            raise TaskUpdateFailed(f"Task with id={task_id} does not exist.")

        return updated_task

    async def delete_task(self, task_id: uuid.UUID) -> None:
        """Delete a task by its identifier.

        Args:
            task_id: UUID of the task to delete.

        Raises:
            TaskDeletionFailed: If no task with the given ID exists.
        """
        deleted_id = await self._tasks_repository.delete_by_id(task_id)

        if deleted_id is None:
            self._logger.error("Task not found for deletion: %s", task_id)
            raise TaskDeletionFailed(f"Task with id={task_id} does not exist.")
