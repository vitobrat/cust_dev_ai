"""Integration tests for UserRepository.

Tests cover all CRUD operations with real PostgreSQL via testcontainers.
Each test runs in an isolated transaction that is rolled back after completion.
"""

import uuid
from collections.abc import Callable

from src.domains.user.db.postgres.repository import UserRepository
from src.infrastructure.db.postgres.client import DatabaseClient
from src.schemas.user import (
    CreateUserSchema,
    UpdateUserSchema,
    UserRelEntitySchema,
)


class TestUserRepositoryCreate:
    """Tests for UserRepository.create().

    All tests call the repository directly to verify DB behaviour.
    """

    async def test_create_returns_user_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that create() returns UserRelEntitySchema instance."""
        # Arrange
        repo = UserRepository(db_client)
        user_data = create_user_schema_factory()

        # Act
        user_result = await repo.create(user_data)

        # Assert
        assert isinstance(user_result, UserRelEntitySchema)

    async def test_create_generates_uuid(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that create() generates a valid UUID for the new user."""
        # Arrange
        repo = UserRepository(db_client)
        user_data = create_user_schema_factory()

        # Act
        user_result = await repo.create(user_data)

        # Assert
        assert user_result.id is not None
        assert isinstance(user_result.id, uuid.UUID)

    async def test_create_persists_name(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that create() correctly persists the name field."""
        # Arrange
        repo = UserRepository(db_client)
        name = "John Doe"
        user_data = create_user_schema_factory(name=name)

        # Act
        user_result = await repo.create(user_data)

        # Assert
        assert user_result.name == name

    async def test_create_two_users_have_different_ids(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that multiple create() calls generate unique IDs."""
        # Arrange
        repo = UserRepository(db_client)
        data_first = create_user_schema_factory()
        data_second = create_user_schema_factory()

        # Act
        first = await repo.create(data_first)
        second = await repo.create(data_second)

        # Assert
        assert first.id != second.id

    async def test_create_initializes_empty_interviews_list(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that create() initializes empty interviews relationship list."""
        # Arrange
        repo = UserRepository(db_client)
        user_data = create_user_schema_factory()

        # Act
        user_result = await repo.create(user_data)

        # Assert
        assert user_result.interviews == []

    async def test_create_initializes_empty_tasks_list(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that create() initializes empty tasks relationship list."""
        # Arrange
        repo = UserRepository(db_client)
        user_data = create_user_schema_factory()

        # Act
        user_result = await repo.create(user_data)

        # Assert
        assert user_result.tasks == []

    async def test_create_user_is_retrievable_from_db(
        self,
        db_client: DatabaseClient,
        create_user_schema_factory: Callable[..., CreateUserSchema],
    ) -> None:
        """Verify that created user can be retrieved via get_by_id()."""
        # Arrange
        repo = UserRepository(db_client)
        user_data = create_user_schema_factory()

        # Act
        created = await repo.create(user_data)
        assert created.id is not None
        fetched = await repo.get_by_id(created.id)

        # Assert
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name


class TestUserRepositoryGetById:
    """Tests for UserRepository.get_by_id()."""

    async def test_get_by_id_returns_correct_user(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() retrieves the correct user by ID."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        user_result = await repo.get_by_id(user.id)

        # Assert
        assert user_result is not None
        assert user_result.id == user.id
        assert user_result.name == user.name

    async def test_get_by_id_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_by_id() returns None for non-existent ID."""
        # Arrange
        repo = UserRepository(db_client)

        # Act
        user_result = await repo.get_by_id(uuid.uuid4())

        # Assert
        assert user_result is None

    async def test_get_by_id_returns_user_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() returns UserRelEntitySchema instance."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        user_result = await repo.get_by_id(user.id)

        # Assert
        assert isinstance(user_result, UserRelEntitySchema)

    async def test_get_by_id_loads_interviews_relationship(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() loads the interviews relationship."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        user_result = await repo.get_by_id(user.id)

        # Assert
        assert user_result is not None
        assert user_result.interviews is not None
        assert isinstance(user_result.interviews, list)

    async def test_get_by_id_loads_tasks_relationship(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() loads the tasks relationship."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        user_result = await repo.get_by_id(user.id)

        # Assert
        assert user_result is not None
        assert user_result.tasks is not None
        assert isinstance(user_result.tasks, list)


class TestUserRepositoryGetAll:
    """Tests for UserRepository.get_all()."""

    async def test_get_all_returns_empty_list_when_no_users(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_all() returns empty list when no users exist."""
        # Arrange
        repo = UserRepository(db_client)

        # Act
        user_result = await repo.get_all()

        # Assert
        assert user_result == []

    async def test_get_all_returns_all_created_users(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns all persisted users."""
        # Arrange
        repo = UserRepository(db_client)
        await user_factory()
        await user_factory()
        await user_factory()

        # Act
        user_result = await repo.get_all()

        # Assert
        assert len(user_result) == 3

    async def test_get_all_returns_list_of_user_rel_entity_schemas(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns list of UserRelEntitySchema instances."""
        # Arrange
        repo = UserRepository(db_client)
        await user_factory()

        # Act
        user_result = await repo.get_all()

        # Assert
        assert all(isinstance(user, UserRelEntitySchema) for user in user_result)

    async def test_get_all_limit_restricts_result_count(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the limit parameter."""
        # Arrange
        repo = UserRepository(db_client)
        for _ in range(5):
            await user_factory()

        # Act
        user_result = await repo.get_all(limit=3)

        # Assert
        assert len(user_result) == 3

    async def test_get_all_offset_skips_records(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the offset parameter."""
        # Arrange
        repo = UserRepository(db_client)
        for _ in range(4):
            await user_factory()

        # Act
        all_users = await repo.get_all(limit=100, offset=0)
        offset_users = await repo.get_all(limit=100, offset=2)

        # Assert
        assert len(offset_users) == len(all_users) - 2

    async def test_get_all_offset_returns_non_overlapping_pages(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_all() pagination returns non-overlapping results."""
        # Arrange
        repo = UserRepository(db_client)
        for _ in range(4):
            await user_factory()

        # Act
        first_page = await repo.get_all(limit=2, offset=0)
        second_page = await repo.get_all(limit=2, offset=2)

        # Assert
        first_ids = {user.id for user in first_page}
        second_ids = {user.id for user in second_page}
        assert first_ids.isdisjoint(second_ids)

    async def test_get_all_users_have_loaded_relationships(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_all() loads relationships for all users."""
        # Arrange
        repo = UserRepository(db_client)
        await user_factory()
        await user_factory()

        # Act
        user_result = await repo.get_all()

        # Assert
        assert all(user.interviews is not None for user in user_result)
        assert all(user.tasks is not None for user in user_result)
        assert all(isinstance(user.interviews, list) for user in user_result)
        assert all(isinstance(user.tasks, list) for user in user_result)


class TestUserRepositoryGetCount:
    """Tests for UserRepository.get_count()."""

    async def test_get_count_returns_zero_on_empty_table(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_count() returns 0 when no users exist."""
        # Arrange
        repo = UserRepository(db_client)

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 0

    async def test_get_count_reflects_created_users(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_count() returns the correct number of users."""
        # Arrange
        repo = UserRepository(db_client)
        await user_factory()
        await user_factory()

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 2

    async def test_get_count_decreases_after_delete(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_count() decreases after deleting a user."""
        # Arrange
        repo = UserRepository(db_client)
        user = await user_factory()
        await user_factory()

        # Act
        await repo.delete_by_id(user.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_get_count_increments_with_each_create(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that get_count() increments correctly with each creation."""
        # Arrange
        repo = UserRepository(db_client)

        # Act & Assert
        for expected in range(1, 4):
            await user_factory()
            assert await repo.get_count() == expected


class TestUserRepositoryUpdateById:
    """Tests for UserRepository.update_by_id()."""

    async def test_update_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that update_by_id() returns None for non-existent ID."""
        # Arrange
        repo = UserRepository(db_client)
        update_data = UpdateUserSchema(name="New Name")

        # Act
        user_result = await repo.update_by_id(uuid.uuid4(), update_data)

        # Assert
        assert user_result is None

    async def test_update_name(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates name field."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None
        new_name = "Updated User Name"
        update_data = UpdateUserSchema(name=new_name)

        # Act
        user_result = await repo.update_by_id(user.id, update_data)

        # Assert
        assert user_result is not None
        assert user_result.name == new_name

    async def test_update_persists_to_database(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() changes are persisted to the database."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None
        update_data = UpdateUserSchema(name="Persisted change")

        # Act
        await repo.update_by_id(user.id, update_data)
        fetched = await repo.get_by_id(user.id)

        # Assert
        assert fetched is not None
        assert fetched.name == "Persisted change"

    async def test_update_returns_user_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() returns UserRelEntitySchema instance."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None
        update_data = UpdateUserSchema(name="Type check")

        # Act
        user_result = await repo.update_by_id(user.id, update_data)

        # Assert
        assert isinstance(user_result, UserRelEntitySchema)

    async def test_update_preserves_relationships(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() preserves relationships."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None
        update_data = UpdateUserSchema(name="Relationship check")

        # Act
        user_result = await repo.update_by_id(user.id, update_data)

        # Assert
        assert user_result is not None
        assert user_result.interviews is not None
        assert user_result.tasks is not None
        assert isinstance(user_result.interviews, list)
        assert isinstance(user_result.tasks, list)

    async def test_update_does_not_change_id(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() does not modify the user ID."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None
        original_id = user.id
        update_data = UpdateUserSchema(name="ID must not change")

        # Act
        user_result = await repo.update_by_id(user.id, update_data)

        # Assert
        assert user_result is not None
        assert user_result.id == original_id

    async def test_update_with_empty_schema_returns_unchanged_user(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() with empty schema returns unchanged user."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None
        original_name = user.name
        update_data = UpdateUserSchema()

        # Act
        user_result = await repo.update_by_id(user.id, update_data)

        # Assert
        assert user_result is not None
        assert user_result.name == original_name


class TestUserRepositoryDeleteById:
    """Tests for UserRepository.delete_by_id()."""

    async def test_delete_returns_deleted_id(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns the ID of the deleted user."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        user_result = await repo.delete_by_id(user.id)

        # Assert
        assert user_result == user.id

    async def test_delete_returns_uuid_type(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns a UUID type."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        user_result = await repo.delete_by_id(user.id)

        # Assert
        assert isinstance(user_result, uuid.UUID)

    async def test_delete_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that delete_by_id() returns None for non-existent ID."""
        # Arrange
        repo = UserRepository(db_client)

        # Act
        user_result = await repo.delete_by_id(uuid.uuid4())

        # Assert
        assert user_result is None

    async def test_delete_removes_user_from_database(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() removes the user from the database."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        await repo.delete_by_id(user.id)
        fetched = await repo.get_by_id(user.id)

        # Assert
        assert fetched is None

    async def test_delete_does_not_affect_other_users(
        self,
        db_client: DatabaseClient,
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() only deletes the specified user."""
        # Arrange
        repo = UserRepository(db_client)
        to_delete = await user_factory()
        to_keep = await user_factory()
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
        user_factory: Callable[..., UserRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() decreases the total user count."""
        # Arrange
        repo = UserRepository(db_client)
        user1 = await user_factory()
        await user_factory()
        assert user1.id is not None

        # Act
        await repo.delete_by_id(user1.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_delete_is_idempotent_on_second_call(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() is idempotent (returns None on second call)."""
        # Arrange
        repo = UserRepository(db_client)
        assert user.id is not None

        # Act
        await repo.delete_by_id(user.id)
        user_result = await repo.delete_by_id(user.id)

        # Assert
        assert user_result is None
