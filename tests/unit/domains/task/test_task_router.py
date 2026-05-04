"""Unit tests for task registration API handlers."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi import Response, status

from src.domains.task.app.requests.router import (
    redis_register_final_report_generation_task,
    redis_register_generate_personas_task,
    redis_register_interview_simulation_task,
)
from src.domains.task.app.requests.schema import (
    PostFinalReportGenerationTaskRequest,
    PostGeneratePersonasTaskRequest,
    PostInterviewSimulationTaskRequest,
)
from src.domains.task.exceptions import TaskQueueError
from src.schemas.api_base import StatusType


def _request_data() -> PostGeneratePersonasTaskRequest:
    """Build a valid generate-personas registration request."""
    return PostGeneratePersonasTaskRequest(
        user_id=uuid.uuid4(),
        interview_id=uuid.uuid4(),
        segment_name="developers",
        segment_description="Software developers",
        person_count=3,
    )


def _interview_request_data() -> PostInterviewSimulationTaskRequest:
    """Build a valid interview simulation registration request."""
    return PostInterviewSimulationTaskRequest(
        user_id=uuid.uuid4(),
        interview_id=uuid.uuid4(),
        rewritten_user_request="Validate AI-assisted custdev interviews.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run customer discovery without a research team.",
        batch_size=1,
    )


def _final_report_request_data() -> PostFinalReportGenerationTaskRequest:
    """Build a valid final report registration request."""
    return PostFinalReportGenerationTaskRequest(
        user_id=uuid.uuid4(),
        interview_id=uuid.uuid4(),
    )


async def test_generate_personas_task_route_returns_success_envelope() -> None:
    """Successful registration must return the common success envelope."""
    response = Response()
    task_service = MagicMock()
    task_service.register_generate_personas_task = AsyncMock()

    route_response = await redis_register_generate_personas_task(
        response=response,
        request_data=_request_data(),
        task_service=task_service,
    )

    assert route_response.msg is True
    assert route_response.status == StatusType.SUCCESS
    assert response.status_code == status.HTTP_200_OK


async def test_generate_personas_task_route_returns_error_envelope_on_queue_failure() -> None:
    """Queue registration failures must return a 500 error envelope."""
    response = Response()
    task_service = MagicMock()
    task_service.register_generate_personas_task = AsyncMock(side_effect=TaskQueueError("redis down"))

    route_response = await redis_register_generate_personas_task(
        response=response,
        request_data=_request_data(),
        task_service=task_service,
    )

    assert route_response.status == StatusType.ERROR
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "redis down" in route_response.details


async def test_interview_simulation_task_route_returns_success_envelope() -> None:
    """Successful interview task registration must return the common success envelope."""
    response = Response()
    task_service = MagicMock()
    task_service.register_interview_simulation_task = AsyncMock()

    route_response = await redis_register_interview_simulation_task(
        response=response,
        request_data=_interview_request_data(),
        task_service=task_service,
    )

    assert route_response.msg is True
    assert route_response.status == StatusType.SUCCESS
    assert response.status_code == status.HTTP_200_OK


async def test_final_report_generation_task_route_returns_success_envelope() -> None:
    """Successful final report task registration must return the common success envelope."""
    response = Response()
    task_service = MagicMock()
    task_service.register_final_report_generation_task = AsyncMock()

    route_response = await redis_register_final_report_generation_task(
        response=response,
        request_data=_final_report_request_data(),
        task_service=task_service,
    )

    assert route_response.msg is True
    assert route_response.status == StatusType.SUCCESS
    assert response.status_code == status.HTTP_200_OK
