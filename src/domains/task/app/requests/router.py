"""FastAPI router for Task CRUD endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from src.configs.log.logger import get_logger
from src.domains.task.app.requests.schema import (  # noqa: WPS235
    DeleteTaskResponse,
    GetCountTaskResponse,
    GetTaskResponse,
    GetTasksRequest,
    GetTasksResponse,
    PostCreateTaskRequest,
    PostCreateTaskResponse,
    PutUpdateTaskRequest,
    PutUpdateTaskResponse,
)
from src.domains.task.app.usecases.service import TaskService
from src.domains.task.exceptions import TaskError, TaskNotFound
from src.infrastructure.containers.domain import DomainContainer
from src.schemas.api_base import ResponseBase, StatusType

_logger = get_logger(__name__)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.post("/", response_model=PostCreateTaskResponse | ResponseBase, status_code=status.HTTP_201_CREATED)
@inject
async def create_task(
    response: Response,
    request_data: PostCreateTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> PostCreateTaskResponse | ResponseBase:
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

    return PostCreateTaskResponse(msg=new_task, status=StatusType.SUCCESS)


@router.get("/count", response_model=GetCountTaskResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def count_tasks(
    response: Response,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> GetCountTaskResponse | ResponseBase:
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

    return GetCountTaskResponse(msg=count, status=StatusType.SUCCESS)


@router.get("/", response_model=GetTasksResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_tasks(
    response: Response,
    pagination: Annotated[GetTasksRequest, Query()],
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> GetTasksResponse | ResponseBase:
    """Get a paginated list of tasks.

    Args:
        response: FastAPI response object used to override the status code on errors.
        params: Pagination query parameters (limit, offset).
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

    return GetTasksResponse(msg=tasks, status=StatusType.SUCCESS)


@router.get("/{task_id}", response_model=GetTaskResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_task(
    response: Response,
    task_id: uuid.UUID,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> GetTaskResponse | ResponseBase:
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

    return GetTaskResponse(msg=task, status=StatusType.SUCCESS)


@router.put("/{task_id}", response_model=PutUpdateTaskResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def update_task(
    response: Response,
    task_id: uuid.UUID,
    request_data: PutUpdateTaskRequest,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> PutUpdateTaskResponse | ResponseBase:
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

    return PutUpdateTaskResponse(msg=updated_task, status=StatusType.SUCCESS)


@router.delete("/{task_id}", response_model=DeleteTaskResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def delete_task(
    response: Response,
    task_id: uuid.UUID,
    task_service: TaskService = Depends(Provide[DomainContainer.task.task_service]),
) -> DeleteTaskResponse | ResponseBase:
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

    return DeleteTaskResponse(msg=True, status=StatusType.SUCCESS)
