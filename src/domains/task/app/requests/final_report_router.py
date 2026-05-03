"""FastAPI router for final report generation task registration."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from src.configs.log.logger import get_logger
from src.domains.task.app.requests.final_report_schema import (
    PostFinalReportGenerationTaskRequest,
)
from src.domains.task.app.requests.schema import TaskBoolResponse
from src.domains.task.app.usecases.service import TaskService
from src.domains.task.exceptions import TaskError, TaskQueueError
from src.infrastructure.containers.domain import DomainContainer
from src.schemas.api_base import ResponseBase, StatusType
from src.schemas.interview import FinalReportGenerationTaskInputData

_logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/generate_final_report_task",
    response_model=TaskBoolResponse | ResponseBase,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def redis_register_final_report_generation_task(
    response: Response,
    request_data: PostFinalReportGenerationTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskBoolResponse | ResponseBase:
    """Register a final report generation task and enqueue it in Redis."""
    try:
        await task_service.register_final_report_generation_task(
            user_id=request_data.user_id,
            task_input=FinalReportGenerationTaskInputData(
                interview_id=request_data.interview_id,
            ),
        )
    except TaskQueueError as exc:
        _logger.error("Task registration final report generation in redis queue failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration final report generation in redis queue failed: {exc}",
            status=StatusType.ERROR,
        )
    except TaskError as exc:
        _logger.error("Task registration final report generation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration final report generation failed: {exc}",
            status=StatusType.ERROR,
        )
    except Exception as exc:
        _logger.exception("Unexpected error during task registration final report generation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Internal server error: {exc}",
            status=StatusType.ERROR,
        )

    return TaskBoolResponse(msg=True, status=StatusType.SUCCESS)
