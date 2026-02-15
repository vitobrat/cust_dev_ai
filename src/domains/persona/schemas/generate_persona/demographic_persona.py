"""Demographic attribute persona model with formatting properties."""

from pydantic import BaseModel, Field

from src.domains.persona.schemas.generate_persona.persona_blocks import (
    PersonalInfoBlock,
    ProblemBlock,
    PsychographicBehaviorBlock,
    SocialBlock,
)


class DemographicAttributePersona(BaseModel):
    """Complete demographic attributes of a persona."""

    personal_info_block: PersonalInfoBlock = Field(..., description="The personal information block of the persona.")
    problem_block: ProblemBlock = Field(..., description="The problem block of the persona.")
    social_block: SocialBlock = Field(..., description="The social block of the persona.")
    psychographic_behavior_block: PsychographicBehaviorBlock = Field(
        ...,
        description="The psychographic behavior block of the persona.",
    )

    @property
    def demographic_info(self) -> str:
        """Formatted persona description ready to be used in prompts."""
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
