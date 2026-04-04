"""Report generation task handler for the Redis worker."""

from src.domains.interview.app.usecases.service import InterviewService
from src.schemas.task import TaskSchema


class ReportGenerationTaskHandler:
    """Handle ``REPORT_GENERATION`` tasks.

    Attributes:
        _interview_service: Service executing report generation logic.
    """

    def __init__(self, interview_service: InterviewService) -> None:
        self._interview_service = interview_service

    async def execute(self, task: TaskSchema) -> None:
        """Execute report generation for the given task.

        Args:
            task: Dequeued task payload.
        """
        await self._interview_service.generate(task.input_params)  # type: ignore[attr-defined]
