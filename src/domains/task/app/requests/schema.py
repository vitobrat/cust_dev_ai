"""Request and response schemas for the Task API endpoints."""

import uuid

from pydantic import BaseModel

from src.schemas.api_base import PaginationBase, ResponseBase
from src.schemas.task import (
    CreateTaskSchema,
    TaskRelEntitySchema,
    UpdateTaskSchema,
)


class PostPersonasPipelineTaskRequest(BaseModel):
    """Request schema for registering a full persona pipeline task in Redis."""

    user_id: uuid.UUID
    interview_id: uuid.UUID
    user_prompt: str
    person_count: int


class PostSinglePersonaTaskRequest(BaseModel):
    """Request schema for registering a single persona generation task in Redis."""

    user_id: uuid.UUID
    interview_id: uuid.UUID
    segment_name: str
    segment_description: str


class PostGeneratePersonasTaskRequest(BaseModel):
    """Request schema for registering a batch persona generation task in Redis."""

    user_id: uuid.UUID
    interview_id: uuid.UUID
    segment_name: str
    segment_description: str
    person_count: int


class PostCreateTaskRequest(CreateTaskSchema):
    """Request schema for task creation."""


class GetTasksRequest(PaginationBase):
    """Pagination query parameters for task list endpoint."""


class PutUpdateTaskRequest(UpdateTaskSchema):
    """Request schema for partial task update."""


class TaskEntityResponse(ResponseBase):
    """Response schema wrapping a single task entity."""

    msg: TaskRelEntitySchema


class TaskListResponse(ResponseBase):
    """Response schema for paginated task list retrieval."""

    msg: list[TaskRelEntitySchema]


class TaskCountResponse(ResponseBase):
    """Response schema for task count."""

    msg: int


class TaskBoolResponse(ResponseBase):
    """Response schema for boolean result operations."""

    msg: bool
