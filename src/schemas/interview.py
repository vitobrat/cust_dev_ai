"""Interview domain schemas.

This module defines Pydantic schemas for interview creation, updates, and entity representation.
Interviews represent customer development sessions with associated personas and sub-interviews.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.configs.consts import URL_MAX_LENGTH
from src.schemas.base import VerboseBase

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
    user_id: uuid.UUID


class UpdateInterviewSchema(BaseModel):
    """Schema for updating an existing interview.

    All fields are optional to support partial updates.

    Attributes:
        report_content_url: Updated URL to the interview report content.
    """

    report_content_url: Optional[str] = Field(default=None, max_length=URL_MAX_LENGTH)


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
