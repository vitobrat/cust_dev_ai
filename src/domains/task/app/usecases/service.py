"""Business logic service for the Task domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.db.postgres.repository import TaskRepository
from src.domains.task.db.redis.repository import TaskQueueRepository
from src.domains.task.exceptions import (
    TaskCreationFailed,
    TaskDeletionFailed,
    TaskGetFailed,
    TaskQueueError,
    TaskUpdateFailed,
)
from src.schemas.interview import (
    FinalReportGenerationTaskInputData,
    InterviewSimulationTaskInputData,
)
from src.schemas.persona import (
    GeneratePersonasTaskInputData,
    GenerateSinglePersonaTaskInputData,
    PersonasPipelineTaskInputData,
)
from src.schemas.task import (
    CreateTaskSchema,
    TaskInputParams,
    TaskRelEntitySchema,
    TaskSchema,
    UpdateTaskSchema,
)


class TaskService:
    """Service layer for task business logic.

    Encapsulates CRUD operations for task entities, acting as the boundary
    between the HTTP layer and the persistence layer.

    Attributes:
        _tasks_repository: Repository for task persistence operations.
        _redis_task_repository: Repository for task queue operations.
    """

    def __init__(
        self,
        tasks_repository: TaskRepository,
        redis_task_repository: TaskQueueRepository,
    ) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._tasks_repository = tasks_repository
        self._redis_task_repository = redis_task_repository

    async def register_personas_pipeline_task(
        self,
        user_id: uuid.UUID,
        task_input: PersonasPipelineTaskInputData,
    ) -> None:
        """Register a full persona pipeline task (segment search + generation).

        Args:
            user_id: Owner of the task.
            task_input: Input with user prompt, interview reference, and persona count.

        Raises:
            TaskCreationFailed: If Postgres insert fails.
            TaskQueueError: If Redis enqueue fails (task is marked FAILED first).
        """
        await self._register_task(user_id, TaskType.PERSONAS_PIPELINE, task_input)

    async def register_generate_personas_task(
        self,
        user_id: uuid.UUID,
        task_input: GeneratePersonasTaskInputData,
    ) -> None:
        """Register a batch persona generation task.

        Args:
            user_id: Owner of the task.
            task_input: Input with segment info, interview reference, and persona count.

        Raises:
            TaskCreationFailed: If Postgres insert fails.
            TaskQueueError: If Redis enqueue fails (task is marked FAILED first).
        """
        await self._register_task(user_id, TaskType.PERSONAS_GENERATION, task_input)

    async def register_generate_single_persona_task(
        self,
        user_id: uuid.UUID,
        task_input: GenerateSinglePersonaTaskInputData,
    ) -> None:
        """Register a single persona generation task.

        Args:
            user_id: Owner of the task.
            task_input: Input with segment info and interview reference.

        Raises:
            TaskCreationFailed: If Postgres insert fails.
            TaskQueueError: If Redis enqueue fails (task is marked FAILED first).
        """
        await self._register_task(user_id, TaskType.SINGLE_PERSONA_GENERATION, task_input)

    async def register_interview_simulation_task(
        self,
        user_id: uuid.UUID,
        task_input: InterviewSimulationTaskInputData,
    ) -> None:
        """Register a full interview simulation task.

        Args:
            user_id: Owner of the task.
            task_input: Input with interview reference, segment context, and batch controls.

        Raises:
            TaskCreationFailed: If Postgres insert fails.
            TaskQueueError: If Redis enqueue fails (task is marked FAILED first).
        """
        await self._register_task(user_id, TaskType.INTERVIEW_SIMULATION, task_input)

    async def register_final_report_generation_task(
        self,
        user_id: uuid.UUID,
        task_input: FinalReportGenerationTaskInputData,
    ) -> None:
        """Register a final interview analytics report generation task.

        Args:
            user_id: Owner of the task.
            task_input: Input with interview reference. Report source data is loaded from PostgreSQL.

        Raises:
            TaskCreationFailed: If Postgres insert fails.
            TaskQueueError: If Redis enqueue fails (task is marked FAILED first).
        """
        await self._register_task(user_id, TaskType.REPORT_GENERATION, task_input)

    async def create_task(self, create_task_data: CreateTaskSchema) -> TaskRelEntitySchema:
        """Persist a new task entity.

        Args:
            create_task_data: Validated creation payload.

        Returns:
            Newly created task entity with generated ID and timestamps.

        Raises:
            TaskCreationFailed: If the database insert fails.
        """
        try:
            task_entity = await self._tasks_repository.create(create_task_data)
        except Exception as exc:
            self._logger.error("Task creation failed: %s", exc)
            raise TaskCreationFailed(f"Failed to create task: {exc}") from exc

        return task_entity

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

    async def _register_task(
        self,
        user_id: uuid.UUID,
        task_type: TaskType,
        task_input: TaskInputParams,
    ) -> None:
        """Persist a task in Postgres and enqueue it in Redis.

        If enqueue fails the task is rolled back to FAILED status so it
        does not remain stuck in PENDING state forever.

        Args:
            user_id: Owner of the task.
            task_type: Type of the task to register.
            task_input: Validated, discriminator-tagged input payload.

        Raises:
            TaskCreationFailed: If Postgres insert fails.
            TaskQueueError: If Redis enqueue fails (task is marked FAILED first).
        """
        task_entity = await self.create_task(
            CreateTaskSchema(
                user_id=user_id,
                type=task_type,
                input_params=task_input,
            ),
        )
        self._logger.debug("Task type %s successfully created in DB", task_entity.type)

        try:
            queue_length = await self._redis_task_repository.enqueue(
                TaskSchema(
                    task_id=task_entity.id,
                    user_id=user_id,
                    type=task_type,
                    input_params=task_input,
                ),
            )
        except TaskQueueError:
            await self._tasks_repository.update_by_id(
                task_entity.id,
                UpdateTaskSchema(status=TaskStatus.FAILED),
            )
            raise

        self._logger.debug(
            "Task %s enqueued in Redis, queue length: %s",
            task_entity.id,
            queue_length,
        )
