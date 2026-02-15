"""Input data models for persona generation."""

from pydantic import BaseModel, Field


class BaseInputData(BaseModel):
    """Base input data for persona generation."""

    segment_name: str = Field(..., description="The name of the user segment associated with the persona.")
    segment_description: str = Field(
        ...,
        description="The description of the user segment associated with the persona.",
    )


class InputData(BaseInputData):
    """Extended input data with persona count."""

    person_count: int = Field(..., description="The number of personas to create.")
