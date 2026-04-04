"""Sub-interview generation task handler for the Redis worker."""

from src.domains.sub_interview.app.usecases.service import SubInterviewService
from src.schemas.task import TaskSchema


class SubInterviewGenerationTaskHandler:
    """Handle ``SUB_INTERVIEW_GENERATION`` tasks.

    Attributes:
        _sub_interview_service: Service executing sub-interview generation.
    """

    def __init__(self, sub_interview_service: SubInterviewService) -> None:
        self._sub_interview_service = sub_interview_service

    async def execute(self, task: TaskSchema) -> None:
        """Execute sub-interview generation for the given task.

        Args:
            task: Dequeued task payload.
        """
        await self._sub_interview_service.generate(task.input_params)  # type: ignore[attr-defined]
