"""Unit tests for the generate personas graph operations."""

from __future__ import annotations

import pytest
from langgraph.types import Send

from src.domains.persona.infrastructure.graph.generate_personas import (
    GeneratePersonasGraph,
)
from src.domains.persona.schemas.generate_persona import (
    BaseInputData,
    GeneratePersonasSchema,
)


@pytest.mark.asyncio
async def test_map_personas_creates_correct_number_of_sends(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Ensure map_personas creates Send objects for each persona count."""

    sends = await generate_personas_graph._map_personas(generate_personas_state)

    assert len(sends) == 3
    for send in sends:
        assert isinstance(send, Send)
        assert send.node == "generate_single_persona"


@pytest.mark.asyncio
async def test_map_personas_propagates_segment_data(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Confirm map_personas passes segment name and description to each Send."""

    sends = await generate_personas_graph._map_personas(generate_personas_state)

    for send in sends:
        assert isinstance(send.arg, dict)
        assert "input_data" in send.arg
        input_data = send.arg["input_data"]
        assert isinstance(input_data, BaseInputData)
        assert input_data.segment_name == "Cloud Infrastructure Leaders"
        assert input_data.segment_description == "Teams managing scalable cloud deployments"


@pytest.mark.asyncio
async def test_map_personas_defaults_to_one_when_count_missing(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Map personas should default to 1 persona when person_count is missing."""

    generate_personas_state["input_data"].person_count = 1

    sends = await generate_personas_graph._map_personas(generate_personas_state)

    assert len(sends) == 1


@pytest.mark.asyncio
async def test_map_personas_requires_segment_name(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Map personas should reject empty segment_name."""

    generate_personas_state["input_data"].segment_name = ""

    with pytest.raises(ValueError):
        await generate_personas_graph._map_personas(generate_personas_state)


@pytest.mark.asyncio
async def test_map_personas_requires_segment_description(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Map personas should reject empty segment_description."""

    generate_personas_state["input_data"].segment_description = ""

    with pytest.raises(ValueError):
        await generate_personas_graph._map_personas(generate_personas_state)


@pytest.mark.asyncio
async def test_map_personas_handles_large_counts(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Verify map_personas can handle larger persona counts."""

    generate_personas_state["input_data"].person_count = 10

    sends = await generate_personas_graph._map_personas(generate_personas_state)

    assert len(sends) == 10
    for send in sends:
        assert send.node == "generate_single_persona"
        assert send.arg["input_data"].segment_name == "Cloud Infrastructure Leaders"


@pytest.mark.asyncio
async def test_map_personas_creates_independent_send_objects(
    generate_personas_graph: GeneratePersonasGraph,
    generate_personas_state: GeneratePersonasSchema,
) -> None:
    """Ensure each Send object has independent input_data instances."""

    sends = await generate_personas_graph._map_personas(generate_personas_state)

    # Verify all Send objects are distinct
    assert len(sends) == len(set(id(send) for send in sends))

    # Verify input_data objects are independent
    input_data_ids = [id(send.arg["input_data"]) for send in sends]
    assert len(input_data_ids) == len(set(input_data_ids))
