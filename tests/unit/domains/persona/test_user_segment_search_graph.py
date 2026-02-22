"""Unit tests for the user segment search graph operations."""

from __future__ import annotations

import pytest
from langchain_core.messages import SystemMessage

from src.domains.persona.infrastructure.graph.user_segment_search import (
    UserSegmentSearchGraph,
)
from src.domains.persona.schemas.user_segment_search import (
    FindUserSegmentOutput,
    UserSegment,
    UserSegmentSearchOutputSchema,
    UserSegmentSearchSchema,
    VerificationSegmentOutput,
)
from src.infrastructure.containers.root import RootContainer


@pytest.mark.asyncio
async def test_analyse_user_prompt_updates_state(
    container: RootContainer,
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
) -> None:
    """Ensure analyse node writes the LLM text into the shared state."""
    mock_llm_adapter = container.infrastructure.llm_adapter()
    mock_persona_prompt_builder = container.domain.persona.prompt_builder()

    await user_segment_search_graph._analyse_user_prompt(user_segment_search_state)

    mock_persona_prompt_builder.build_analyse_user_prompt.assert_called_once_with(
        user_prompt="user prompt",
        previous_segments="",
    )
    mock_llm_adapter.ainvoke.assert_awaited_once_with([SystemMessage(content="analyse prompt")])
    assert user_segment_search_state.analysis_result == "llm adapter ainvoke"


@pytest.mark.asyncio
async def test_find_user_segment_appends_history_item(
    container: RootContainer,
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
) -> None:
    """Confirm the find node stores the structured response in history."""
    mock_llm_adapter = container.infrastructure.llm_adapter()
    mock_persona_prompt_builder = container.domain.persona.prompt_builder()

    structured_response = FindUserSegmentOutput(
        segment_name="CloudOps Leaders",
        segment_description="Teams automating deployment pipelines.",
        comments_for_improvement="Add persona context.",
        unifying_problem="Manual pipelines slow releases",
        where_to_find="DevOps forums",
    )
    mock_llm_adapter.structured_ainvoke.return_value = structured_response

    await user_segment_search_graph._find_user_segment(user_segment_search_state)

    mock_persona_prompt_builder.build_find_user_segment_prompt.assert_called_once_with(
        user_prompt="user prompt",
        analysis_result="analysis payload",
    )
    mock_llm_adapter.structured_ainvoke.assert_awaited_once_with(
        [SystemMessage(content="find prompt")],
        FindUserSegmentOutput,
    )
    assert len(user_segment_search_state.segments_history) == 1
    last_segment = user_segment_search_state.segments_history[-1]
    assert last_segment.segment_name == "CloudOps Leaders"
    assert last_segment.where_to_find == "DevOps forums"


@pytest.mark.asyncio
async def test_verify_user_segment_requires_history(
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
) -> None:
    """The verification node should reject empty histories."""

    with pytest.raises(ValueError):
        await user_segment_search_graph._verify_user_segment(user_segment_search_state)


@pytest.mark.asyncio
async def test_verify_user_segment_sets_result(
    container: RootContainer,
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
    user_segment_state: UserSegment,
    verification_state: VerificationSegmentOutput,
) -> None:
    """Verify node should populate the verification result on success."""
    mock_llm_adapter = container.infrastructure.llm_adapter()
    mock_persona_prompt_builder = container.domain.persona.prompt_builder()

    mock_llm_adapter.structured_ainvoke.return_value = verification_state
    user_segment_search_state.segments_history = [user_segment_state]

    await user_segment_search_graph._verify_user_segment(user_segment_search_state)

    mock_persona_prompt_builder.build_verify_user_segment_prompt.assert_called_once_with(
        segment_name="Automation Architects",
        unifying_problem_segment="Manual toil",
        where_to_find_segment="Infra communities",
        segment_description="Focus on resilient pipelines",
    )
    mock_llm_adapter.structured_ainvoke.assert_awaited_once_with(
        [SystemMessage(content="verify prompt")],
        VerificationSegmentOutput,
    )
    assert user_segment_search_state.verification_result is verification_state


@pytest.mark.asyncio
async def test_output_node_returns_final_segment(
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
    user_segment_state: UserSegment,
) -> None:
    """Output node should produce output schema from the latest segment."""

    user_segment_search_state.segments_history = [user_segment_state]

    graph_result = await user_segment_search_graph._output_node(user_segment_search_state)

    assert isinstance(graph_result, UserSegmentSearchOutputSchema)
    assert graph_result.segment_name == "Automation Architects"
    assert graph_result.segment_description == "Focus on resilient pipelines"


@pytest.mark.asyncio
async def test_output_node_requires_segment(
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
) -> None:
    """Output node should raise if no segments exist."""

    with pytest.raises(ValueError):
        await user_segment_search_graph._output_node(user_segment_search_state)


@pytest.mark.asyncio
async def test_check_verification_result_favors_output(
    user_segment_search_graph: UserSegmentSearchGraph,
    user_segment_search_state: UserSegmentSearchSchema,
    verification_state: VerificationSegmentOutput,
) -> None:
    """Conditional transition should return the appropriate next node."""

    user_segment_search_state.verification_result = verification_state
    assert await user_segment_search_graph._check_verification_result(user_segment_search_state) == "output"

    verification_state.is_valid = False
    user_segment_search_state.verification_result = verification_state
    assert (
        await user_segment_search_graph._check_verification_result(user_segment_search_state) == "analyse_user_prompt"
    )
