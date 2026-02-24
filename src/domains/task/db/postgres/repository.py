"""Task repository for PostgreSQL database operations.

This module provides the repository implementation for managing task entities
in PostgreSQL database using SQLAlchemy ORM.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select

from src.domains.task.db.postgres.model import TasksOrm
from src.infrastructure.db.postgres.repository import BaseCRUDRepository
from src.schemas.task import (
    CreateTaskSchema,
    TaskEntitySchema,
    UpdateTaskSchema,
)


class TaskRepository(BaseCRUDRepository[TasksOrm, CreateTaskSchema, UpdateTaskSchema, TaskEntitySchema]):
    """Repository for task entity CRUD operations.

    Provides async methods for creating, reading, updating, and deleting task records
    in PostgreSQL database.
    """

    async def create(
        self,
        create_data: CreateTaskSchema,
    ) -> TaskEntitySchema:
        """Create a new task record.

        Args:
            create_data: Schema containing task creation data.

        Returns:
            Created task entity with generated ID and timestamps.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        task = TasksOrm(
            type=create_data.type,
            status=create_data.status,
            progress=create_data.progress,
            error_log=create_data.error_log,
            input_params=create_data.input_params,
            user_id=create_data.user_id,
        )

        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)

        return TaskEntitySchema.model_validate(task)

    async def get_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[TaskEntitySchema]:
        """Retrieve a task by its ID.

        Args:
            entity_id: UUID of the task to retrieve.

        Returns:
            Task entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        task = await self._session.get(TasksOrm, entity_id)

        if task is None:
            return None

        return TaskEntitySchema.model_validate(task)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskEntitySchema]:
        """Retrieve all tasks with pagination.

        Args:
            limit: Maximum number of records to return. Defaults to 100.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of task entities.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        query = select(TasksOrm).limit(limit).offset(offset)
        tasks_result = await self._session.execute(query)
        tasks = tasks_result.scalars().all()

        return [TaskEntitySchema.model_validate(task) for task in tasks]

    async def get_count(self) -> int:
        """Get total count of tasks in the database.

        Returns:
            Total number of task records.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        query = select(func.count()).select_from(TasksOrm)
        tasks_result = await self._session.execute(query)

        return tasks_result.scalar_one()

    async def update_by_id(
        self,
        entity_id: uuid.UUID,
        update_data: UpdateTaskSchema,
    ) -> Optional[TaskEntitySchema]:
        """Update a task by its ID.

        Only fields present in update_data will be modified.

        Args:
            entity_id: UUID of the task to update.
            update_data: Schema containing fields to update.

        Returns:
            Updated task entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        task = await self._session.get(TasksOrm, entity_id)

        if task is None:
            return None

        update_fields = update_data.model_dump(exclude_unset=True)

        for field, task_value in update_fields.items():
            setattr(task, field, task_value)

        await self._session.flush()
        await self._session.refresh(task)

        return TaskEntitySchema.model_validate(task)

    async def delete_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """Delete a task by its ID.

        Args:
            entity_id: UUID of the task to delete.

        Returns:
            UUID of deleted task if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        task = await self._session.get(TasksOrm, entity_id)

        if task is None:
            return None

        await self._session.delete(task)
        await self._session.flush()

        return entity_id
