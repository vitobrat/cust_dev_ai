"""User domain schemas.

This module defines Pydantic schemas for user creation, updates, and entity representation.
Users are the primary actors in the system who create interviews and tasks.
"""

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.configs.consts import USER_NAME_MAX_LENGTH
from src.schemas.api_base import VerboseBase

if TYPE_CHECKING:
    from src.schemas.interview import InterviewEntitySchema
    from src.schemas.task import TaskEntitySchema


class CreateUserSchema(BaseModel):
    """Schema for creating a new user.

    Attributes:
        name: User's display name, limited to 256 characters.
    """

    name: str = Field(max_length=USER_NAME_MAX_LENGTH, min_length=1)


class UpdateUserSchema(BaseModel):
    """Schema for updating an existing user.

    All fields are optional to support partial updates.

    Attributes:
        name: Updated user display name.
    """

    name: Optional[str] = Field(default=None, max_length=USER_NAME_MAX_LENGTH, min_length=1)


class UserEntitySchema(VerboseBase, CreateUserSchema):
    """Complete user entity schema with relations.

    Extends CreateUserSchema with relationships to other entities.

    Attributes:
        interviews: List of interviews created by this user.
        tasks: List of tasks created by this user.
    """

    model_config = ConfigDict(from_attributes=True)


class UserRelEntitySchema(UserEntitySchema):
    interviews: list["InterviewEntitySchema"] = []
    tasks: list["TaskEntitySchema"] = []
