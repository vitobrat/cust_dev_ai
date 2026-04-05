"""Unit tests for the generate single persona graph operations."""

from __future__ import annotations

import pytest
from langchain_core.messages import SystemMessage

from src.domains.persona.infrastructure.graph.generate_single_persona import (
    GenerateSinglePersonaGraph,
)
from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.input_data import (
    BaseInputData,
)
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonaSchema,
    PersonaSchema,
)
from src.infrastructure.containers.root import RootContainer


@pytest.mark.asyncio
async def test_generate_persona_attribute_updates_state(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    container: RootContainer,
    generate_persona_state: GeneratePersonaSchema,
    persona: DemographicAttributePersona,
) -> None:
    """Ensure generate_persona_attribute node creates demographic attributes."""
    mock_llm_adapter = container.infrastructure.llm_adapter()
    mock_persona_prompt_builder = container.domain.persona.prompt_builder()

    mock_llm_adapter.structured_ainvoke.return_value = persona

    graph_result = await generate_single_persona_graph._generate_persona_attribute(generate_persona_state)

    mock_persona_prompt_builder.build_generate_persona_prompt.assert_called_once_with(
        segment_name="DevOps Innovators",
        segment_description="Teams automating infrastructure and deployment workflows",
    )
    mock_llm_adapter.structured_ainvoke.assert_awaited_once_with(
        [SystemMessage(content="generate persona prompt")],
        DemographicAttributePersona,
    )
    assert graph_result["demographic_attributes"] == persona


@pytest.mark.asyncio
async def test_generate_persona_attribute_requires_segment_name(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """The generate_persona_attribute node should reject missing segment_name."""

    generate_persona_state["input_data"] = BaseInputData(
        segment_name="",
        segment_description="Some description",
    )

    with pytest.raises(ValueError):
        await generate_single_persona_graph._generate_persona_attribute(generate_persona_state)


@pytest.mark.asyncio
async def test_generate_persona_attribute_requires_segment_description(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """The generate_persona_attribute node should reject missing segment_description."""

    generate_persona_state["input_data"] = BaseInputData(
        segment_name="Test Segment",
        segment_description="",
    )

    with pytest.raises(ValueError):
        await generate_single_persona_graph._generate_persona_attribute(generate_persona_state)


@pytest.mark.asyncio
async def test_generate_persona_biography_creates_narrative(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    container: RootContainer,
    generate_persona_state: GeneratePersonaSchema,
    persona: DemographicAttributePersona,
) -> None:
    """Confirm biography node generates narrative from demographic attributes."""
    mock_llm_adapter = container.infrastructure.llm_adapter()
    mock_persona_prompt_builder = container.domain.persona.prompt_builder()

    generate_persona_state["demographic_attributes"] = persona
    mock_llm_adapter.ainvoke.return_value = "Generated biography text"

    graph_result = await generate_single_persona_graph._generate_persona_biography(generate_persona_state)

    mock_persona_prompt_builder.build_generate_persona_biography_prompt.assert_called_once_with(
        demographic_attributes=persona.demographic_info,
        segment_description=generate_persona_state["input_data"].segment_description,
    )
    mock_llm_adapter.ainvoke.assert_awaited_once_with([SystemMessage(content="biography prompt")])
    assert graph_result["biography"] == "Generated biography text"


@pytest.mark.asyncio
async def test_generate_persona_biography_requires_demographic_attributes(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """Biography node should reject missing demographic attributes."""

    with pytest.raises(ValueError):
        await generate_single_persona_graph._generate_persona_biography(generate_persona_state)


@pytest.mark.asyncio
async def test_generate_persona_biography_validates_attribute_type(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """Biography node should validate demographic attributes type."""

    generate_persona_state["demographic_attributes"] = "invalid type"  # type: ignore[typeddict-item]

    with pytest.raises(ValueError):
        await generate_single_persona_graph._generate_persona_biography(generate_persona_state)


@pytest.mark.asyncio
async def test_generate_persona_experiences_creates_narrative(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    container: RootContainer,
    generate_persona_state: GeneratePersonaSchema,
    persona: DemographicAttributePersona,
) -> None:
    """Confirm experiences node generates problem-related narrative."""

    generate_persona_state["demographic_attributes"] = persona
    mock_llm_adapter = container.infrastructure.llm_adapter()
    mock_llm_adapter.ainvoke.return_value = "Generated experiences text"

    graph_result = await generate_single_persona_graph._generate_persona_experiences(generate_persona_state)

    mock_persona_prompt_builder = container.domain.persona.prompt_builder()
    mock_persona_prompt_builder.build_generate_persona_experiences_prompt.assert_called_once_with(
        demographic_attributes=persona.demographic_info,
        segment_description=generate_persona_state["input_data"].segment_description,
    )
    mock_llm_adapter.ainvoke.assert_awaited_once_with([SystemMessage(content="experiences prompt")])
    assert graph_result["experiences"] == "Generated experiences text"


@pytest.mark.asyncio
async def test_generate_persona_experiences_requires_demographic_attributes(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """Experiences node should reject missing demographic attributes."""

    with pytest.raises(ValueError):
        await generate_single_persona_graph._generate_persona_experiences(generate_persona_state)


@pytest.mark.asyncio
async def test_generate_persona_experiences_validates_attribute_type(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """Experiences node should validate demographic attributes type."""

    generate_persona_state["demographic_attributes"] = "invalid type"  # type: ignore[typeddict-item]

    with pytest.raises(ValueError):
        await generate_single_persona_graph._generate_persona_experiences(generate_persona_state)


@pytest.mark.asyncio
async def test_format_output_combines_all_components(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
    persona: DemographicAttributePersona,
) -> None:
    """Output node should combine demographic attributes, biography, and experiences."""

    generate_persona_state["demographic_attributes"] = persona
    generate_persona_state["biography"] = "Biography narrative"
    generate_persona_state["experiences"] = "Experiences narrative"

    graph_result = await generate_single_persona_graph._format_output(generate_persona_state)

    assert "personas" in graph_result
    assert len(graph_result["personas"]) == 1
    persona_output = graph_result["personas"][0]
    assert isinstance(persona_output, PersonaSchema)
    assert persona_output.demographic_attributes == persona
    assert persona_output.biography == "Biography narrative"
    assert persona_output.experiences == "Experiences narrative"


@pytest.mark.asyncio
async def test_format_output_handles_missing_optional_fields(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
    persona: DemographicAttributePersona,
) -> None:
    """Output node should handle missing biography and experiences gracefully."""

    generate_persona_state["demographic_attributes"] = persona

    graph_result = await generate_single_persona_graph._format_output(generate_persona_state)

    assert "personas" in graph_result
    assert len(graph_result) == 1
    persona_output = graph_result["personas"][0]
    assert persona_output.demographic_attributes == persona
    assert persona_output.biography == ""
    assert persona_output.experiences == ""


@pytest.mark.asyncio
async def test_format_output_requires_demographic_attributes(
    generate_single_persona_graph: GenerateSinglePersonaGraph,
    generate_persona_state: GeneratePersonaSchema,
) -> None:
    """Output node should reject missing demographic attributes."""

    with pytest.raises(ValueError):
        await generate_single_persona_graph._format_output(generate_persona_state)
