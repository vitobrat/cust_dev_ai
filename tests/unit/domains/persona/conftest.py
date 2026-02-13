from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import SystemMessage

from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.base import Gender, GeographicalLocation
from src.domains.persona.schemas.generate_persona import (
    DemographicAttributePersona,
    PersonalInfoBlock,
    ProblemBlock,
    PsychographicBehaviorBlock,
    SocialBlock,
)
from src.infrastructure.containers.root import RootContainer


@pytest.fixture
def user_segment_search_graph(
    container: RootContainer,
    mock_llm_adapter,
    mock_persona_prompt_builder,
):
    with (
        container.infrastructure.llm_adapter.override(mock_llm_adapter),
        container.domain.persona.prompt_builder.override(mock_persona_prompt_builder),
    ):
        yield container.domain.persona.graph()


@pytest.fixture
def mock_persona_prompt_builder() -> PersonaPromptManager:
    builder: MagicMock = MagicMock(spec=PersonaPromptManager)
    builder.build_analyse_user_prompt.return_value = [SystemMessage(content="analyse prompt")]
    builder.build_find_user_segment_prompt.return_value = [SystemMessage(content="find prompt")]
    builder.build_verify_user_segment_prompt.return_value = [SystemMessage(content="verify prompt")]
    return builder


@pytest.fixture()
def prompt_payloads() -> dict[str, dict[str, str]]:
    return {
        "user_segment_search": {
            "analyse_user_prompt.md": "Analyse command: {user_prompt} :: {previous_segments}",
            "find_user_segment.md": ("Find request: {user_prompt} -> {analysis_result}; example {output_example}"),
            "find_user_segment_output_example.md": "Find output example",
            "verify_user_segment.md": (
                "Verify segment {segment_name} described as {segment_description}."
                " Unified problem {unifying_problem_segment}, find at {where_to_find_segment}."
                " Output sample {output_example}"
            ),
            "verify_user_segment_output_example.md": "Verify output example",
        },
        "demographic_attribute_person": {
            "generate_persona.md": (
                "Generate persona for {segment_name} ({segment_description})." " Sample output {output_example}"
            ),
        },
        "generate_persona": {
            "generate_persona_output_example.md": "Persona generation output sample",
            "generate_persona_biography.md": "Biography narrative: {demographic_attributes}",
            "generate_persona_experiences.md": (
                "Experiences narrative: {demographic_attributes}, {segment_description}"
            ),
        },
    }


@pytest.fixture(name="persona_prompt_manager")
def fixture_persona_prompt_manager(
    tmp_path: Path,
    prompt_payloads: dict[str, dict[str, str]],
) -> PersonaPromptManager:
    """Provide a PersonaPromptManager with controlled templates for prompt builders."""

    prompts_root = tmp_path / "prompts"
    for directory in ("user_segment_search", "demographic_attribute_person", "generate_persona"):
        (prompts_root / directory).mkdir(parents=True, exist_ok=True)

    manager = PersonaPromptManager(prompts_root)
    manager._prompts = prompt_payloads
    return manager


@pytest.fixture(scope="function")
def persona() -> DemographicAttributePersona:
    personal_info = PersonalInfoBlock(
        name="Alex",
        age=34,
        gender=Gender.MALE,
        marital_status="married",
    )
    problem_block = ProblemBlock(
        persona_specific_problem="Scaling pipelines",
        problem_spendings="2 days weekly",
        person_suffering="High",
        is_manage_budget=True,
    )
    social_block = SocialBlock(
        geographical_location=GeographicalLocation.CITY,
        education="Master of distributed systems",
        social_status="Tech lead lifestyle",
        profession="Cloud architect",
    )
    psychographic_behavior_block = PsychographicBehaviorBlock(
        psychological_profile="Analytical decision maker",
        idealogical_beliefs="Believes in transparent ops",
        technology_adoption="Early adopter",
        communication_style="Prefers async updates",
    )

    return DemographicAttributePersona(
        personal_info_block=personal_info,
        problem_block=problem_block,
        social_block=social_block,
        psychographic_behavior_block=psychographic_behavior_block,
    )
