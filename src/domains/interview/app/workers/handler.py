"""Interview-domain task handlers for the Redis worker."""

from src.domains.interview.app.usecases.service import InterviewService
from src.domains.task.app.constants import TaskType
from src.schemas.interview import (
    FinalReportGenerationTaskInputData,
    InterviewSimulationTaskInputData,
)
from src.schemas.task import TaskSchema


class InterviewSimulationTaskHandler:
    """Handle full interview simulation Redis tasks."""

    def __init__(self, interview_service: InterviewService) -> None:
        self._interview_service = interview_service

    async def execute(self, task: TaskSchema) -> None:
        """Execute a full interview simulation task.

        Args:
            task: Dequeued Redis task payload.

        Raises:
            ValueError: If task type or input payload does not match this handler.
        """
        if task.type is not TaskType.INTERVIEW_SIMULATION:
            raise ValueError(f"InterviewSimulationTaskHandler cannot execute task type {task.type.value}.")

        task_input = task.input_params
        if not isinstance(task_input, InterviewSimulationTaskInputData):
            raise ValueError("Interview simulation task payload has invalid input_params.")

        await self._interview_service.simulate_interviews(task_input)


class FinalReportGenerationTaskHandler:
    """Handle final interview report generation Redis tasks."""

    def __init__(self, interview_service: InterviewService) -> None:
        self._interview_service = interview_service

    async def execute(self, task: TaskSchema) -> None:
        """Execute a final report generation task.

        Args:
            task: Dequeued Redis task payload.

        Raises:
            ValueError: If task type or input payload does not match this handler.
        """
        if task.type is not TaskType.REPORT_GENERATION:
            raise ValueError(f"FinalReportGenerationTaskHandler cannot execute task type {task.type.value}.")

        task_input = task.input_params
        if not isinstance(task_input, FinalReportGenerationTaskInputData):
            raise ValueError("Final report generation task payload has invalid input_params.")

        await self._interview_service.generate_final_report(task_input)
