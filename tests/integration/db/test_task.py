"""Integration tests for TaskRepository.

Tests cover all CRUD operations with real PostgreSQL via testcontainers.
Each test runs in an isolated transaction that is rolled back after completion.
"""

import uuid
from collections.abc import Callable

from src.domains.task.app.constants import TaskStatus, TaskType
from src.domains.task.db.postgres.repository import TaskRepository
from src.infrastructure.db.postgres.client import DatabaseClient
from src.schemas.persona import GeneratePersonasInputData
from src.schemas.task import (
    CreateTaskSchema,
    TaskRelEntitySchema,
    UpdateTaskSchema,
)
from src.schemas.user import UserEntitySchema, UserRelEntitySchema


class TestTaskRepositoryCreate:
    """Tests for TaskRepository.create().

    All tests call the repository directly to verify DB behaviour.
    """

    async def test_create_returns_task_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() returns TaskRelEntitySchema instance."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert isinstance(task_result, TaskRelEntitySchema)

    async def test_create_generates_uuid(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() generates a valid UUID for the new task."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.id is not None
        assert isinstance(task_result.id, uuid.UUID)

    async def test_create_persists_type(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() correctly persists the type field."""
        # Arrange
        repo = TaskRepository(db_client)
        task_type = TaskType.PERSONA_GENERATION
        task_data = create_task_schema_factory(user_id=user.id, type=task_type)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.type == task_type

    async def test_create_persists_status(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() correctly persists the status field."""
        # Arrange
        repo = TaskRepository(db_client)
        task_status = TaskStatus.PENDING
        task_data = create_task_schema_factory(user_id=user.id, status=task_status)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.status == task_status

    async def test_create_persists_progress(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() correctly persists the progress field."""
        # Arrange
        repo = TaskRepository(db_client)
        progress = 0.5
        task_data = create_task_schema_factory(user_id=user.id, progress=progress)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.progress == progress

    async def test_create_persists_error_log_none(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() correctly persists error_log=None."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id, error_log=None)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.error_log is None

    async def test_create_persists_error_log_with_message(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() correctly persists error_log with error message."""
        # Arrange
        repo = TaskRepository(db_client)
        error_message = "Connection timeout after 30 seconds"
        task_data = create_task_schema_factory(user_id=user.id, error_log=error_message)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.error_log == error_message

    async def test_create_persists_input_params(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() correctly persists input_params field."""
        # Arrange
        repo = TaskRepository(db_client)
        input_params = GeneratePersonasInputData(
            segment_name="test_segment",
            segment_description="test_description",
            person_count=5,
            interview_id=uuid.uuid4(),
        )
        task_data = create_task_schema_factory(user_id=user.id, input_params=input_params)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.input_params == input_params

    async def test_create_generates_created_at_timestamp(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() automatically generates created_at timestamp."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.created_at is not None

    async def test_create_generates_updated_at_timestamp(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() automatically generates updated_at timestamp."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.updated_at is not None

    async def test_create_two_tasks_have_different_ids(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that multiple create() calls generate unique IDs."""
        # Arrange
        repo = TaskRepository(db_client)
        data_first = create_task_schema_factory(user_id=user.id)
        data_second = create_task_schema_factory(user_id=user.id)

        # Act
        first = await repo.create(data_first)
        second = await repo.create(data_second)

        # Assert
        assert first.id != second.id

    async def test_create_loads_user_relationship(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that create() eagerly loads the user relationship."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.user is not None

    async def test_create_user_relationship_has_correct_id(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that the loaded user relationship has the correct ID."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert task_result.user.id == task_result.user_id == user.id

    async def test_create_user_relationship_is_correct_type(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that the user relationship is of correct schema type."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        task_result = await repo.create(task_data)

        # Assert
        assert isinstance(task_result.user, UserEntitySchema)

    async def test_create_task_is_retrievable_from_db(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_task_schema_factory: Callable[..., CreateTaskSchema],
    ) -> None:
        """Verify that created task can be retrieved via get_by_id()."""
        # Arrange
        repo = TaskRepository(db_client)
        task_data = create_task_schema_factory(user_id=user.id)

        # Act
        created = await repo.create(task_data)
        assert created.id is not None
        fetched = await repo.get_by_id(created.id)

        # Assert
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.type == created.type
        assert fetched.status == created.status


class TestTaskRepositoryGetById:
    """Tests for TaskRepository.get_by_id()."""

    async def test_get_by_id_returns_correct_task(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() retrieves the correct task by ID."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.get_by_id(task.id)

        # Assert
        assert task_result is not None
        assert task_result.id == task.id
        assert task_result.type == task.type
        assert task_result.status == task.status

    async def test_get_by_id_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_by_id() returns None for non-existent ID."""
        # Arrange
        repo = TaskRepository(db_client)

        # Act
        task_result = await repo.get_by_id(uuid.uuid4())

        # Assert
        assert task_result is None

    async def test_get_by_id_returns_task_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() returns TaskRelEntitySchema instance."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.get_by_id(task.id)

        # Assert
        assert isinstance(task_result, TaskRelEntitySchema)

    async def test_get_by_id_loads_user_relationship(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() eagerly loads the user relationship."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.get_by_id(task.id)

        # Assert
        assert task_result is not None
        assert task_result.user is not None

    async def test_get_by_id_user_relationship_has_correct_id(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that the loaded user relationship has the correct ID."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.get_by_id(task.id)

        # Assert
        assert task_result is not None
        assert task_result.user.id == task.user_id

    async def test_get_by_id_user_relationship_is_correct_type(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that the user relationship is of correct schema type."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.get_by_id(task.id)

        # Assert
        assert task_result is not None
        assert isinstance(task_result.user, UserEntitySchema)


class TestTaskRepositoryGetAll:
    """Tests for TaskRepository.get_all()."""

    async def test_get_all_returns_empty_list_when_no_tasks(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_all() returns empty list when no tasks exist."""
        # Arrange
        repo = TaskRepository(db_client)

        # Act
        task_result = await repo.get_all()

        # Assert
        assert task_result == []

    async def test_get_all_returns_all_created_tasks(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns all persisted tasks."""
        # Arrange
        repo = TaskRepository(db_client)
        await task_factory()
        await task_factory()
        await task_factory()

        # Act
        task_result = await repo.get_all()

        # Assert
        assert len(task_result) == 3

    async def test_get_all_returns_list_of_task_rel_entity_schemas(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns list of TaskRelEntitySchema instances."""
        # Arrange
        repo = TaskRepository(db_client)
        await task_factory()

        # Act
        task_result = await repo.get_all()

        # Assert
        assert all(isinstance(task, TaskRelEntitySchema) for task in task_result)

    async def test_get_all_limit_restricts_result_count(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the limit parameter."""
        # Arrange
        repo = TaskRepository(db_client)
        for _ in range(5):
            await task_factory()

        # Act
        task_result = await repo.get_all(limit=3)

        # Assert
        assert len(task_result) == 3

    async def test_get_all_offset_skips_records(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the offset parameter."""
        # Arrange
        repo = TaskRepository(db_client)
        for _ in range(4):
            await task_factory()

        # Act
        all_tasks = await repo.get_all(limit=100, offset=0)
        offset_tasks = await repo.get_all(limit=100, offset=2)

        # Assert
        assert len(offset_tasks) == len(all_tasks) - 2

    async def test_get_all_offset_returns_non_overlapping_pages(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_all() pagination returns non-overlapping results."""
        # Arrange
        repo = TaskRepository(db_client)
        for _ in range(4):
            await task_factory()

        # Act
        first_page = await repo.get_all(limit=2, offset=0)
        second_page = await repo.get_all(limit=2, offset=2)

        # Assert
        first_ids = {task.id for task in first_page}
        second_ids = {task.id for task in second_page}
        assert first_ids.isdisjoint(second_ids)

    async def test_get_all_tasks_have_loaded_user_relationships(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_all() eagerly loads user relationships for all tasks."""
        # Arrange
        repo = TaskRepository(db_client)
        await task_factory()
        await task_factory()

        # Act
        task_result = await repo.get_all()

        # Assert
        assert all(task.user for task in task_result)
        assert all(isinstance(task.user, UserEntitySchema) for task in task_result)


class TestTaskRepositoryGetCount:
    """Tests for TaskRepository.get_count()."""

    async def test_get_count_returns_zero_on_empty_table(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_count() returns 0 when no tasks exist."""
        # Arrange
        repo = TaskRepository(db_client)

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 0

    async def test_get_count_reflects_created_tasks(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_count() returns the correct number of tasks."""
        # Arrange
        repo = TaskRepository(db_client)
        await task_factory()
        await task_factory()

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 2

    async def test_get_count_decreases_after_delete(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_count() decreases after deleting a task."""
        # Arrange
        repo = TaskRepository(db_client)
        task = await task_factory()
        await task_factory()

        # Act
        await repo.delete_by_id(task.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_get_count_increments_with_each_create(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that get_count() increments correctly with each creation."""
        # Arrange
        repo = TaskRepository(db_client)

        # Act & Assert
        for expected in range(1, 4):
            await task_factory()
            assert await repo.get_count() == expected


class TestTaskRepositoryUpdateById:
    """Tests for TaskRepository.update_by_id()."""

    async def test_update_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that update_by_id() returns None for non-existent ID."""
        # Arrange
        repo = TaskRepository(db_client)
        update_data = UpdateTaskSchema(status=TaskStatus.COMPLETED)

        # Act
        task_result = await repo.update_by_id(uuid.uuid4(), update_data)

        # Assert
        assert task_result is None

    async def test_update_type(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates type field."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        new_type = TaskType.REPORT_GENERATION
        update_data = UpdateTaskSchema(type=new_type)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.type == new_type

    async def test_update_status(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates status field."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        new_status = TaskStatus.COMPLETED
        update_data = UpdateTaskSchema(status=new_status)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.status == new_status

    async def test_update_progress(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates progress field."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        new_progress = 0.75
        update_data = UpdateTaskSchema(progress=new_progress)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.progress == new_progress

    async def test_update_error_log(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates error_log field."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        new_error = "Database connection lost"
        update_data = UpdateTaskSchema(error_log=new_error)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.error_log == new_error

    async def test_update_input_params(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates input_params field."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        new_params = GeneratePersonasInputData(
            segment_name="updated_segment",
            segment_description="updated_description",
            person_count=10,
            interview_id=uuid.uuid4(),
        )
        update_data = UpdateTaskSchema(input_params=new_params.model_dump(mode="json"))

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.input_params == new_params

    async def test_update_does_not_change_unspecified_fields(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() only modifies specified fields."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        original_type = task.type
        original_user_id = task.user_id
        update_data = UpdateTaskSchema(status=TaskStatus.IN_PROGRESS)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.type == original_type
        assert task_result.user_id == original_user_id

    async def test_update_persists_to_database(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() changes are persisted to the database."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        update_data = UpdateTaskSchema(status=TaskStatus.FAILED)

        # Act
        await repo.update_by_id(task.id, update_data)
        fetched = await repo.get_by_id(task.id)

        # Assert
        assert fetched is not None
        assert fetched.status == TaskStatus.FAILED

    async def test_update_returns_task_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() returns TaskRelEntitySchema instance."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        update_data = UpdateTaskSchema(progress=1.0)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert isinstance(task_result, TaskRelEntitySchema)

    async def test_update_preserves_user_relationship(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() preserves the user relationship."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        update_data = UpdateTaskSchema(status=TaskStatus.COMPLETED)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.user is not None
        assert task_result.user.id == task.user_id
        assert isinstance(task_result.user, UserEntitySchema)

    async def test_update_does_not_change_id(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() does not modify the task ID."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None
        original_id = task.id
        update_data = UpdateTaskSchema(status=TaskStatus.CANCELLED)

        # Act
        task_result = await repo.update_by_id(task.id, update_data)

        # Assert
        assert task_result is not None
        assert task_result.id == original_id


class TestTaskRepositoryDeleteById:
    """Tests for TaskRepository.delete_by_id()."""

    async def test_delete_returns_deleted_id(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns the ID of the deleted task."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.delete_by_id(task.id)

        # Assert
        assert task_result == task.id

    async def test_delete_returns_uuid_type(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns a UUID type."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        task_result = await repo.delete_by_id(task.id)

        # Assert
        assert isinstance(task_result, uuid.UUID)

    async def test_delete_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that delete_by_id() returns None for non-existent ID."""
        # Arrange
        repo = TaskRepository(db_client)

        # Act
        task_result = await repo.delete_by_id(uuid.uuid4())

        # Assert
        assert task_result is None

    async def test_delete_removes_task_from_database(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() removes the task from the database."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        await repo.delete_by_id(task.id)
        fetched = await repo.get_by_id(task.id)

        # Assert
        assert fetched is None

    async def test_delete_does_not_affect_other_tasks(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() only deletes the specified task."""
        # Arrange
        repo = TaskRepository(db_client)
        to_delete = await task_factory()
        to_keep = await task_factory()
        assert to_delete.id is not None
        assert to_keep.id is not None

        # Act
        await repo.delete_by_id(to_delete.id)

        # Assert
        kept = await repo.get_by_id(to_keep.id)
        assert kept is not None
        assert kept.id == to_keep.id

    async def test_delete_decreases_count(
        self,
        db_client: DatabaseClient,
        task_factory: Callable[..., TaskRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() decreases the total task count."""
        # Arrange
        repo = TaskRepository(db_client)
        task1 = await task_factory()
        await task_factory()
        assert task1.id is not None

        # Act
        await repo.delete_by_id(task1.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_delete_is_idempotent_on_second_call(
        self,
        db_client: DatabaseClient,
        task: TaskRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() is idempotent (returns None on second call)."""
        # Arrange
        repo = TaskRepository(db_client)
        assert task.id is not None

        # Act
        await repo.delete_by_id(task.id)
        task_result = await repo.delete_by_id(task.id)

        # Assert
        assert task_result is None
