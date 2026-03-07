"""Sub-interview domain schemas.

This module defines Pydantic schemas for sub-interview creation, updates, and entity representation.
Sub-interviews represent individual conversation sessions within a larger interview context.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict

from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.schemas.base import VerboseBase

if TYPE_CHECKING:
    from src.schemas.interview import InterviewEntitySchema


class CreateSubInterviewSchema(BaseModel):
    """Schema for creating a new sub-interview.

    Attributes:
        chat_history: Dictionary containing the conversation history and metadata.
        status: Current status of the sub-interview (e.g., in_progress, completed).
        interview_id: UUID of the parent interview this sub-interview belongs to.
    """

    chat_history: dict[str, Any]
    status: SubInterviewStatus
    interview_id: uuid.UUID


class UpdateSubInterviewSchema(BaseModel):
    """Schema for updating an existing sub-interview.

    All fields are optional to support partial updates.

    Attributes:
        chat_history: Updated conversation history dictionary.
        status: Updated sub-interview status.
    """

    chat_history: Optional[dict[str, Any]] = None
    status: Optional[SubInterviewStatus] = None


class SubInterviewEntitySchema(VerboseBase, CreateSubInterviewSchema):
    """Complete sub-interview entity schema with timestamps and relations.

    Extends CreateSubInterviewSchema with database-generated fields and relationships.

    Attributes:
        created_at: Timestamp when the sub-interview was created.
        interview: Parent interview entity (lazy-loaded relationship).
    """

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubInterviewRelEntitySchema(SubInterviewEntitySchema):
    interview: "InterviewEntitySchema"
