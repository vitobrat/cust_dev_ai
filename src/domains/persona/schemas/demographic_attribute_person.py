import operator
from enum import StrEnum
from typing import Annotated, List, TypedDict

from pydantic import BaseModel, Field


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"


class GeographicalLocation(StrEnum):
    VILLAGE = "village"
    SMALL_TOWN = "small_town"
    MEDIUM_SIZED_TOWN = "medium_sized_town"
    LARGE_TOWN = "large_town"
    CITY = "city"


class PersonalInfoBlock(BaseModel):
    name: str = Field(..., description="The name of the persona.")
    age: int = Field(..., description="The age of the persona.")
    marital_status: str = Field(..., description="The marital status of the persona.")
    gender: Gender = Field(..., description="The gender of the persona.")


class ProblemBlock(BaseModel):
    person_specific_problem: str = Field(..., description="A specific problem that the persona faces.")
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


class DemographicAttributePerson(BaseModel):
    personal_info_block: PersonalInfoBlock = Field(..., description="The personal information block of the persona.")
    problem_block: ProblemBlock = Field(..., description="The problem block of the persona.")
    social_block: SocialBlock = Field(..., description="The social block of the persona.")
    psychographic_behavior_block: PsychographicBehaviorBlock = Field(
        ...,
        description="The psychographic behavior block of the persona.",
    )


class InputData(BaseModel):
    person_count: int = Field(..., description="The number of personas to create.")
    segment_name: str = Field(..., description="The name of the user segment associated with the persona.")
    segment_description: str = Field(
        ...,
        description="The description of the user segment associated with the persona.",
    )


class GenerateDemographicAttributePersonSchema(TypedDict):
    input_data: InputData
    demographic_attributes: Annotated[List[DemographicAttributePerson], operator.add]
