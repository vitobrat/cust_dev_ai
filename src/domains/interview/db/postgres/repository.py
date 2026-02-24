"""Interview repository for PostgreSQL database operations.

This module provides the repository implementation for managing interview entities
in PostgreSQL database using SQLAlchemy ORM.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select

from src.domains.interview.db.postgres.model import InterviewsOrm
from src.infrastructure.db.postgres.repository import BaseCRUDRepository
from src.schemas.interview import (
    CreateInterviewSchema,
    InterviewEntitySchema,
    UpdateInterviewSchema,
)


class InterviewRepository(
    BaseCRUDRepository[InterviewsOrm, CreateInterviewSchema, UpdateInterviewSchema, InterviewEntitySchema],
):
    """Repository for interview entity CRUD operations.

    Provides async methods for creating, reading, updating, and deleting interview records
    in PostgreSQL database.
    """

    async def create(
        self,
        create_data: CreateInterviewSchema,
    ) -> InterviewEntitySchema:
        """Create a new interview record.

        Args:
            create_data: Schema containing interview creation data.

        Returns:
            Created interview entity with generated ID and timestamps.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        interview = InterviewsOrm(
            report_content_url=create_data.report_content_url,
            user_id=create_data.user_id,
        )

        self._session.add(interview)
        await self._session.flush()
        await self._session.refresh(interview)

        return InterviewEntitySchema.model_validate(interview)

    async def get_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[InterviewEntitySchema]:
        """Retrieve an interview by its ID.

        Args:
            entity_id: UUID of the interview to retrieve.

        Returns:
            Interview entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        interview = await self._session.get(InterviewsOrm, entity_id)

        if interview is None:
            return None

        return InterviewEntitySchema.model_validate(interview)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InterviewEntitySchema]:
        """Retrieve all interviews with pagination.

        Args:
            limit: Maximum number of records to return. Defaults to 100.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of interview entities.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        query = select(InterviewsOrm).limit(limit).offset(offset)
        interviews_result = await self._session.execute(query)
        interviews = interviews_result.scalars().all()

        return [InterviewEntitySchema.model_validate(interview) for interview in interviews]

    async def get_count(self) -> int:
        """Get total count of interviews in the database.

        Returns:
            Total number of interview records.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        query = select(func.count()).select_from(InterviewsOrm)
        interviews_result = await self._session.execute(query)

        return interviews_result.scalar_one()

    async def update_by_id(
        self,
        entity_id: uuid.UUID,
        update_data: UpdateInterviewSchema,
    ) -> Optional[InterviewEntitySchema]:
        """Update an interview by its ID.

        Only fields present in update_data will be modified.

        Args:
            entity_id: UUID of the interview to update.
            update_data: Schema containing fields to update.

        Returns:
            Updated interview entity if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        interview = await self._session.get(InterviewsOrm, entity_id)

        if interview is None:
            return None

        update_fields = update_data.model_dump(exclude_unset=True)

        for field, interview_value in update_fields.items():
            setattr(interview, field, interview_value)

        await self._session.flush()
        await self._session.refresh(interview)

        return InterviewEntitySchema.model_validate(interview)

    async def delete_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """Delete an interview by its ID.

        Args:
            entity_id: UUID of the interview to delete.

        Returns:
            UUID of deleted interview if found, None otherwise.

        Raises:
            SQLAlchemyError: If database operation fails.
        """
        interview = await self._session.get(InterviewsOrm, entity_id)

        if interview is None:
            return None

        await self._session.delete(interview)
        await self._session.flush()

        return entity_id
