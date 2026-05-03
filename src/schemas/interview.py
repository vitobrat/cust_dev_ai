"""Interview domain schemas.

This module defines Pydantic schemas for interview creation, updates, and entity representation.
Interviews represent customer development sessions with associated personas and sub-interviews.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from src.configs.consts import (
    INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE,
    URL_MAX_LENGTH,
)
from src.schemas.api_base import VerboseBase

if TYPE_CHECKING:
    from src.schemas.persona import PersonaEntitySchema
    from src.schemas.sub_interview import SubInterviewEntitySchema
    from src.schemas.user import UserEntitySchema


class CreateInterviewSchema(BaseModel):
    """Schema for creating a new interview.

    Attributes:
        report_content_url: Optional URL to the generated interview report content.
        user_id: UUID of the user who created the interview.
    """

    report_content_url: Optional[str] = Field(default=None, max_length=URL_MAX_LENGTH)
    final_report: Optional[dict[str, JsonValue]] = None
    user_id: uuid.UUID


class UpdateInterviewSchema(BaseModel):
    """Schema for updating an existing interview.

    All fields are optional to support partial updates.

    Attributes:
        report_content_url: Updated URL to the interview report content.
    """

    report_content_url: Optional[str] = Field(default=None, max_length=URL_MAX_LENGTH)
    final_report: Optional[dict[str, JsonValue]] = None


class InterviewSimulationTaskInputData(BaseModel):
    """Redis task input for running the full custdev interview simulation cycle.

    The task references an existing interview and loads its generated personas
    from PostgreSQL before running the interview orchestration graph.
    """

    task_type: Literal["interview_simulation"] = "interview_simulation"
    interview_id: uuid.UUID
    rewritten_user_request: str = Field(..., min_length=1)
    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    batch_size: int = Field(default=3, ge=1, le=INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE)
    max_iterations_per_interview: int = Field(default=8, ge=1)
    user_controlled_knowledge_context: str = ""
    allow_external_search: bool = True


class FinalReportGenerationTaskInputData(BaseModel):
    """Redis task input for generating the final analytics report from stored interviews."""

    task_type: Literal["report_generation"] = "report_generation"
    interview_id: uuid.UUID


class InterviewEntitySchema(VerboseBase, CreateInterviewSchema):
    """Complete interview entity schema with timestamps and relations.

    Extends CreateInterviewSchema with database-generated fields and relationships.

    Attributes:
        created_at: Timestamp when the interview was created.
        updated_at: Timestamp when the interview was last updated.
        user: User entity who owns this interview (lazy-loaded relationship).
        personas: List of personas associated with this interview.
        sub_interviews: List of sub-interviews conducted within this interview.
    """

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewRelEntitySchema(InterviewEntitySchema):
    user: "UserEntitySchema"
    personas: list["PersonaEntitySchema"] = []
    sub_interviews: list["SubInterviewEntitySchema"] = []
