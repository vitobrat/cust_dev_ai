"""FastAPI router for Task CRUD endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from src.configs.log.logger import get_logger
from src.domains.task.app.requests.schema import (  # noqa: WPS235
    GetTasksRequest,
    PostCreateTaskRequest,
    PostFinalReportGenerationTaskRequest,
    PostGeneratePersonasTaskRequest,
    PostInterviewSimulationTaskRequest,
    PostPersonasPipelineTaskRequest,
    PostSinglePersonaTaskRequest,
    PutUpdateTaskRequest,
    TaskBoolResponse,
    TaskCountResponse,
    TaskEntityResponse,
    TaskListResponse,
)
from src.domains.task.app.usecases.service import TaskService
from src.domains.task.exceptions import TaskError, TaskNotFound, TaskQueueError
from src.infrastructure.containers.domain import DomainContainer
from src.schemas.api_base import ResponseBase, StatusType
from src.schemas.interview import (
    FinalReportGenerationTaskInputData,
    InterviewSimulationTaskInputData,
)
from src.schemas.persona import (
    GeneratePersonasTaskInputData,
    GenerateSinglePersonaTaskInputData,
    PersonasPipelineTaskInputData,
)

_logger = get_logger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.post(
    "/personas_pipeline_task",
    response_model=TaskBoolResponse | ResponseBase,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def redis_register_personas_pipeline_task(
    response: Response,
    request_data: PostPersonasPipelineTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskBoolResponse | ResponseBase:
    """Register a full persona pipeline task and enqueue it in Redis."""
    try:
        await task_service.register_personas_pipeline_task(
            user_id=request_data.user_id,
            task_input=PersonasPipelineTaskInputData(
                interview_id=request_data.interview_id,
                user_prompt=request_data.user_prompt,
                person_count=request_data.person_count,
            ),
        )
    except TaskQueueError as exc:
        _logger.error("Task registration personas pipeline in redis queue failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration personas pipeline in redis queue failed: {exc}",
            status=StatusType.ERROR,
        )
    except TaskError as exc:
        _logger.error("Task registration personas pipeline failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration personas pipeline failed: {exc}",
            status=StatusType.ERROR,
        )
    except Exception as exc:
        _logger.exception("Unexpected error during task registration personas pipeline")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Internal server error: {exc}",
            status=StatusType.ERROR,
        )

    return TaskBoolResponse(msg=True, status=StatusType.SUCCESS)


@router.post(
    "/generate_single_persona_task",
    response_model=TaskBoolResponse | ResponseBase,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def redis_register_generate_single_persona_task(
    response: Response,
    request_data: PostSinglePersonaTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskBoolResponse | ResponseBase:
    """Register a single persona generation task and enqueue it in Redis."""
    try:
        await task_service.register_generate_single_persona_task(
            user_id=request_data.user_id,
            task_input=GenerateSinglePersonaTaskInputData(
                interview_id=request_data.interview_id,
                segment_name=request_data.segment_name,
                segment_description=request_data.segment_description,
            ),
        )
    except TaskQueueError as exc:
        _logger.error("Task registration generate single persona in redis queue failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration generate single persona in redis queue failed: {exc}",
            status=StatusType.ERROR,
        )
    except TaskError as exc:
        _logger.error("Task registration generate single persona failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration generate single persona failed: {exc}",
            status=StatusType.ERROR,
        )
    except Exception as exc:
        _logger.exception("Unexpected error during task registration generate single persona")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Internal server error: {exc}",
            status=StatusType.ERROR,
        )

    return TaskBoolResponse(msg=True, status=StatusType.SUCCESS)


@router.post(
    "/generate_personas_task",
    response_model=TaskBoolResponse | ResponseBase,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def redis_register_generate_personas_task(
    response: Response,
    request_data: PostGeneratePersonasTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskBoolResponse | ResponseBase:
    """Register a batch persona generation task and enqueue it in Redis."""
    try:
        await task_service.register_generate_personas_task(
            user_id=request_data.user_id,
            task_input=GeneratePersonasTaskInputData(
                interview_id=request_data.interview_id,
                segment_name=request_data.segment_name,
                segment_description=request_data.segment_description,
                person_count=request_data.person_count,
            ),
        )
    except TaskQueueError as exc:
        _logger.error("Task registration generate personas in redis queue failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration generate personas in redis queue failed: {exc}",
            status=StatusType.ERROR,
        )
    except TaskError as exc:
        _logger.error("Task registration generate personas failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration generate personas failed: {exc}",
            status=StatusType.ERROR,
        )
    except Exception as exc:
        _logger.exception("Unexpected error during task registration generate personas")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Internal server error: {exc}",
            status=StatusType.ERROR,
        )

    return TaskBoolResponse(msg=True, status=StatusType.SUCCESS)


@router.post(
    "/interview_simulation_task",
    response_model=TaskBoolResponse | ResponseBase,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def redis_register_interview_simulation_task(
    response: Response,
    request_data: PostInterviewSimulationTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskBoolResponse | ResponseBase:
    """Register a full interview simulation task and enqueue it in Redis."""
    try:
        await task_service.register_interview_simulation_task(
            user_id=request_data.user_id,
            task_input=InterviewSimulationTaskInputData(
                interview_id=request_data.interview_id,
                rewritten_user_request=request_data.rewritten_user_request,
                segment_name=request_data.segment_name,
                segment_description=request_data.segment_description,
                batch_size=request_data.batch_size,
                max_iterations_per_interview=request_data.max_iterations_per_interview,
                user_controlled_knowledge_context=request_data.user_controlled_knowledge_context,
                allow_external_search=request_data.allow_external_search,
            ),
        )
    except TaskQueueError as exc:
        _logger.error("Task registration interview simulation in redis queue failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration interview simulation in redis queue failed: {exc}",
            status=StatusType.ERROR,
        )
    except TaskError as exc:
        _logger.error("Task registration interview simulation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Task registration interview simulation failed: {exc}",
            status=StatusType.ERROR,
        )
    except Exception as exc:
        _logger.exception("Unexpected error during task registration interview simulation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(
            details=f"Internal server error: {exc}",
            status=StatusType.ERROR,
        )

    return TaskBoolResponse(msg=True, status=StatusType.SUCCESS)


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


@router.post("/", response_model=TaskEntityResponse | ResponseBase, status_code=status.HTTP_201_CREATED)
@inject
async def create_task(
    response: Response,
    request_data: PostCreateTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskEntityResponse | ResponseBase:
    """Create a new task.

    Args:
        response: FastAPI response object used to override the status code on errors.
        request_data: Validated task creation payload.
        task_service: Injected task service.

    Returns:
        Created task entity wrapped in a success response, or an error response.
    """
    try:
        new_task = await task_service.create_task(request_data)
    except TaskError as exc:
        _logger.error("Task creation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Task creation failed: {exc}", status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during task creation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return TaskEntityResponse(msg=new_task, status=StatusType.SUCCESS)


@router.get("/count", response_model=TaskCountResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def count_tasks(
    response: Response,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskCountResponse | ResponseBase:
    """Get total count of tasks.

    Args:
        response: FastAPI response object used to override the status code on errors.
        task_service: Injected task service.

    Returns:
        Integer count wrapped in a success response, or an error response.
    """
    try:
        count = await task_service.count_tasks()
    except Exception as exc:
        _logger.exception("Unexpected error during task count")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return TaskCountResponse(msg=count, status=StatusType.SUCCESS)


@router.get("/", response_model=TaskListResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_tasks(
    response: Response,
    pagination: Annotated[GetTasksRequest, Query()],
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskListResponse | ResponseBase:
    """Get a paginated list of tasks.

    Args:
        response: FastAPI response object used to override the status code on errors.
        pagination: Pagination query parameters (limit, offset).
        task_service: Injected task service.

    Returns:
        List of task entities wrapped in a success response, or an error response.
    """
    try:
        tasks = await task_service.get_tasks(limit=pagination.limit, offset=pagination.offset)
    except Exception as exc:
        _logger.exception("Unexpected error during tasks retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return TaskListResponse(msg=tasks, status=StatusType.SUCCESS)


@router.get("/{task_id}", response_model=TaskEntityResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_task(
    response: Response,
    task_id: uuid.UUID,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskEntityResponse | ResponseBase:
    """Get a single task by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        task_id: UUID of the task to retrieve.
        task_service: Injected task service.

    Returns:
        Task entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        task = await task_service.get_task(task_id)
    except TaskNotFound as exc:
        _logger.warning("Task not found: %s", task_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during task retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return TaskEntityResponse(msg=task, status=StatusType.SUCCESS)


@router.put("/{task_id}", response_model=TaskEntityResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def update_task(
    response: Response,
    task_id: uuid.UUID,
    request_data: PutUpdateTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskEntityResponse | ResponseBase:
    """Update a task by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        task_id: UUID of the task to update.
        request_data: Validated partial update payload.
        task_service: Injected task service.

    Returns:
        Updated task entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        updated_task = await task_service.update_task(
            task_id=task_id,
            update_task_data=request_data,
        )
    except TaskNotFound as exc:
        _logger.warning("Task not found for update: %s", task_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during task update")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return TaskEntityResponse(msg=updated_task, status=StatusType.SUCCESS)


@router.delete("/{task_id}", response_model=TaskBoolResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def delete_task(
    response: Response,
    task_id: uuid.UUID,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> TaskBoolResponse | ResponseBase:
    """Delete a task by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        task_id: UUID of the task to delete.
        task_service: Injected task service.

    Returns:
        Boolean success flag wrapped in a success response, or a 404/500 error response.
    """
    try:
        await task_service.delete_task(task_id)
    except TaskNotFound as exc:
        _logger.warning("Task not found for deletion: %s", task_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during task deletion")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return TaskBoolResponse(msg=True, status=StatusType.SUCCESS)
