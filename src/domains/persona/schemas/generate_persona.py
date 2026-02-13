import operator
from typing import Annotated, List, Optional, TypedDict

from pydantic import BaseModel, Field

from src.domains.persona.schemas.base import Gender, GeographicalLocation


class PersonalInfoBlock(BaseModel):
    name: str = Field(..., description="The name of the persona.")
    age: int = Field(..., description="The age of the persona.")
    marital_status: str = Field(..., description="The marital status of the persona.")
    gender: Gender = Field(..., description="The gender of the persona.")


class ProblemBlock(BaseModel):
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


class DemographicAttributePersona(BaseModel):
    personal_info_block: PersonalInfoBlock = Field(..., description="The personal information block of the persona.")
    problem_block: ProblemBlock = Field(..., description="The problem block of the persona.")
    social_block: SocialBlock = Field(..., description="The social block of the persona.")
    psychographic_behavior_block: PsychographicBehaviorBlock = Field(
        ...,
        description="The psychographic behavior block of the persona.",
    )

    @property
    def demographic_info(self) -> str:
        """Formatted persona description ready to be used in prompts"""
        return "\n".join(
            [
                self.personal_info,
                self.problem_info,
                self.social_info,
                self.psychographic_behavior_info,
            ],
        )

    @property
    def personal_info(self) -> str:
        """Build a formatted string of the personal information block."""
        personal_info_block = self.personal_info_block

        lines = []

        lines.append("Persona Profile:")
        lines.append(f"• Name: {personal_info_block.name}")
        lines.append(f"• Age: {personal_info_block.age}")
        lines.append(f"• Gender: {personal_info_block.gender.value}")
        lines.append(f"• Marital status: {personal_info_block.marital_status}")
        lines.append("")

        return "\n".join(lines)

    @property
    def problem_info(self) -> str:
        """Build a formatted string of the problem block."""
        problem_block = self.problem_block

        lines = []

        lines.append("Main Problem:")
        lines.append(f"• Problem: {problem_block.persona_specific_problem}")
        lines.append(f"• Time & money spent trying to solve it: {problem_block.problem_spendings}")
        lines.append(f"• Level of suffering: {problem_block.person_suffering}")
        lines.append(f"• Trying to manage budget for this: {'Yes' if problem_block.is_manage_budget else 'No'}")
        lines.append("")

        return "\n".join(lines)

    @property
    def social_info(self) -> str:
        """Build a formatted string of the social block."""
        social_block = self.social_block

        lines = []

        lines.append("Social & Demographic Information:")
        lines.append(f"• Location: {social_block.geographical_location.value.replace('_', ' ').title()}")
        lines.append(f"• Education: {social_block.education}")
        lines.append(f"• Profession: {social_block.profession}")
        lines.append(f"• Social status & lifestyle: {social_block.social_status}")
        lines.append("")

        return "\n".join(lines)

    @property
    def psychographic_behavior_info(self) -> str:
        """Build a formatted string of the psychographic behavior block."""
        psychographic_behavior_block = self.psychographic_behavior_block

        lines = []

        lines.append("Psychographics & Behavior:")
        lines.append(f"• Psychological profile: {psychographic_behavior_block.psychological_profile}")
        lines.append(f"• Ideological beliefs: {psychographic_behavior_block.idealogical_beliefs}")
        lines.append(f"• Technology adoption: {psychographic_behavior_block.technology_adoption}")
        lines.append(f"• Communication style: {psychographic_behavior_block.communication_style}")

        return "\n".join(lines)


class BaseInputData(BaseModel):
    segment_name: str = Field(..., description="The name of the user segment associated with the persona.")
    segment_description: str = Field(
        ...,
        description="The description of the user segment associated with the persona.",
    )


class InputData(BaseInputData):
    person_count: int = Field(..., description="The number of personas to create.")


class PersonaSchema(BaseModel):
    demographic_attributes: DemographicAttributePersona = Field(
        ...,
        description="The demographic attributes of the persona.",
    )
    biography: str = Field(..., description="The biography of the persona.")
    experiences: str = Field(..., description="The experiences of the persona with problem.")


class GeneratePersonaSchema(TypedDict):
    input_data: BaseInputData = Field(..., description="The input data used to generate the persona.")
    demographic_attributes: Optional[DemographicAttributePersona] = Field(
        None,
        description="The demographic attributes of the persona.",
    )
    biography: Optional[str] = Field(
        None,
        description="The biography of the persona.",
    )
    experiences: Optional[str] = Field(
        None,
        description="The experiences of the persona with problem.",
    )


class GeneratePersonasSchema(TypedDict):
    input_data: InputData
    personas: Annotated[List[PersonaSchema], operator.add]
