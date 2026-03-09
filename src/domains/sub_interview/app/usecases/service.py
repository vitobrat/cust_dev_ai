"""Business logic service for the SubInterview domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.domains.sub_interview.exceptions import (
    SubInterviewDeletionFailed,
    SubInterviewGetFailed,
    SubInterviewUpdateFailed,
)
from src.schemas.sub_interview import (
    CreateSubInterviewSchema,
    SubInterviewRelEntitySchema,
    UpdateSubInterviewSchema,
)


class SubInterviewService:
    """Service layer for sub-interview business logic.

    Encapsulates CRUD operations for sub-interview entities, acting as the boundary
    between the HTTP layer and the persistence layer.

    Attributes:
        _sub_interviews_repository: Repository for sub-interview persistence operations.
    """

    def __init__(self, sub_interviews_repository: SubInterviewRepository) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._sub_interviews_repository = sub_interviews_repository

    async def create_sub_interview(
        self,
        create_sub_interview_data: CreateSubInterviewSchema,
    ) -> SubInterviewRelEntitySchema:
        """Persist a new sub-interview entity.

        Args:
            create_sub_interview_data: Validated creation payload.

        Returns:
            Newly created sub-interview entity with generated ID and timestamps.
        """
        return await self._sub_interviews_repository.create(create_sub_interview_data)

    async def get_sub_interview(self, sub_interview_id: uuid.UUID) -> SubInterviewRelEntitySchema:
        """Retrieve a single sub-interview by its identifier.

        Args:
            sub_interview_id: UUID of the sub-interview to retrieve.

        Returns:
            Sub-interview entity with loaded relations if found.

        Raises:
            SubInterviewGetFailed: If no sub-interview with the given ID exists.
        """
        sub_interview = await self._sub_interviews_repository.get_by_id(sub_interview_id)

        if sub_interview is None:
            self._logger.error("SubInterview not found: %s", sub_interview_id)
            raise SubInterviewGetFailed(f"SubInterview with id={sub_interview_id} does not exist.")

        return sub_interview

    async def get_sub_interviews(self, limit: int = 10, offset: int = 0) -> list[SubInterviewRelEntitySchema]:
        """Retrieve a paginated list of sub-interviews.

        Args:
            limit: Maximum number of records to return. Defaults to 10.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of sub-interview entities (may be empty).
        """
        return await self._sub_interviews_repository.get_all(limit, offset)

    async def count_sub_interviews(self) -> int:
        """Return the total number of stored sub-interviews.

        Returns:
            Integer count of sub-interview records.
        """
        return await self._sub_interviews_repository.get_count()

    async def update_sub_interview(
        self,
        sub_interview_id: uuid.UUID,
        update_sub_interview_data: UpdateSubInterviewSchema,
    ) -> SubInterviewRelEntitySchema:
        """Apply a partial update to an existing sub-interview.

        Args:
            sub_interview_id: UUID of the sub-interview to update.
            update_sub_interview_data: Partial schema; only set fields are applied.

        Returns:
            Updated sub-interview entity.

        Raises:
            SubInterviewUpdateFailed: If no sub-interview with the given ID exists.
        """
        updated = await self._sub_interviews_repository.update_by_id(sub_interview_id, update_sub_interview_data)

        if updated is None:
            self._logger.error("SubInterview not found for update: %s", sub_interview_id)
            raise SubInterviewUpdateFailed(f"SubInterview with id={sub_interview_id} does not exist.")

        return updated

    async def delete_sub_interview(self, sub_interview_id: uuid.UUID) -> None:
        """Delete a sub-interview by its identifier.

        Args:
            sub_interview_id: UUID of the sub-interview to delete.

        Raises:
            SubInterviewDeletionFailed: If no sub-interview with the given ID exists.
        """
        deleted_id = await self._sub_interviews_repository.delete_by_id(sub_interview_id)

        if deleted_id is None:
            self._logger.error("SubInterview not found for deletion: %s", sub_interview_id)
            raise SubInterviewDeletionFailed(f"SubInterview with id={sub_interview_id} does not exist.")
