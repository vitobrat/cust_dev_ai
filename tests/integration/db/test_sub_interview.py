"""Integration tests for SubInterviewRepository.

Tests cover all CRUD operations with real PostgreSQL via testcontainers.
Each test runs in an isolated transaction that is rolled back after completion.
"""

import uuid
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.schemas.interview import (
    InterviewEntitySchema,
    InterviewRelEntitySchema,
)
from src.schemas.sub_interview import (
    CreateSubInterviewSchema,
    SubInterviewRelEntitySchema,
    UpdateSubInterviewSchema,
)


class TestSubInterviewRepositoryCreate:
    """Tests for SubInterviewRepository.create().

    All tests call the repository directly to verify DB behaviour.
    """

    async def test_create_returns_sub_interview_rel_entity_schema(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() returns SubInterviewRelEntitySchema instance."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert isinstance(sub_interview_result, SubInterviewRelEntitySchema)

    async def test_create_generates_uuid(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() generates a valid UUID for the new sub-interview."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.id is not None
        assert isinstance(sub_interview_result.id, uuid.UUID)

    async def test_create_persists_chat_history(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists the chat_history field."""
        # Arrange
        repo = SubInterviewRepository(session)
        chat_history = {"messages": [{"role": "user", "content": "Hello"}], "metadata": {"version": "1.0"}}
        sub_interview_data = create_sub_interview_schema_factory(
            interview_id=interview.id,
            chat_history=chat_history,
        )

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.chat_history == chat_history

    async def test_create_persists_status_pending(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists status=pending."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(
            interview_id=interview.id,
            status=SubInterviewStatus.PENDING,
        )

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.status == SubInterviewStatus.PENDING

    async def test_create_persists_status_completed(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists status=completed."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(
            interview_id=interview.id,
            status=SubInterviewStatus.COMPLETED,
        )

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.status == SubInterviewStatus.COMPLETED

    async def test_create_persists_status_failed(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() correctly persists status=failed."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(
            interview_id=interview.id,
            status=SubInterviewStatus.FAILED,
        )

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.status == SubInterviewStatus.FAILED

    async def test_create_generates_created_at_timestamp(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() automatically generates created_at timestamp."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.created_at is not None

    async def test_create_two_sub_interviews_have_different_ids(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that multiple create() calls generate unique IDs."""
        # Arrange
        repo = SubInterviewRepository(session)
        data_first = create_sub_interview_schema_factory(interview_id=interview.id)
        data_second = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        first = await repo.create(data_first)
        second = await repo.create(data_second)

        # Assert
        assert first.id != second.id

    async def test_create_loads_interview_relationship(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that create() eagerly loads the interview relationship."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.interview is not None

    async def test_create_interview_relationship_has_correct_id(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that the loaded interview relationship has the correct ID."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert sub_interview_result.interview.id == sub_interview_result.interview_id == interview.id

    async def test_create_interview_relationship_is_correct_type(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that the interview relationship is of correct schema type."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        sub_interview_result = await repo.create(sub_interview_data)

        # Assert
        assert isinstance(sub_interview_result.interview, InterviewEntitySchema)

    async def test_create_sub_interview_is_retrievable_from_db(
        self,
        session: AsyncSession,
        interview: InterviewRelEntitySchema,
        create_sub_interview_schema_factory: Callable[..., CreateSubInterviewSchema],
    ) -> None:
        """Verify that created sub-interview can be retrieved via get_by_id()."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview_data = create_sub_interview_schema_factory(interview_id=interview.id)

        # Act
        created = await repo.create(sub_interview_data)
        assert created.id is not None
        fetched = await repo.get_by_id(created.id)

        # Assert
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.chat_history == created.chat_history
        assert fetched.status == created.status


class TestSubInterviewRepositoryGetById:
    """Tests for SubInterviewRepository.get_by_id()."""

    async def test_get_by_id_returns_correct_sub_interview(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() retrieves the correct sub-interview by ID."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.get_by_id(sub_interview.id)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.id == sub_interview.id
        assert sub_interview_result.chat_history == sub_interview.chat_history
        assert sub_interview_result.status == sub_interview.status

    async def test_get_by_id_returns_none_for_nonexistent(
        self,
        session: AsyncSession,
    ) -> None:
        """Verify that get_by_id() returns None for non-existent ID."""
        # Arrange
        repo = SubInterviewRepository(session)

        # Act
        sub_interview_result = await repo.get_by_id(uuid.uuid4())

        # Assert
        assert sub_interview_result is None

    async def test_get_by_id_returns_sub_interview_rel_entity_schema(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() returns SubInterviewRelEntitySchema instance."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.get_by_id(sub_interview.id)

        # Assert
        assert isinstance(sub_interview_result, SubInterviewRelEntitySchema)

    async def test_get_by_id_loads_interview_relationship(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() eagerly loads the interview relationship."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.get_by_id(sub_interview.id)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.interview is not None

    async def test_get_by_id_interview_relationship_has_correct_id(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that the loaded interview relationship has the correct ID."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.get_by_id(sub_interview.id)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.interview.id == sub_interview.interview_id

    async def test_get_by_id_interview_relationship_is_correct_type(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that the interview relationship is of correct schema type."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.get_by_id(sub_interview.id)

        # Assert
        assert sub_interview_result is not None
        assert isinstance(sub_interview_result.interview, InterviewEntitySchema)


class TestSubInterviewRepositoryGetAll:
    """Tests for SubInterviewRepository.get_all()."""

    async def test_get_all_returns_empty_list_when_no_sub_interviews(
        self,
        session: AsyncSession,
    ) -> None:
        """Verify that get_all() returns empty list when no sub-interviews exist."""
        # Arrange
        repo = SubInterviewRepository(session)

        # Act
        sub_interview_result = await repo.get_all()

        # Assert
        assert sub_interview_result == []

    async def test_get_all_returns_all_created_sub_interviews(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns all persisted sub-interviews."""
        # Arrange
        repo = SubInterviewRepository(session)
        await sub_interview_factory()
        await sub_interview_factory()
        await sub_interview_factory()

        # Act
        sub_interview_result = await repo.get_all()

        # Assert
        assert len(sub_interview_result) == 3

    async def test_get_all_returns_list_of_sub_interview_rel_entity_schemas(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns list of SubInterviewRelEntitySchema instances."""
        # Arrange
        repo = SubInterviewRepository(session)
        await sub_interview_factory()

        # Act
        sub_interview_result = await repo.get_all()

        # Assert
        assert all(isinstance(sub_interview, SubInterviewRelEntitySchema) for sub_interview in sub_interview_result)

    async def test_get_all_limit_restricts_result_count(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the limit parameter."""
        # Arrange
        repo = SubInterviewRepository(session)
        for _ in range(5):
            await sub_interview_factory()

        # Act
        sub_interview_result = await repo.get_all(limit=3)

        # Assert
        assert len(sub_interview_result) == 3

    async def test_get_all_offset_skips_records(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the offset parameter."""
        # Arrange
        repo = SubInterviewRepository(session)
        for _ in range(4):
            await sub_interview_factory()

        # Act
        all_sub_interviews = await repo.get_all(limit=100, offset=0)
        offset_sub_interviews = await repo.get_all(limit=100, offset=2)

        # Assert
        assert len(offset_sub_interviews) == len(all_sub_interviews) - 2

    async def test_get_all_offset_returns_non_overlapping_pages(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() pagination returns non-overlapping results."""
        # Arrange
        repo = SubInterviewRepository(session)
        for _ in range(4):
            await sub_interview_factory()

        # Act
        first_page = await repo.get_all(limit=2, offset=0)
        second_page = await repo.get_all(limit=2, offset=2)

        # Assert
        first_ids = {sub_interview.id for sub_interview in first_page}
        second_ids = {sub_interview.id for sub_interview in second_page}
        assert first_ids.isdisjoint(second_ids)

    async def test_get_all_sub_interviews_have_loaded_interview_relationships(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_all() eagerly loads interview relationships for all sub-interviews."""
        # Arrange
        repo = SubInterviewRepository(session)
        await sub_interview_factory()
        await sub_interview_factory()

        # Act
        sub_interview_result = await repo.get_all()

        # Assert
        assert all(sub_interview.interview for sub_interview in sub_interview_result)
        assert all(isinstance(sub_interview.interview, InterviewEntitySchema) for sub_interview in sub_interview_result)


class TestSubInterviewRepositoryGetCount:
    """Tests for SubInterviewRepository.get_count()."""

    async def test_get_count_returns_zero_on_empty_table(
        self,
        session: AsyncSession,
    ) -> None:
        """Verify that get_count() returns 0 when no sub-interviews exist."""
        # Arrange
        repo = SubInterviewRepository(session)

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 0

    async def test_get_count_reflects_created_sub_interviews(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_count() returns the correct number of sub-interviews."""
        # Arrange
        repo = SubInterviewRepository(session)
        await sub_interview_factory()
        await sub_interview_factory()

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 2

    async def test_get_count_decreases_after_delete(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_count() decreases after deleting a sub-interview."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview = await sub_interview_factory()
        await sub_interview_factory()

        # Act
        await repo.delete_by_id(sub_interview.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_get_count_increments_with_each_create(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that get_count() increments correctly with each creation."""
        # Arrange
        repo = SubInterviewRepository(session)

        # Act & Assert
        for expected in range(1, 4):
            await sub_interview_factory()
            assert await repo.get_count() == expected


class TestSubInterviewRepositoryUpdateById:
    """Tests for SubInterviewRepository.update_by_id()."""

    async def test_update_returns_none_for_nonexistent(
        self,
        session: AsyncSession,
    ) -> None:
        """Verify that update_by_id() returns None for non-existent ID."""
        # Arrange
        repo = SubInterviewRepository(session)
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        sub_interview_result = await repo.update_by_id(uuid.uuid4(), update_data)

        # Assert
        assert sub_interview_result is None

    async def test_update_chat_history(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates chat_history field."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None
        new_chat_history = {"messages": [{"role": "assistant", "content": "Updated message"}]}
        update_data = UpdateSubInterviewSchema(chat_history=new_chat_history)

        # Act
        sub_interview_result = await repo.update_by_id(sub_interview.id, update_data)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.chat_history == new_chat_history

    async def test_update_status_to_completed(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that update_by_id() can change status to completed."""
        # Arrange
        repo = SubInterviewRepository(session)
        pending_sub_interview = await sub_interview_factory(status=SubInterviewStatus.PENDING)
        assert pending_sub_interview.id is not None
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        sub_interview_result = await repo.update_by_id(pending_sub_interview.id, update_data)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.status == SubInterviewStatus.COMPLETED

    async def test_update_status_to_failed(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that update_by_id() can change status to failed."""
        # Arrange
        repo = SubInterviewRepository(session)
        generating_sub_interview = await sub_interview_factory(status=SubInterviewStatus.GENERATING)
        assert generating_sub_interview.id is not None
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.FAILED)

        # Act
        sub_interview_result = await repo.update_by_id(generating_sub_interview.id, update_data)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.status == SubInterviewStatus.FAILED

    async def test_update_does_not_change_unspecified_fields(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() only modifies specified fields."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None
        original_chat_history = sub_interview.chat_history
        original_interview_id = sub_interview.interview_id
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        sub_interview_result = await repo.update_by_id(sub_interview.id, update_data)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.chat_history == original_chat_history
        assert sub_interview_result.interview_id == original_interview_id

    async def test_update_persists_to_database(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() changes are persisted to the database."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        await repo.update_by_id(sub_interview.id, update_data)
        fetched = await repo.get_by_id(sub_interview.id)

        # Assert
        assert fetched is not None
        assert fetched.status == SubInterviewStatus.COMPLETED

    async def test_update_returns_sub_interview_rel_entity_schema(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() returns SubInterviewRelEntitySchema instance."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        sub_interview_result = await repo.update_by_id(sub_interview.id, update_data)

        # Assert
        assert isinstance(sub_interview_result, SubInterviewRelEntitySchema)

    async def test_update_preserves_interview_relationship(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() preserves the interview relationship."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        sub_interview_result = await repo.update_by_id(sub_interview.id, update_data)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.interview is not None
        assert sub_interview_result.interview.id == sub_interview.interview_id
        assert isinstance(sub_interview_result.interview, InterviewEntitySchema)

    async def test_update_does_not_change_id(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() does not modify the sub-interview ID."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None
        original_id = sub_interview.id
        update_data = UpdateSubInterviewSchema(status=SubInterviewStatus.COMPLETED)

        # Act
        sub_interview_result = await repo.update_by_id(sub_interview.id, update_data)

        # Assert
        assert sub_interview_result is not None
        assert sub_interview_result.id == original_id


class TestSubInterviewRepositoryDeleteById:
    """Tests for SubInterviewRepository.delete_by_id()."""

    async def test_delete_returns_deleted_id(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns the ID of the deleted sub-interview."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.delete_by_id(sub_interview.id)

        # Assert
        assert sub_interview_result == sub_interview.id

    async def test_delete_returns_uuid_type(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns a UUID type."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        sub_interview_result = await repo.delete_by_id(sub_interview.id)

        # Assert
        assert isinstance(sub_interview_result, uuid.UUID)

    async def test_delete_returns_none_for_nonexistent(
        self,
        session: AsyncSession,
    ) -> None:
        """Verify that delete_by_id() returns None for non-existent ID."""
        # Arrange
        repo = SubInterviewRepository(session)

        # Act
        sub_interview_result = await repo.delete_by_id(uuid.uuid4())

        # Assert
        assert sub_interview_result is None

    async def test_delete_removes_sub_interview_from_database(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() removes the sub-interview from the database."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        await repo.delete_by_id(sub_interview.id)
        fetched = await repo.get_by_id(sub_interview.id)

        # Assert
        assert fetched is None

    async def test_delete_does_not_affect_other_sub_interviews(
        self,
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() only deletes the specified sub-interview."""
        # Arrange
        repo = SubInterviewRepository(session)
        to_delete = await sub_interview_factory()
        to_keep = await sub_interview_factory()
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
        session: AsyncSession,
        sub_interview_factory: Callable[..., SubInterviewRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() decreases the total sub-interview count."""
        # Arrange
        repo = SubInterviewRepository(session)
        sub_interview1 = await sub_interview_factory()
        await sub_interview_factory()
        assert sub_interview1.id is not None

        # Act
        await repo.delete_by_id(sub_interview1.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_delete_is_idempotent_on_second_call(
        self,
        session: AsyncSession,
        sub_interview: SubInterviewRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() is idempotent (returns None on second call)."""
        # Arrange
        repo = SubInterviewRepository(session)
        assert sub_interview.id is not None

        # Act
        await repo.delete_by_id(sub_interview.id)
        sub_interview_result = await repo.delete_by_id(sub_interview.id)

        # Assert
        assert sub_interview_result is None
