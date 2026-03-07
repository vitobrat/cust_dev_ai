"""Persona repository implementation for PostgreSQL database operations.

This module provides concrete implementation of CRUD operations for Persona entities
using SQLAlchemy ORM and async sessions.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select

from src.domains.persona.db.postgres.model import PersonasOrm
from src.infrastructure.db.postgres.repository import BaseCRUDRepository
from src.schemas.persona import (
    CreatePersonaSchema,
    PersonaRelEntitySchema,
    UpdatePersonasSchema,
)


class PersonaRepository(
    BaseCRUDRepository[PersonasOrm, CreatePersonaSchema, UpdatePersonasSchema, PersonaRelEntitySchema],
):
    """Repository for managing Persona entities in PostgreSQL.

    This repository handles all database operations for Persona entities,
    including creation, retrieval, updates, and deletion with proper
    validation and type safety.

    Attributes:
        model: PersonasOrm SQLAlchemy model class.
    """

    model = PersonasOrm

    async def create(
        self,
        create_data: CreatePersonaSchema,
    ) -> PersonaRelEntitySchema:
        """Create a new persona in the database.

        Args:
            create_data: Validated schema containing persona creation data.

        Returns:
            Created persona entity with generated ID and timestamps.
        """
        persona = PersonasOrm(
            demographic_state=create_data.demographic_state.model_dump(),
            bio_description=create_data.bio_description,
            is_verified=create_data.is_verified,
            interview_id=create_data.interview_id,
        )

        self._session.add(persona)
        await self._session.flush()
        await self._session.refresh(persona)

        return PersonaRelEntitySchema.model_validate(persona)

    async def get_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[PersonaRelEntitySchema]:
        """Retrieve a persona by its unique identifier with related interview.

        Args:
            entity_id: UUID of the persona to retrieve.

        Returns:
            Persona entity with loaded interview relation if found, None otherwise.
        """
        persona = await self._session.get(PersonasOrm, entity_id)

        if persona is None:
            return None

        return PersonaRelEntitySchema.model_validate(persona)

    async def get_all(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[PersonaRelEntitySchema]:
        """Retrieve multiple personas with pagination support.

        Args:
            limit: Maximum number of personas to return. Defaults to 10.
            offset: Number of personas to skip. Defaults to 0.

        Returns:
            List of persona entities ordered by database default.
        """
        query = select(PersonasOrm).limit(limit).offset(offset)
        persona_result = await self._session.execute(query)
        personas = persona_result.scalars().all()

        return [PersonaRelEntitySchema.model_validate(persona) for persona in personas]

    async def get_count(self) -> int:
        """Get total count of personas in the database.

        Returns:
            Total number of persona records.
        """
        query = select(func.count()).select_from(PersonasOrm)
        persona_result = await self._session.execute(query)

        return persona_result.scalar_one()

    async def update_by_id(
        self,
        entity_id: uuid.UUID,
        update_data: UpdatePersonasSchema,
    ) -> Optional[PersonaRelEntitySchema]:
        """Update an existing persona by its identifier.

        Only fields present in update_data (exclude_unset=True) will be modified.

        Args:
            entity_id: UUID of the persona to update.
            update_data: Schema containing fields to update.

        Returns:
            Updated persona entity if found, None otherwise.
        """
        persona = await self._session.get(PersonasOrm, entity_id)

        if persona is None:
            return None

        update_fields = update_data.model_dump(exclude_unset=True)

        for field, field_value in update_fields.items():
            setattr(persona, field, field_value)

        await self._session.flush()
        await self._session.refresh(persona)

        return PersonaRelEntitySchema.model_validate(persona)

    async def delete_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """Delete a persona by its identifier.

        Args:
            entity_id: UUID of the persona to delete.

        Returns:
            UUID of deleted persona if found, None otherwise.
        """
        persona = await self._session.get(PersonasOrm, entity_id)

        if persona is None:
            return None

        await self._session.delete(persona)
        await self._session.flush()

        return entity_id
