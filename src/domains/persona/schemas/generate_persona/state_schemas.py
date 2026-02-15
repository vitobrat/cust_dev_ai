"""State and output schemas for persona generation workflows."""

import operator
from typing import Annotated, List, Optional, TypedDict

from pydantic import BaseModel, Field

from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.input_data import (
    BaseInputData,
    InputData,
)


class PersonaSchema(BaseModel):
    """Complete persona schema with all attributes."""

    demographic_attributes: DemographicAttributePersona = Field(
        ...,
        description="The demographic attributes of the persona.",
    )
    biography: str = Field(..., description="The biography of the persona.")
    experiences: str = Field(..., description="The experiences of the persona with problem.")


class GeneratePersonaSchema(TypedDict):
    """State schema for single persona generation workflow."""

    input_data: BaseInputData
    demographic_attributes: Optional[DemographicAttributePersona]
    biography: Optional[str]
    experiences: Optional[str]


class GeneratePersonasSchema(TypedDict):
    """State schema for multiple personas generation workflow."""

    input_data: InputData
    personas: Annotated[List[PersonaSchema], operator.add]


class GeneratePersonasOutputSchema(TypedDict):
    """Output schema for multiple personas generation."""

    personas: Annotated[List[PersonaSchema], operator.add]
