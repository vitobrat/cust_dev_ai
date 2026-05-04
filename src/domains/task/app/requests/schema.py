"""Request and response schemas for the Task API endpoints."""

import uuid

from pydantic import BaseModel, Field

from src.configs.consts import INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE
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


class PostInterviewSimulationTaskRequest(BaseModel):
    """Request schema for registering a full interview simulation task in Redis."""

    user_id: uuid.UUID
    interview_id: uuid.UUID
    rewritten_user_request: str = Field(..., min_length=1)
    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    batch_size: int = Field(default=3, ge=1, le=INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE)
    max_iterations_per_interview: int = Field(default=8, ge=1)
    user_controlled_knowledge_context: str = ""
    allow_external_search: bool = True


class PostFinalReportGenerationTaskRequest(BaseModel):
    """Request schema for registering a final interview report generation task in Redis."""

    user_id: uuid.UUID
    interview_id: uuid.UUID


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
