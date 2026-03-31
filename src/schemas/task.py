"""Task domain schemas.

This module defines Pydantic schemas for task creation, updates, and entity representation.
Tasks represent background jobs or operations with status tracking and progress monitoring.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.domains.task.app.constants import TaskStatus, TaskType
from src.schemas.api_base import VerboseBase

if TYPE_CHECKING:
    from src.schemas.user import UserEntitySchema


class CreateTaskSchema(BaseModel):
    """Schema for creating a new task.

    Attributes:
        type: Type of the task (e.g., data processing, report generation).
        status: Current status of the task execution.
        progress: Task completion progress as a float between 0.0 and 1.0.
        error_log: Optional error message if task execution failed.
        input_params: Dictionary containing task input parameters and configuration.
        user_id: UUID of the user who created the task.
    """

    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    progress: float = Field(default=0, ge=0, le=1.0)
    error_log: Optional[str] = None
    input_params: dict[str, Any]
    user_id: uuid.UUID


class TaskSchema(CreateTaskSchema):
    """Full task representation stored in the queue.

    Attributes:
        task_id: Unique identifier assigned at creation time.
        status: Current execution status. Defaults to ``pending``.
        progress: Completion ratio from 0.0 to 1.0. Defaults to 0.
        error_log: Error message if the task has failed.
    """

    task_id: uuid.UUID


class UpdateTaskSchema(BaseModel):
    """Schema for updating an existing task.

    All fields are optional to support partial updates.

    Attributes:
        type: Updated task type.
        status: Updated task status.
        progress: Updated task progress (0.0 to 1.0).
        error_log: Updated error log message.
        input_params: Updated input parameters dictionary.
    """

    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    progress: Optional[float] = Field(default=None, ge=0, le=1.0)
    error_log: Optional[str] = None
    input_params: Optional[dict[str, Any]] = None


class TaskEntitySchema(VerboseBase, CreateTaskSchema):
    """Complete task entity schema with timestamps and relations.

    Extends CreateTaskSchema with database-generated fields and relationships.

    Attributes:
        created_at: Timestamp when the task was created.
        updated_at: Timestamp when the task was last updated.
        user: User entity who owns this task (lazy-loaded relationship).
    """

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskRelEntitySchema(TaskEntitySchema):
    user: "UserEntitySchema"
