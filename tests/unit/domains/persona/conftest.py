from __future__ import annotations

from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import SystemMessage

from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.base import Gender, GeographicalLocation
from src.domains.persona.schemas.generate_persona import (
    BaseInputData,
    DemographicAttributePersona,
    GeneratePersonaSchema,
    GeneratePersonasSchema,
)
from src.domains.persona.schemas.generate_persona import (
    InputData as GeneratePersonasInputData,
)
from src.domains.persona.schemas.generate_persona import (
    PersonalInfoBlock,
    ProblemBlock,
    PsychographicBehaviorBlock,
    SocialBlock,
)
from src.domains.persona.schemas.user_segment_search import (
    InputData,
    UserSegment,
    UserSegmentSearchSchema,
    VerificationSegmentOutput,
)
from src.infrastructure.containers.root import RootContainer
from src.infrastructure.llm.llm_adapter import LLMAdapter


@pytest.fixture
def user_segment_search_state() -> UserSegmentSearchSchema:
    return UserSegmentSearchSchema(
        input_data=InputData(user_prompt="user prompt"),
        analysis_result="analysis payload",
    )


@pytest.fixture
def user_segment_state() -> UserSegment:
    return UserSegment(
        segment_name="Automation Architects",
        segment_description="Focus on resilient pipelines",
        comments_for_improvement="Share success metrics.",
        unifying_problem="Manual toil",
        where_to_find="Infra communities",
    )


@pytest.fixture
def verification_state() -> VerificationSegmentOutput:
    return VerificationSegmentOutput(
        reasoning="Sound rationale",
        is_valid=True,
        comments_for_improvement=None,
    )


@pytest.fixture
def user_segment_search_graph(
    container: RootContainer,
    mock_llm_adapter: LLMAdapter,
    mock_persona_prompt_builder: PersonaPromptManager,
) -> Generator[Any, Any, Any]:
    with (
        container.infrastructure.llm_adapter.override(mock_llm_adapter),  # type: ignore[attr-defined]
        container.domain.persona.prompt_builder.override(mock_persona_prompt_builder),  # type: ignore[attr-defined]
    ):
        yield container.domain.persona.user_segment_search_graph()


@pytest.fixture
def mock_persona_prompt_builder() -> PersonaPromptManager:
    builder: MagicMock = MagicMock(spec=PersonaPromptManager)
    builder.build_analyse_user_prompt.return_value = [SystemMessage(content="analyse prompt")]
    builder.build_find_user_segment_prompt.return_value = [SystemMessage(content="find prompt")]
    builder.build_verify_user_segment_prompt.return_value = [SystemMessage(content="verify prompt")]
    builder.build_generate_persona_prompt.return_value = [SystemMessage(content="generate persona prompt")]
    builder.build_generate_persona_biography_prompt.return_value = [SystemMessage(content="biography prompt")]
    builder.build_generate_persona_experiences_prompt.return_value = [SystemMessage(content="experiences prompt")]
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
            "generate_persona_biography.md": "Biography narrative: {demographic_attributes}, "
            "Segment description: {segment_description}",
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
        age=34,  # noqa: WPS432
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


@pytest.fixture
def generate_persona_input_data() -> BaseInputData:
    return BaseInputData(
        segment_name="DevOps Innovators",
        segment_description="Teams automating infrastructure and deployment workflows",
    )


@pytest.fixture
def generate_persona_state(generate_persona_input_data: BaseInputData) -> GeneratePersonaSchema:
    return GeneratePersonaSchema(
        input_data=generate_persona_input_data,
        demographic_attributes=None,
        biography=None,
        experiences=None,
    )


@pytest.fixture
def generate_single_persona_graph(
    container: RootContainer,
    mock_llm_adapter: LLMAdapter,
    mock_persona_prompt_builder: PersonaPromptManager,
) -> Generator[Any, Any, Any]:
    with (
        container.infrastructure.llm_adapter.override(mock_llm_adapter),  # type: ignore[attr-defined]
        container.domain.persona.prompt_builder.override(mock_persona_prompt_builder),  # type: ignore[attr-defined]
    ):
        yield container.domain.persona.generate_single_persona_graph()


@pytest.fixture
def generate_personas_input_data() -> GeneratePersonasInputData:
    return GeneratePersonasInputData(
        segment_name="Cloud Infrastructure Leaders",
        segment_description="Teams managing scalable cloud deployments",
        person_count=3,
    )


@pytest.fixture
def generate_personas_state(generate_personas_input_data: GeneratePersonasInputData) -> GeneratePersonasSchema:
    return GeneratePersonasSchema(
        input_data=generate_personas_input_data,
        personas=[],
    )


@pytest.fixture
def generate_personas_graph(
    container: RootContainer,
    mock_llm_adapter: LLMAdapter,
    mock_persona_prompt_builder: PersonaPromptManager,
) -> Generator[Any, Any, Any]:
    with (
        container.infrastructure.llm_adapter.override(mock_llm_adapter),  # type: ignore[attr-defined]
        container.domain.persona.prompt_builder.override(mock_persona_prompt_builder),  # type: ignore[attr-defined]
    ):
        yield container.domain.persona.generate_personas_graph()
