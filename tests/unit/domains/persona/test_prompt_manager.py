from __future__ import annotations

from langchain_core.messages import SystemMessage

from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)


def test_build_analyse_user_prompt_templates_update_content(
    persona_prompt_manager: PersonaPromptManager,
) -> None:
    """Validate that analyse prompt populates both user prompt and segments context."""

    user_prompt = "Need segmentation insights"
    previous_segments = "Segment A; Segment B"
    messages = persona_prompt_manager.build_analyse_user_prompt(user_prompt, previous_segments)

    assert len(messages) == 1
    message = messages[0]
    assert isinstance(message, SystemMessage)
    assert message.content == "Analyse command: Need segmentation insights :: Segment A; Segment B"


def test_build_find_user_segment_prompt_handles_missing_analysis_result(
    persona_prompt_manager: PersonaPromptManager,
) -> None:
    """Ensure find segment prompt emits the example block even when analysis_result is None."""

    content = persona_prompt_manager.build_find_user_segment_prompt(
        "A future CloudOps leader",
        None,
    )[0].content

    assert "None" in content
    assert "Find output example" in content


def test_build_verify_user_segment_prompt_includes_optional_details(
    persona_prompt_manager: PersonaPromptManager,
) -> None:
    """Check that verify prompt serializes optional segment metadata without errors."""

    content = persona_prompt_manager.build_verify_user_segment_prompt(
        segment_name="DataOps Visionaries",
        unifying_problem_segment=None,
        where_to_find_segment=None,
        segment_description="Teams needing real-time observability",
    )[0].content

    assert "DataOps Visionaries" in content
    assert "None" in content
    assert "Verify output example" in content


def test_build_generate_persona_prompt_incorporates_output_example(
    persona_prompt_manager: PersonaPromptManager,
) -> None:
    """Assert that generate persona prompt merges the provided description with the sample output."""

    content = persona_prompt_manager.build_generate_persona_prompt(
        segment_name="Sustainable Infrastructure Leads",
        segment_description="Leaders investing in energy-efficient clusters",
    )[0].content

    assert "Sustainable Infrastructure Leads" in content
    assert "Leaders investing in energy-efficient clusters" in content
    assert "Persona generation output sample" in content


def test_build_generate_persona_biography_prompt_returns_combined_attributes(
    persona_prompt_manager: PersonaPromptManager,
) -> None:
    """Verify that the biography prompt exposes demographic attributes verbatim."""

    attributes = ("Analytical, prefers async updates", "segment description")
    content = persona_prompt_manager.build_generate_persona_biography_prompt(*attributes)[0].content

    assert "Analytical, prefers async updates" in content
    assert "segment description" in content


def test_build_generate_persona_experiences_prompt_injects_description(
    persona_prompt_manager: PersonaPromptManager,
) -> None:
    """Confirm that experiences prompt includes the segment description along with attributes."""

    content = persona_prompt_manager.build_generate_persona_experiences_prompt(
        demographic_attributes="Early adopter",
        segment_description="Needs compliance automation",
    )[0].content

    assert "Early adopter" in content
    assert "Needs compliance automation" in content
