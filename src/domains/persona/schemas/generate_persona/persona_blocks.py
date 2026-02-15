"""Persona block models for demographic attributes."""

from pydantic import BaseModel, Field

from src.domains.persona.schemas.base import Gender, GeographicalLocation


class PersonalInfoBlock(BaseModel):
    """Personal information block of the persona."""

    name: str = Field(..., description="The name of the persona.")
    age: int = Field(..., description="The age of the persona.")
    marital_status: str = Field(..., description="The marital status of the persona.")
    gender: Gender = Field(..., description="The gender of the persona.")


class ProblemBlock(BaseModel):
    """Problem block describing persona's main challenges."""

    persona_specific_problem: str = Field(..., description="A specific problem that the persona faces.")
    problem_spendings: str = Field(
        ...,
        description="How much the persona spends time and money on solving this problem.",
    )
    person_suffering: str = Field(..., description="How much the persona suffers from this problem.")
    is_manage_budget: bool = Field(
        ...,
        description="Whether the persona is managing a budget for solving this problem.",
    )


class SocialBlock(BaseModel):
    """Social and demographic information block."""

    geographical_location: GeographicalLocation = Field(..., description="The geographical location of the persona.")
    education: str = Field(
        ...,
        description="The level of education of the character with a description of where the education was received.",
    )
    social_status: str = Field(
        ...,
        description="The social status of the persona with a description of their lifestyle and social interactions.",
    )
    profession: str = Field(
        ...,
        description="The profession of the persona with a description of their job role and industry or homewife.",
    )


class PsychographicBehaviorBlock(BaseModel):
    """Psychographic and behavioral characteristics block."""

    psychological_profile: str = Field(
        ...,
        description="The psychological profile of the persona including traits, values, and attitudes.",
    )
    idealogical_beliefs: str = Field(
        ...,
        description="The ideological beliefs of the persona including political views, "
        "religious beliefs, and cultural values.",
    )
    technology_adoption: str = Field(
        ...,
        description="The technology adoption behavior of the persona including their "
        "comfort level with technology and preferred devices or platforms.",
    )
    communication_style: str = Field(
        ...,
        description="The communication style of the persona including their preferred methods "
        "of communication and frequency of interaction.",
    )
