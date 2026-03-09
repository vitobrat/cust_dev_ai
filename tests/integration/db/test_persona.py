"""Integration tests for PersonaRepository.

Tests cover all CRUD operations with real PostgreSQL via testcontainers.
Each test runs in an isolated transaction that is rolled back after completion.
"""

import uuid
from collections.abc import Callable

from src.domains.persona.db.postgres.repository import PersonaRepository
from src.infrastructure.db.postgres.client import DatabaseClient
from src.schemas.interview import (
    InterviewEntitySchema,
    InterviewRelEntitySchema,
)
from src.schemas.persona import (
    CreatePersonaSchema,
    PersonaRelEntitySchema,
    UpdatePersonasSchema,
)


class TestPersonaRepositoryCreate:
    """Tests for PersonaRepository.create().

    All tests call the repository directly to verify DB behaviour.
    """

    async def test_create_returns_persona_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() returns PersonaRelEntitySchema instance."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert isinstance(persona_result, PersonaRelEntitySchema)

    async def test_create_generates_uuid(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() generates a valid UUID for the new persona."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.id is not None
        assert isinstance(persona_result.id, uuid.UUID)

    async def test_create_persists_bio_description(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() correctly persists the bio_description field."""
        # Arrange
        repo = PersonaRepository(db_client)
        bio = "Senior backend engineer with 10 years of experience"
        persona_data = create_persona_schema_factory(interview_id=interview.id, bio_description=bio)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.bio_description == bio

    async def test_create_persists_is_verified_true(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() correctly persists is_verified=True."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id, is_verified=True)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.is_verified is True

    async def test_create_persists_is_verified_false(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() correctly persists is_verified=False (default)."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.is_verified is False

    async def test_create_persists_demographic_state(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() correctly persists demographic_state field."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.demographic_state is not None
        assert persona_result.demographic_state == persona_data.demographic_state

    async def test_create_generates_created_at_timestamp(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() automatically generates created_at timestamp."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.created_at is not None

    async def test_create_generates_updated_at_timestamp(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() automatically generates updated_at timestamp."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.updated_at is not None

    async def test_create_two_personas_have_different_ids(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that multiple create() calls generate unique IDs."""
        # Arrange
        repo = PersonaRepository(db_client)
        data_first = create_persona_schema_factory(interview_id=interview.id)
        data_second = create_persona_schema_factory(interview_id=interview.id)

        # Act
        first = await repo.create(data_first)
        second = await repo.create(data_second)

        # Assert
        assert first.id != second.id

    async def test_create_loads_interview_relationship(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that create() eagerly loads the interview relationship."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.interview is not None

    async def test_create_interview_relationship_has_correct_id(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that the loaded interview relationship has the correct ID."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert persona_result.interview.id == persona_result.interview_id == interview.id

    async def test_create_interview_relationship_is_correct_type(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that the interview relationship is of correct schema type."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        persona_result = await repo.create(persona_data)

        # Assert
        assert isinstance(persona_result.interview, InterviewEntitySchema)

    async def test_create_persona_is_retrievable_from_db(
        self,
        db_client: DatabaseClient,
        interview: InterviewRelEntitySchema,
        create_persona_schema_factory: Callable[..., CreatePersonaSchema],
    ) -> None:
        """Verify that created persona can be retrieved via get_by_id()."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona_data = create_persona_schema_factory(interview_id=interview.id)

        # Act
        created = await repo.create(persona_data)
        assert created.id is not None
        fetched = await repo.get_by_id(created.id)

        # Assert
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.bio_description == created.bio_description


class TestPersonaRepositoryGetById:
    """Tests for PersonaRepository.get_by_id()."""

    async def test_get_by_id_returns_correct_persona(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() retrieves the correct persona by ID."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.get_by_id(persona.id)

        # Assert
        assert persona_result is not None
        assert persona_result.id == persona.id
        assert persona_result.bio_description == persona.bio_description

    async def test_get_by_id_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_by_id() returns None for non-existent ID."""
        # Arrange
        repo = PersonaRepository(db_client)

        # Act
        persona_result = await repo.get_by_id(uuid.uuid4())

        # Assert
        assert persona_result is None

    async def test_get_by_id_returns_persona_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() returns PersonaRelEntitySchema instance."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.get_by_id(persona.id)

        # Assert
        assert isinstance(persona_result, PersonaRelEntitySchema)

    async def test_get_by_id_loads_interview_relationship(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that get_by_id() eagerly loads the interview relationship."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.get_by_id(persona.id)

        # Assert
        assert persona_result is not None
        assert persona_result.interview is not None

    async def test_get_by_id_interview_relationship_has_correct_id(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that the loaded interview relationship has the correct ID."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.get_by_id(persona.id)

        # Assert
        assert persona_result is not None
        assert persona_result.interview.id == persona.interview_id

    async def test_get_by_id_interview_relationship_is_correct_type(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that the interview relationship is of correct schema type."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.get_by_id(persona.id)

        # Assert
        assert persona_result is not None
        assert isinstance(persona_result.interview, InterviewEntitySchema)


class TestPersonaRepositoryGetAll:
    """Tests for PersonaRepository.get_all()."""

    async def test_get_all_returns_empty_list_when_no_personas(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_all() returns empty list when no personas exist."""
        # Arrange
        repo = PersonaRepository(db_client)

        # Act
        persona_result = await repo.get_all()

        # Assert
        assert persona_result == []

    async def test_get_all_returns_all_created_personas(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns all persisted personas."""
        # Arrange
        repo = PersonaRepository(db_client)
        await persona_factory()
        await persona_factory()
        await persona_factory()

        # Act
        persona_result = await repo.get_all()

        # Assert
        assert len(persona_result) == 3

    async def test_get_all_returns_list_of_persona_rel_entity_schemas(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_all() returns list of PersonaRelEntitySchema instances."""
        # Arrange
        repo = PersonaRepository(db_client)
        await persona_factory()

        # Act
        persona_result = await repo.get_all()

        # Assert
        assert all(isinstance(persona, PersonaRelEntitySchema) for persona in persona_result)

    async def test_get_all_limit_restricts_result_count(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the limit parameter."""
        # Arrange
        repo = PersonaRepository(db_client)
        for _ in range(5):
            await persona_factory()

        # Act
        persona_result = await repo.get_all(limit=3)

        # Assert
        assert len(persona_result) == 3

    async def test_get_all_offset_skips_records(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_all() respects the offset parameter."""
        # Arrange
        repo = PersonaRepository(db_client)
        for _ in range(4):
            await persona_factory()

        # Act
        all_personas = await repo.get_all(limit=100, offset=0)
        offset_personas = await repo.get_all(limit=100, offset=2)

        # Assert
        assert len(offset_personas) == len(all_personas) - 2

    async def test_get_all_offset_returns_non_overlapping_pages(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_all() pagination returns non-overlapping results."""
        # Arrange
        repo = PersonaRepository(db_client)
        for _ in range(4):
            await persona_factory()

        # Act
        first_page = await repo.get_all(limit=2, offset=0)
        second_page = await repo.get_all(limit=2, offset=2)

        # Assert
        first_ids = {persona.id for persona in first_page}
        second_ids = {persona.id for persona in second_page}
        assert first_ids.isdisjoint(second_ids)

    async def test_get_all_personas_have_loaded_interview_relationships(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_all() eagerly loads interview relationships for all personas."""
        # Arrange
        repo = PersonaRepository(db_client)
        await persona_factory()
        await persona_factory()

        # Act
        persona_result = await repo.get_all()

        # Assert
        assert all(persona.interview for persona in persona_result)
        assert all(isinstance(persona.interview, InterviewEntitySchema) for persona in persona_result)


class TestPersonaRepositoryGetCount:
    """Tests for PersonaRepository.get_count()."""

    async def test_get_count_returns_zero_on_empty_table(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that get_count() returns 0 when no personas exist."""
        # Arrange
        repo = PersonaRepository(db_client)

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 0

    async def test_get_count_reflects_created_personas(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_count() returns the correct number of personas."""
        # Arrange
        repo = PersonaRepository(db_client)
        await persona_factory()
        await persona_factory()

        # Act
        count = await repo.get_count()

        # Assert
        assert count == 2

    async def test_get_count_decreases_after_delete(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_count() decreases after deleting a persona."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona = await persona_factory()
        await persona_factory()

        # Act
        await repo.delete_by_id(persona.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_get_count_increments_with_each_create(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that get_count() increments correctly with each creation."""
        # Arrange
        repo = PersonaRepository(db_client)

        # Act & Assert
        for expected in range(1, 4):
            await persona_factory()
            assert await repo.get_count() == expected


class TestPersonaRepositoryUpdateById:
    """Tests for PersonaRepository.update_by_id()."""

    async def test_update_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that update_by_id() returns None for non-existent ID."""
        # Arrange
        repo = PersonaRepository(db_client)
        update_data = UpdatePersonasSchema(bio_description="New bio")

        # Act
        persona_result = await repo.update_by_id(uuid.uuid4(), update_data)

        # Assert
        assert persona_result is None

    async def test_update_bio_description(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() correctly updates bio_description field."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None
        new_bio = "Completely updated biography text"
        update_data = UpdatePersonasSchema(bio_description=new_bio)

        # Act
        persona_result = await repo.update_by_id(persona.id, update_data)

        # Assert
        assert persona_result is not None
        assert persona_result.bio_description == new_bio

    async def test_update_is_verified_to_true(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that update_by_id() can change is_verified from False to True."""
        # Arrange
        repo = PersonaRepository(db_client)
        unverified = await persona_factory(is_verified=False)
        assert unverified.id is not None
        update_data = UpdatePersonasSchema(is_verified=True)

        # Act
        persona_result = await repo.update_by_id(unverified.id, update_data)

        # Assert
        assert persona_result is not None
        assert persona_result.is_verified is True

    async def test_update_is_verified_to_false(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that update_by_id() can change is_verified from True to False."""
        # Arrange
        repo = PersonaRepository(db_client)
        verified = await persona_factory(is_verified=True)
        assert verified.id is not None
        update_data = UpdatePersonasSchema(is_verified=False)

        # Act
        persona_result = await repo.update_by_id(verified.id, update_data)

        # Assert
        assert persona_result is not None
        assert persona_result.is_verified is False

    async def test_update_does_not_change_unspecified_fields(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() only modifies specified fields."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None
        original_demographic = persona.demographic_state
        original_interview_id = persona.interview_id
        update_data = UpdatePersonasSchema(bio_description="Only bio changed")

        # Act
        persona_result = await repo.update_by_id(persona.id, update_data)

        # Assert
        assert persona_result is not None
        assert persona_result.demographic_state == original_demographic
        assert persona_result.interview_id == original_interview_id

    async def test_update_persists_to_database(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() changes are persisted to the database."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None
        update_data = UpdatePersonasSchema(bio_description="Persisted change")

        # Act
        await repo.update_by_id(persona.id, update_data)
        fetched = await repo.get_by_id(persona.id)

        # Assert
        assert fetched is not None
        assert fetched.bio_description == "Persisted change"

    async def test_update_returns_persona_rel_entity_schema(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() returns PersonaRelEntitySchema instance."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None
        update_data = UpdatePersonasSchema(bio_description="Type check")

        # Act
        persona_result = await repo.update_by_id(persona.id, update_data)

        # Assert
        assert isinstance(persona_result, PersonaRelEntitySchema)

    async def test_update_preserves_interview_relationship(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() preserves the interview relationship."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None
        update_data = UpdatePersonasSchema(bio_description="Relationship check")

        # Act
        persona_result = await repo.update_by_id(persona.id, update_data)

        # Assert
        assert persona_result is not None
        assert persona_result.interview is not None
        assert persona_result.interview.id == persona.interview_id
        assert isinstance(persona_result.interview, InterviewEntitySchema)

    async def test_update_does_not_change_id(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that update_by_id() does not modify the persona ID."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None
        original_id = persona.id
        update_data = UpdatePersonasSchema(bio_description="ID must not change")

        # Act
        persona_result = await repo.update_by_id(persona.id, update_data)

        # Assert
        assert persona_result is not None
        assert persona_result.id == original_id


class TestPersonaRepositoryDeleteById:
    """Tests for PersonaRepository.delete_by_id()."""

    async def test_delete_returns_deleted_id(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns the ID of the deleted persona."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.delete_by_id(persona.id)

        # Assert
        assert persona_result == persona.id

    async def test_delete_returns_uuid_type(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() returns a UUID type."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        persona_result = await repo.delete_by_id(persona.id)

        # Assert
        assert isinstance(persona_result, uuid.UUID)

    async def test_delete_returns_none_for_nonexistent(
        self,
        db_client: DatabaseClient,
    ) -> None:
        """Verify that delete_by_id() returns None for non-existent ID."""
        # Arrange
        repo = PersonaRepository(db_client)

        # Act
        persona_result = await repo.delete_by_id(uuid.uuid4())

        # Assert
        assert persona_result is None

    async def test_delete_removes_persona_from_database(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() removes the persona from the database."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        await repo.delete_by_id(persona.id)
        fetched = await repo.get_by_id(persona.id)

        # Assert
        assert fetched is None

    async def test_delete_does_not_affect_other_personas(
        self,
        db_client: DatabaseClient,
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() only deletes the specified persona."""
        # Arrange
        repo = PersonaRepository(db_client)
        to_delete = await persona_factory()
        to_keep = await persona_factory()
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
        persona_factory: Callable[..., PersonaRelEntitySchema],
    ) -> None:
        """Verify that delete_by_id() decreases the total persona count."""
        # Arrange
        repo = PersonaRepository(db_client)
        persona1 = await persona_factory()
        await persona_factory()
        assert persona1.id is not None

        # Act
        await repo.delete_by_id(persona1.id)
        count = await repo.get_count()

        # Assert
        assert count == 1

    async def test_delete_is_idempotent_on_second_call(
        self,
        db_client: DatabaseClient,
        persona: PersonaRelEntitySchema,
    ) -> None:
        """Verify that delete_by_id() is idempotent (returns None on second call)."""
        # Arrange
        repo = PersonaRepository(db_client)
        assert persona.id is not None

        # Act
        await repo.delete_by_id(persona.id)
        persona_result = await repo.delete_by_id(persona.id)

        # Assert
        assert persona_result is None
