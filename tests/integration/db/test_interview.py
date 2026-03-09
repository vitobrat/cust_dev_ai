"""Integration tests for InterviewRepository.

Tests cover all CRUD operations with real PostgreSQL via testcontainers.
Each test runs in an isolated transaction that is rolled back after completion.
"""

import uuid
from collections.abc import Callable

from src.domains.interview.db.postgres.repository import InterviewRepository
from src.infrastructure.db.postgres.client import DatabaseClient
from src.schemas.interview import (
    CreateInterviewSchema,
    InterviewRelEntitySchema,
    UpdateInterviewSchema,
)
from src.schemas.user import UserEntitySchema, UserRelEntitySchema


class TestInterviewRepositoryCreate:
    """Tests for InterviewRepository.create().

    All tests call the repository directly to verify DB behaviour.
    """

    async def test_create_returns_interview_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() returns InterviewRelEntitySchema instance."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert isinstance(interview_result, InterviewRelEntitySchema)

    async def test_create_generates_uuid(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() generates a valid UUID for the new interview."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.id is not None
        assert isinstance(interview_result.id, uuid.UUID)

    async def test_create_persists_report_content_url(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists the report_content_url field."""
        # Arrange
        repo = InterviewRepository(db_client)
        report_url = "https://example.com/reports/interview-123.pdf"
        interview_data = create_interview_schema_factory(
            user_id=user.id,
            report_content_url=report_url,
        )

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.report_content_url == report_url

    async def test_create_persists_none_report_content_url(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists None for report_content_url."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(
            user_id=user.id,
            report_content_url=None,
        )

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.report_content_url is None

    async def test_create_persists_user_id(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists user_id field."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.user_id == user.id

    async def test_create_generates_created_at_timestamp(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() automatically generates created_at timestamp."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.created_at is not None

    async def test_create_generates_updated_at_timestamp(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() automatically generates updated_at timestamp."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.updated_at is not None

    async def test_create_two_interviews_have_different_ids(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that multiple create() calls generate unique IDs."""
        # Arrange
        repo = InterviewRepository(db_client)
        data_first = create_interview_schema_factory(user_id=user.id)
        data_second = create_interview_schema_factory(user_id=user.id)

        # Act
        first = await repo.create(data_first)
        second = await repo.create(data_second)

        # Assert
        assert first.id != second.id

    async def test_create_loads_user_relationship(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() eagerly loads the user relationship."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.user is not None

    async def test_create_user_relationship_has_correct_id(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that the loaded user relationship has the correct ID."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.user.id == interview_result.user_id == user.id

    async def test_create_user_relationship_is_correct_type(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that the user relationship is of correct schema type."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert isinstance(interview_result.user, UserEntitySchema)

    async def test_create_interview_is_retrievable_from_db(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that created interview can be retrieved via get_by_id()."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        created = await repo.create(interview_data)
        assert created.id is not None
        fetched = await repo.get_by_id(created.id)

        # Assert
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.report_content_url == created.report_content_url

    async def test_create_initializes_empty_personas_list(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() initializes empty personas list."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.personas == []

    async def test_create_initializes_empty_sub_interviews_list(
        self,
        db_client: DatabaseClient,
        user: UserRelEntitySchema,
        create_interview_schema_factory: Callable[..., CreateInterviewSchema],
    ) -> None:
        """Verify that create() initializes empty sub_interviews list."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview_data = create_interview_schema_factory(user_id=user.id)

        # Act
        interview_result = await repo.create(interview_data)

        # Assert
        assert interview_result.sub_interviews == []


class TestInterviewRepositoryGetById:
    """Tests for InterviewRepository.get_by_id()."""

    async def test_get_by_id_returns_correct_interview(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() retrieves the correct interview by ID."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert interview_result is not None
        assert interview_result.id == interview.id
        assert interview_result.report_content_url == interview.report_content_url

    async def test_get_by_id_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_by_id() returns None for non-existent ID."""
        # Arrange
        repo = InterviewRepository(db_client)

        # Act
        interview_result = await repo.get_by_id(uuid.uuid4())

        # Assert
        assert interview_result is None

    async def test_get_by_id_returns_interview_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() returns InterviewRelEntitySchema instance."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert isinstance(interview_result, InterviewRelEntitySchema)

    async def test_get_by_id_loads_user_relationship(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() eagerly loads the user relationship."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert interview_result is not None
        assert interview_result.user is not None

    async def test_get_by_id_user_relationship_has_correct_id(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that the loaded user relationship has the correct ID."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert interview_result is not None
        assert interview_result.user.id == interview.user_id

    async def test_get_by_id_user_relationship_is_correct_type(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that the user relationship is of correct schema type."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert interview_result is not None
        assert isinstance(interview_result.user, UserEntitySchema)

    async def test_get_by_id_loads_personas_relationship(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() loads the personas relationship."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert interview_result is not None
        assert interview_result.personas is not None
        assert isinstance(interview_result.personas, list)

    async def test_get_by_id_loads_sub_interviews_relationship(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() loads the sub_interviews relationship."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.get_by_id(interview.id)

        # Assert
        assert interview_result is not None
        assert interview_result.sub_interviews is not None
        assert isinstance(interview_result.sub_interviews, list)


class TestInterviewRepositoryGetAll:
    """Tests for InterviewRepository.get_all()."""

    async def test_get_all_returns_empty_list_when_no_interviews(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_all() returns empty list when no interviews exist."""
        # Arrange
        repo = InterviewRepository(db_client)

        # Act
        interview_result = await repo.get_all()

        # Assert
        assert interview_result == []

    async def test_get_all_returns_all_created_interviews(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns all persisted interviews."""
        # Arrange
        repo = InterviewRepository(db_client)
        await interview_factory()
        await interview_factory()
        await interview_factory()

        # Act
        interview_result = await repo.get_all()

        # Assert
        assert len(interview_result) == 3

    async def test_get_all_returns_list_of_interview_rel_entity_schemas(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns list of InterviewRelEntitySchema instances."""
        # Arrange
        repo = InterviewRepository(db_client)
        await interview_factory()

        # Act
        interview_result = await repo.get_all()

        # Assert
        assert all(isinstance(interview, InterviewRelEntitySchema) for interview in interview_result)

    async def test_get_all_limit_restricts_result_count(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the limit parameter."""
        # Arrange
        repo = InterviewRepository(db_client)
        for _ in range(5):
            await interview_factory()

        # Act
        interview_result = await repo.get_all(limit=3)

        # Assert
        assert len(interview_result) == 3

    async def test_get_all_offset_skips_records(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the offset parameter."""
        # Arrange
        repo = InterviewRepository(db_client)
        for _ in range(4):
            await interview_factory()

        # Act
        all_interviews = await repo.get_all(limit=100, offset=0)
        offset_interviews = await repo.get_all(limit=100, offset=2)

        # Assert
        assert len(offset_interviews) == len(all_interviews) - 2

    async def test_get_all_offset_returns_non_overlapping_pages(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() pagination returns non-overlapping results."""
        # Arrange
        repo = InterviewRepository(db_client)
        for _ in range(4):
            await interview_factory()

        # Act
        first_page = await repo.get_all(limit=2, offset=0)
        second_page = await repo.get_all(limit=2, offset=2)

        # Assert
        first_ids = {interview.id for interview in first_page}
        second_ids = {interview.id for interview in second_page}
        assert first_ids.isdisjoint(second_ids)

    async def test_get_all_interviews_have_loaded_user_relationships(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() eagerly loads user relationships for all interviews."""
        # Arrange
        repo = InterviewRepository(db_client)
        await interview_factory()
        await interview_factory()

        # Act
        interview_result = await repo.get_all()

        # Assert
        assert all(interview.user for interview in interview_result)
        assert all(isinstance(interview.user, UserEntitySchema) for interview in interview_result)


class TestInterviewRepositoryGetCount:
    """Tests for InterviewRepository.get_count()."""

    async def test_get_count_returns_zero_on_empty_table(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_count() returns 0 when no interviews exist."""
        # Arrange
        repo = InterviewRepository(db_client)

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 0

    async def test_get_count_reflects_created_interviews(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_count() returns the correct number of interviews."""
        # Arrange
        repo = InterviewRepository(db_client)
        await interview_factory()
        await interview_factory()

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 2

    async def test_get_count_decreases_after_delete(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_count() decreases after deleting an interview."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview = await interview_factory()
        await interview_factory()

        # Act
        await repo.delete_by_id(interview.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_get_count_increments_with_each_create(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that get_count() increments correctly with each creation."""
        # Arrange
        repo = InterviewRepository(db_client)

        # Act & Assert
        for expected in range(1, 4):
            await interview_factory()
            assert await repo.get_count() == expected


class TestInterviewRepositoryUpdateById:
    """Tests for InterviewRepository.update_by_id()."""

    async def test_update_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that update_by_id() returns None for non-existent ID."""
        # Arrange
        repo = InterviewRepository(db_client)
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/new-report.pdf")

        # Act
        interview_result = await repo.update_by_id(uuid.uuid4(), update_data)

        # Assert
        assert interview_result is None

    async def test_update_report_content_url(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates report_content_url field."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        new_url = "https://example.com/updated-report.pdf"
        update_data = UpdateInterviewSchema(report_content_url=new_url)

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert interview_result is not None
        assert interview_result.report_content_url == new_url

    async def test_update_report_content_url_to_none(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that update_by_id() can set report_content_url to None."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview = await interview_factory(report_content_url="https://example.com/report.pdf")
        assert interview.id is not None
        update_data = UpdateInterviewSchema(report_content_url=None)

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert interview_result is not None
        assert interview_result.report_content_url is None

    async def test_update_does_not_change_unspecified_fields(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() only modifies specified fields."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        original_user_id = interview.user_id
        original_created_at = interview.created_at
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/new.pdf")

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert interview_result is not None
        assert interview_result.user_id == original_user_id
        assert interview_result.created_at == original_created_at

    async def test_update_persists_to_database(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() changes are persisted to the database."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/persisted.pdf")

        # Act
        await repo.update_by_id(interview.id, update_data)
        fetched = await repo.get_by_id(interview.id)

        # Assert
        assert fetched is not None
        assert fetched.report_content_url == "https://example.com/persisted.pdf"

    async def test_update_returns_interview_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() returns InterviewRelEntitySchema instance."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/type-check.pdf")

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert isinstance(interview_result, InterviewRelEntitySchema)

    async def test_update_preserves_user_relationship(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() preserves the user relationship."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/relationship.pdf")

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert interview_result is not None
        assert interview_result.user is not None
        assert interview_result.user.id == interview.user_id
        assert isinstance(interview_result.user, UserEntitySchema)

    async def test_update_does_not_change_id(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() does not modify the interview ID."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        original_id = interview.id
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/id-check.pdf")

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert interview_result is not None
        assert interview_result.id == original_id

    async def test_update_changes_updated_at_timestamp(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() updates the updated_at timestamp."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None
        original_updated_at = interview.updated_at
        update_data = UpdateInterviewSchema(report_content_url="https://example.com/timestamp.pdf")

        # Act
        interview_result = await repo.update_by_id(interview.id, update_data)

        # Assert
        assert interview_result is not None
        assert interview_result.updated_at >= original_updated_at


class TestInterviewRepositoryDeleteById:
    """Tests for InterviewRepository.delete_by_id()."""

    async def test_delete_returns_deleted_id(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns the ID of the deleted interview."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.delete_by_id(interview.id)

        # Assert
        assert interview_result == interview.id

    async def test_delete_returns_uuid_type(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns a UUID type."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        interview_result = await repo.delete_by_id(interview.id)

        # Assert
        assert isinstance(interview_result, uuid.UUID)

    async def test_delete_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that delete_by_id() returns None for non-existent ID."""
        # Arrange
        repo = InterviewRepository(db_client)

        # Act
        interview_result = await repo.delete_by_id(uuid.uuid4())

        # Assert
        assert interview_result is None

    async def test_delete_removes_interview_from_database(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() removes the interview from the database."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        await repo.delete_by_id(interview.id)
        fetched = await repo.get_by_id(interview.id)

        # Assert
        assert fetched is None

    async def test_delete_does_not_affect_other_interviews(
        self,
        db_client: DatabaseClient,
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() only deletes the specified interview."""
        # Arrange
        repo = InterviewRepository(db_client)
        to_delete = await interview_factory()
        to_keep = await interview_factory()
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
        interview_factory: Callable[..., InterviewRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() decreases the total interview count."""
        # Arrange
        repo = InterviewRepository(db_client)
        interview1 = await interview_factory()
        await interview_factory()
        assert interview1.id is not None

        # Act
        await repo.delete_by_id(interview1.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_delete_is_idempotent_on_second_call(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() is idempotent (returns None on second call)."""
        # Arrange
        repo = InterviewRepository(db_client)
        assert interview.id is not None

        # Act
        await repo.delete_by_id(interview.id)
        interview_result = await repo.delete_by_id(interview.id)

        # Assert
        assert interview_result is None
