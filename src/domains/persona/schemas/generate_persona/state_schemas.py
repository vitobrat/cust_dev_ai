"""State and output schemas for persona generation workflows."""

import operator
from typing import Annotated, Any, List, Optional, TypedDict

from pydantic import BaseModel, BeforeValidator

from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.input_data import (
    BaseInputData,
    InputData,
)


def coerce_none_to_str(str_value: Any) -> str:
    return str_value if str_value else ""


# Определение типа с валидатором
CleanStr = Annotated[str, BeforeValidator(coerce_none_to_str)]


class PersonaSchema(BaseModel):
    demographic_attributes: DemographicAttributePersona
    biography: CleanStr = ""
    experiences: CleanStr = ""


class GeneratePersonaInputSchema(TypedDict):
    """Input state accepted by ``GenerateSinglePersonaGraph``."""

    input_data: BaseInputData


class GeneratePersonaSchema(GeneratePersonaInputSchema):
    """State schema for single persona generation workflow."""

    demographic_attributes: Optional[DemographicAttributePersona]
    biography: Optional[str]
    experiences: Optional[str]


class GeneratePersonasInputSchema(TypedDict):
    """Input state accepted by ``GeneratePersonasGraph``."""

    input_data: InputData


class GeneratePersonasSchema(GeneratePersonasInputSchema):
    """State schema for multiple personas generation workflow."""

    personas: Annotated[List[PersonaSchema], operator.add]


class GeneratePersonasOutputSchema(TypedDict):
    """Output schema for multiple personas generation."""

    personas: Annotated[List[PersonaSchema], operator.add]
