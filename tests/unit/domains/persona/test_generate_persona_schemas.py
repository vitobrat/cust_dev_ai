from typing import Callable

import pytest

from src.domains.persona.schemas.base import GeographicalLocation
from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.persona_blocks import (
    SocialBlock,
)
from tests.unit.domains.persona.persona_test_utils import assert_section_present


def test_demographic_info_contains_all_sections(persona: DemographicAttributePersona) -> None:

    demographic_info = persona.demographic_info

    assert_section_present(demographic_info, "persona", "Persona Profile:")
    assert_section_present(demographic_info, "problem", "Main Problem:")
    assert_section_present(demographic_info, "social", "Social & Demographic Information:")
    assert_section_present(demographic_info, "psychographic", "Psychographics & Behavior:")
    assert_section_present(demographic_info, "gender", "• Gender: male")


def test_demographic_info_formats_budget_flag(persona: DemographicAttributePersona) -> None:
    no_persona = persona.model_copy(deep=True)
    no_persona.problem_block.is_manage_budget = False

    assert "Trying to manage budget for this: Yes" in persona.problem_info
    assert "Trying to manage budget for this: No" in no_persona.problem_info


def test_demographic_info_formats_geographical_location(persona: DemographicAttributePersona) -> None:
    persona.social_block.geographical_location = GeographicalLocation.MEDIUM_SIZED_TOWN

    assert "• Location: Medium Sized Town" in persona.demographic_info


@pytest.mark.parametrize(
    "block_builder",
    [
        lambda: SocialBlock(
            geographical_location=GeographicalLocation.CITY,
            education="X",
            social_status="Y",
            profession="Z",
        ),
        lambda: SocialBlock(
            geographical_location=GeographicalLocation.LARGE_TOWN,
            education="A",
            social_status="B",
            profession="C",
        ),
    ],
)
def test_social_block_accepts_every_enum_value(block_builder: Callable[[], SocialBlock]) -> None:
    block = block_builder()
    assert block.geographical_location in GeographicalLocation, "Enum value should be a member"


def test_social_block_rejects_unknown_location() -> None:
    with pytest.raises(ValueError):
        SocialBlock(
            geographical_location="unknown",
            education="E",
            social_status="S",
            profession="P",
        )
