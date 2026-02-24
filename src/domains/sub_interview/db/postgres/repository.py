"""Sub-interview repository for PostgreSQL database operations.

This module provides the repository implementation for managing sub-interview entities
in PostgreSQL database using SQLAlchemy ORM.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select

from src.domains.sub_interview.db.postgres.model import SubInterviewsOrm
from src.infrastructure.db.postgres.repository import BaseCRUDRepository
from src.schemas.sub_interview import (
    CreateSubInterviewSchema,
    SubInterviewEntitySchema,
    UpdateSubInterviewSchema,
)


class SubInterviewRepository(
    BaseCRUDRepository[SubInterviewsOrm, CreateSubInterviewSchema, UpdateSubInterviewSchema, SubInterviewEntitySchema],
):
    """Repository for sub-interview entity CRUD operations.

    Provides async methods for creating, reading, updating, and deleting sub-interview records
    in PostgreSQL database.
    """

    async def create(
        self,
        create_data: CreateSubInterviewSchema,
    ) -> SubInterviewEntitySchema:
        """Create a new sub-interview record.

        Args:
            create_data: Schema containing sub-interview creation data.

        Returns:
            Created sub-interview entity with generated ID and timestamps.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        sub_interview = SubInterviewsOrm(
            chat_history=create_data.chat_history,
            status=create_data.status,
            interview_id=create_data.interview_id,
        )

        self._session.add(sub_interview)
        await self._session.flush()
        await self._session.refresh(sub_interview)

        return SubInterviewEntitySchema.model_validate(sub_interview)

    async def get_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[SubInterviewEntitySchema]:
        """Retrieve a sub-interview by its ID.

        Args:
            entity_id: UUID of the sub-interview to retrieve.

        Returns:
            Sub-interview entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        sub_interview = await self._session.get(SubInterviewsOrm, entity_id)

        if sub_interview is None:
            return None

        return SubInterviewEntitySchema.model_validate(sub_interview)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SubInterviewEntitySchema]:
        """Retrieve all sub-interviews with pagination.

        Args:
            limit: Maximum number of records to return. Defaults to 100.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of sub-interview entities.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        query = select(SubInterviewsOrm).limit(limit).offset(offset)
        sub_interviews_result = await self._session.execute(query)
        sub_interviews = sub_interviews_result.scalars().all()

        return [SubInterviewEntitySchema.model_validate(sub_interview) for sub_interview in sub_interviews]

    async def get_count(self) -> int:
        """Get total count of sub-interviews in the database.

        Returns:
            Total number of sub-interview records.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        query = select(func.count()).select_from(SubInterviewsOrm)
        users_result = await self._session.execute(query)

        return users_result.scalar_one()

    async def update_by_id(
        self,
        entity_id: uuid.UUID,
        update_data: UpdateSubInterviewSchema,
    ) -> Optional[SubInterviewEntitySchema]:
        """Update a sub-interview by its ID.

        Only fields present in update_data will be modified.

        Args:
            entity_id: UUID of the sub-interview to update.
            update_data: Schema containing fields to update.

        Returns:
            Updated sub-interview entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        sub_interview = await self._session.get(SubInterviewsOrm, entity_id)

        if sub_interview is None:
            return None

        update_fields = update_data.model_dump(exclude_unset=True)

        for field, user_value in update_fields.items():
            setattr(sub_interview, field, user_value)

        await self._session.flush()
        await self._session.refresh(sub_interview)

        return SubInterviewEntitySchema.model_validate(sub_interview)

    async def delete_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """Delete a sub-interview by its ID.

        Args:
            entity_id: UUID of the sub-interview to delete.

        Returns:
            UUID of deleted sub-interview if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        sub_interview = await self._session.get(SubInterviewsOrm, entity_id)

        if sub_interview is None:
            return None

        await self._session.delete(sub_interview)
        await self._session.flush()

        return entity_id
