"""Unit tests for Redis task handler that runs interview simulation."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.configs.consts import INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE
from src.domains.interview.app.workers.handler import (
    InterviewSimulationTaskHandler,
)
from src.domains.task.app.constants import TaskType
from src.schemas.interview import InterviewSimulationTaskInputData
from src.schemas.persona import GeneratePersonasTaskInputData
from src.schemas.task import TaskSchema


def _interview_task_input(interview_id: uuid.UUID, batch_size: int = 1) -> InterviewSimulationTaskInputData:
    return InterviewSimulationTaskInputData(
        interview_id=interview_id,
        rewritten_user_request="Validate AI-assisted custdev interviews.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run customer discovery without a research team.",
        batch_size=batch_size,
    )


def _interview_task(task_input: InterviewSimulationTaskInputData) -> TaskSchema:
    return TaskSchema(
        task_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        type=TaskType.INTERVIEW_SIMULATION,
        input_params=task_input,
    )


async def test_interview_simulation_task_handler_delegates_to_service() -> None:
    """The interview Redis handler must execute exactly one interview simulation task type."""
    interview_service = MagicMock()
    interview_service.simulate_interviews = AsyncMock()
    task_handler = InterviewSimulationTaskHandler(interview_service=interview_service)
    task_input = _interview_task_input(uuid.uuid4())

    await task_handler.execute(_interview_task(task_input))

    interview_service.simulate_interviews.assert_awaited_once_with(task_input)


async def test_interview_simulation_task_handler_rejects_wrong_input_payload() -> None:
    """Incorrect task payloads should fail explicitly instead of reaching the service."""
    interview_service = MagicMock()
    interview_service.simulate_interviews = AsyncMock()
    task_handler = InterviewSimulationTaskHandler(interview_service=interview_service)
    wrong_input = GeneratePersonasTaskInputData(
        interview_id=uuid.uuid4(),
        segment_name="Founders",
        segment_description="Founders doing discovery.",
        person_count=1,
    )
    task = _interview_task(_interview_task_input(uuid.uuid4())).model_copy(update={"input_params": wrong_input})

    with pytest.raises(ValueError):
        await task_handler.execute(task)

    interview_service.simulate_interviews.assert_not_awaited()


def test_interview_simulation_task_input_rejects_unsafe_batch_size() -> None:
    """Task input must cap batch size to protect worker fan-out."""
    with pytest.raises(ValidationError):
        _interview_task_input(uuid.uuid4(), batch_size=INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE + 1)
