"""Business logic service for the Interview domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.interview.exceptions import (
    InterviewDeletionFailed,
    InterviewGetFailed,
    InterviewUpdateFailed,
)
from src.schemas.interview import (
    CreateInterviewSchema,
    InterviewRelEntitySchema,
    UpdateInterviewSchema,
)


class InterviewService:
    """Service layer for interview business logic.

    Encapsulates CRUD operations for interview entities, acting as the boundary
    between the HTTP layer and the persistence layer.

    Attributes:
        _interviews_repository: Repository for interview persistence operations.
    """

    def __init__(self, interviews_repository: InterviewRepository) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._interviews_repository = interviews_repository

    async def create_interview(self, create_interview_data: CreateInterviewSchema) -> InterviewRelEntitySchema:
        """Persist a new interview entity.

        Args:
            create_interview_data: Validated creation payload.

        Returns:
            Newly created interview entity with generated ID and timestamps.
        """
        return await self._interviews_repository.create(create_interview_data)

    async def get_interview(self, interview_id: uuid.UUID) -> InterviewRelEntitySchema:
        """Retrieve a single interview by its identifier.

        Args:
            interview_id: UUID of the interview to retrieve.

        Returns:
            Interview entity with loaded relations if found.

        Raises:
            InterviewGetFailed: If no interview with the given ID exists.
        """
        interview = await self._interviews_repository.get_by_id(interview_id)

        if interview is None:
            self._logger.error("Interview not found: %s", interview_id)
            raise InterviewGetFailed(f"Interview with id={interview_id} does not exist.")

        return interview

    async def get_interviews(self, limit: int = 10, offset: int = 0) -> list[InterviewRelEntitySchema]:
        """Retrieve a paginated list of interviews.

        Args:
            limit: Maximum number of records to return. Defaults to 10.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of interview entities (may be empty).
        """
        return await self._interviews_repository.get_all(limit, offset)

    async def count_interviews(self) -> int:
        """Return the total number of stored interviews.

        Returns:
            Integer count of interview records.
        """
        return await self._interviews_repository.get_count()

    async def update_interview(
        self,
        interview_id: uuid.UUID,
        update_interview_data: UpdateInterviewSchema,
    ) -> InterviewRelEntitySchema:
        """Apply a partial update to an existing interview.

        Args:
            interview_id: UUID of the interview to update.
            update_interview_data: Partial schema; only set fields are applied.

        Returns:
            Updated interview entity.

        Raises:
            InterviewUpdateFailed: If no interview with the given ID exists.
        """
        updated_interview = await self._interviews_repository.update_by_id(interview_id, update_interview_data)

        if updated_interview is None:
            self._logger.error("Interview not found for update: %s", interview_id)
            raise InterviewUpdateFailed(f"Interview with id={interview_id} does not exist.")

        return updated_interview

    async def delete_interview(self, interview_id: uuid.UUID) -> None:
        """Delete an interview by its identifier.

        Args:
            interview_id: UUID of the interview to delete.

        Raises:
            InterviewDeletionFailed: If no interview with the given ID exists.
        """
        deleted_id = await self._interviews_repository.delete_by_id(interview_id)

        if deleted_id is None:
            self._logger.error("Interview not found for deletion: %s", interview_id)
            raise InterviewDeletionFailed(f"Interview with id={interview_id} does not exist.")
