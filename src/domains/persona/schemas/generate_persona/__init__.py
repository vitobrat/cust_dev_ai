"""Persona generation schemas package."""

from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.input_data import (
    BaseInputData,
    InputData,
)
from src.domains.persona.schemas.generate_persona.persona_blocks import (
    PersonalInfoBlock,
    ProblemBlock,
    PsychographicBehaviorBlock,
    SocialBlock,
)
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonaSchema,
    GeneratePersonasOutputSchema,
    GeneratePersonasSchema,
    PersonaSchema,
)

__all__ = [  # noqa: WPS410
    "BaseInputData",
    "DemographicAttributePersona",
    "GeneratePersonaSchema",
    "GeneratePersonasOutputSchema",
    "GeneratePersonasSchema",
    "InputData",
    "PersonalInfoBlock",
    "PersonaSchema",
    "ProblemBlock",
    "PsychographicBehaviorBlock",
    "SocialBlock",
]
