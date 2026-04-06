"""Persona schema module for data validation and serialization.

This module defines Pydantic schemas for Persona entities, including
creation, update, and entity representation with proper validation
and type safety.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonaInputData,
    GeneratePersonasInputData,
)
from src.domains.persona.schemas.user_segment_search import (
    UserSegmentSearchInputData,
)
from src.schemas.api_base import VerboseBase

if TYPE_CHECKING:
    from src.schemas.interview import InterviewEntitySchema


class PersonasPipelineTaskInputData(UserSegmentSearchInputData):
    """Task input for the full persona generation pipeline.

    Triggers user segment search followed by batch persona generation.
    Extends ``UserSegmentSearchInputData`` with a discriminator tag,
    interview reference, and desired persona count.

    Attributes:
        task_type: Discriminator literal used by the ``Discriminator``
            validator on ``CreateTaskSchema.input_params``.
        interview_id: UUID of the interview that triggered generation.
        person_count: Number of personas to generate for the discovered segment.
    """

    task_type: Literal["personas_pipeline"] = "personas_pipeline"
    interview_id: uuid.UUID
    person_count: int = Field(..., description="The number of personas to create.")


class GenerateSinglePersonaTaskInputData(GeneratePersonaInputData):
    """Task input for generating a single persona.

    Extends graph-level input with a discriminator tag and interview
    reference so the Redis worker can route and persist correctly.

    Attributes:
        task_type: Discriminator literal used by the ``Discriminator``
            validator on ``CreateTaskSchema.input_params``.
        interview_id: UUID of the interview that triggered generation.
    """

    task_type: Literal["single_persona_generation"] = "single_persona_generation"
    interview_id: uuid.UUID


class GeneratePersonasTaskInputData(GeneratePersonasInputData):
    """Task input for batch persona generation.

    Extends graph-level input with a discriminator tag and interview
    reference so the Redis worker can route and persist correctly.

    Attributes:
        task_type: Discriminator literal used by the ``Discriminator``
            validator on ``CreateTaskSchema.input_params``.
        interview_id: UUID of the interview that triggered generation.
    """

    task_type: Literal["personas_generation"] = "personas_generation"
    interview_id: uuid.UUID


class CreatePersonaSchema(BaseModel):
    """Schema for creating a new persona.

    This schema validates input data when creating a persona entity,
    ensuring all required fields are present and properly typed.

    Attributes:
        demographic_state: Demographic attributes of the persona including
            age, gender, location, and other demographic information.
        bio_description: Textual biography describing the persona's background,
            experiences, and characteristics.
        is_verified: Flag indicating whether the persona has been verified
            by a human or validation process. Defaults to False.
        interview_id: UUID of the associated interview that generated this persona.
    """

    demographic_state: DemographicAttributePersona
    bio_description: str = Field(min_length=1)
    is_verified: bool = False
    interview_id: uuid.UUID


class UpdatePersonasSchema(BaseModel):
    """Schema for updating an existing persona.

    This schema allows partial updates to persona entities. All fields
    are optional, and only provided fields will be updated.

    Attributes:
        demographic_state: Optional updated demographic attributes.
        bio_description: Optional updated biography description.
        is_verified: Optional updated verification status.
        interview_id: Optional updated interview association.
    """

    demographic_state: Optional[DemographicAttributePersona] = None
    bio_description: Optional[str] = Field(default=None, min_length=1)
    is_verified: Optional[bool] = None


class PersonaEntitySchema(VerboseBase, CreatePersonaSchema):
    """Complete persona entity schema with metadata.

    This schema represents a full persona entity as stored in the database,
    including all creation fields plus system-generated metadata like
    timestamps and related interview data.

    Attributes:
        demographic_state: Demographic attributes of the persona.
        bio_description: Biography describing the persona.
        is_verified: Verification status flag.
        interview_id: UUID of the associated interview.
        created_at: Timestamp when the persona was created.
        updated_at: Timestamp when the persona was last updated.
        interview: Full interview entity associated with this persona.
    """

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonaRelEntitySchema(PersonaEntitySchema):
    interview: "InterviewEntitySchema"
