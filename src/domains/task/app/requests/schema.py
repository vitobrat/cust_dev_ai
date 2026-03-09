"""Request and response schemas for the Task API endpoints."""

from src.schemas.api_base import PaginationBase, ResponseBase
from src.schemas.task import (
    CreateTaskSchema,
    TaskRelEntitySchema,
    UpdateTaskSchema,
)


class PostCreateTaskRequest(CreateTaskSchema):
    """Request schema for task creation."""


class PostCreateTaskResponse(ResponseBase):
    """Response schema for task creation."""

    msg: TaskRelEntitySchema


class GetTasksRequest(PaginationBase):
    """Pagination query parameters for task list endpoint."""


class GetTaskResponse(ResponseBase):
    """Response schema for a single task retrieval."""

    msg: TaskRelEntitySchema


class GetTasksResponse(ResponseBase):
    """Response schema for paginated task list retrieval."""

    msg: list[TaskRelEntitySchema]


class GetCountTaskResponse(ResponseBase):
    """Response schema for task count."""

    msg: int


class PutUpdateTaskRequest(UpdateTaskSchema):
    """Request schema for partial task update."""


class PutUpdateTaskResponse(ResponseBase):
    """Response schema for task update."""

    msg: TaskRelEntitySchema


class DeleteTaskResponse(ResponseBase):
    """Response schema for task deletion."""

    msg: bool
