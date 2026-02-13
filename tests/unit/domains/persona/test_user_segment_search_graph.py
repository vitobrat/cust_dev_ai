"""Unit tests for the user segment search graph operations."""

from __future__ import annotations

import pytest
from langchain_core.messages import SystemMessage

from src.domains.persona.infrastructure.graph.user_segment_search import (
    UserSegmentSearchGraph,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.user_segment_search import (
    FindUserSegmentOutput,
    InputData,
    UserSegment,
    UserSegmentSearchOutputSchema,
    UserSegmentSearchSchema,
    VerificationSegmentOutput,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


@pytest.mark.asyncio
async def test_analyse_user_prompt_updates_state(
    user_segment_search_graph: UserSegmentSearchGraph,
    mock_persona_prompt_builder: PersonaPromptManager,
    mock_llm_adapter: LLMAdapter,
) -> None:
    """Ensure analyse node writes the LLM text into the shared state."""

    state = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="segment request"),
    )

    await user_segment_search_graph._analyse_user_prompt(state)

    mock_persona_prompt_builder.build_analyse_user_prompt.assert_called_once_with(
        user_prompt="segment request",
        previous_segments="",
    )
    mock_llm_adapter.ainvoke.assert_awaited_once_with([SystemMessage(content="analyse prompt")])
    assert state.analysis_result == "llm adapter ainvoke"


@pytest.mark.asyncio
async def test_find_user_segment_appends_history_item(
    user_segment_search_graph: UserSegmentSearchGraph,
    mock_persona_prompt_builder: PersonaPromptManager,
    mock_llm_adapter: LLMAdapter,
) -> None:
    """Confirm the find node stores the structured response in history."""

    structured_response = FindUserSegmentOutput(
        segment_name="CloudOps Leaders",
        segment_description="Teams automating deployment pipelines.",
        comments_for_improvement="Add persona context.",
        unifying_problem="Manual pipelines slow releases",
        where_to_find="DevOps forums",
    )
    mock_llm_adapter.structured_ainvoke.return_value = structured_response

    state = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="deploy", person_count=1),
        analysis_result="analysis payload",
    )

    await user_segment_search_graph._find_user_segment(state)

    mock_persona_prompt_builder.build_find_user_segment_prompt.assert_called_once_with(
        user_prompt="deploy",
        analysis_result="analysis payload",
    )
    mock_llm_adapter.structured_ainvoke.assert_awaited_once_with(
        [SystemMessage(content="find prompt")],
        FindUserSegmentOutput,
    )
    assert len(state.segments_history) == 1
    last_segment = state.segments_history[-1]
    assert last_segment.segment_name == "CloudOps Leaders"
    assert last_segment.where_to_find == "DevOps forums"


@pytest.mark.asyncio
async def test_verify_user_segment_requires_history(
    user_segment_search_graph: UserSegmentSearchGraph,
) -> None:
    """The verification node should reject empty histories."""

    state = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="x"),
    )

    with pytest.raises(ValueError):
        await user_segment_search_graph._verify_user_segment(state)


@pytest.mark.asyncio
async def test_verify_user_segment_sets_result(
    user_segment_search_graph: UserSegmentSearchGraph,
    mock_persona_prompt_builder: PersonaPromptManager,
    mock_llm_adapter: LLMAdapter,
) -> None:
    """Verify node should populate the verification result on success."""

    segment = UserSegment(
        segment_name="Automation Architects",
        segment_description="Focus on resilient pipelines",
        comments_for_improvement="Share success metrics.",
        unifying_problem="Manual toil",
        where_to_find="Infra communities",
    )
    structured_response = VerificationSegmentOutput(
        reasoning="Sound rationale",
        is_valid=True,
        comments_for_improvement=None,
    )
    mock_llm_adapter.structured_ainvoke.return_value = structured_response
    state = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="x"),
        segments_history=[segment],
    )

    await user_segment_search_graph._verify_user_segment(state)

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
    assert state.verification_result is structured_response


@pytest.mark.asyncio
async def test_output_node_returns_final_segment(
    user_segment_search_graph: UserSegmentSearchGraph,
) -> None:
    """Output node should produce output schema from the latest segment."""

    segment = UserSegment(
        segment_name="Quality Leads",
        segment_description="Teams obsessed with testing",
        comments_for_improvement=None,
        unifying_problem="",
        where_to_find="QA chats",
    )
    state = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="qa"),
        segments_history=[segment],
    )

    result = await user_segment_search_graph._output_node(state)

    assert isinstance(result, UserSegmentSearchOutputSchema)
    assert result.segment_name == "Quality Leads"
    assert result.segment_description == "Teams obsessed with testing"


@pytest.mark.asyncio
async def test_output_node_requires_segment(
    user_segment_search_graph: UserSegmentSearchGraph,
) -> None:
    """Output node should raise if no segments exist."""

    state = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="qa"),
    )

    with pytest.raises(ValueError):
        await user_segment_search_graph._output_node(state)


@pytest.mark.asyncio
async def test_check_verification_result_favors_output(
    user_segment_search_graph: UserSegmentSearchGraph,
) -> None:
    """Conditional transition should return the appropriate next node."""

    state_valid = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="x", person_count=1),
        verification_result=VerificationSegmentOutput(
            reasoning="ok",
            is_valid=True,
            comments_for_improvement=None,
        ),
    )
    state_invalid = UserSegmentSearchSchema(
        input_data=InputData(user_prompt="x", person_count=1),
        verification_result=VerificationSegmentOutput(
            reasoning="ok",
            is_valid=False,
            comments_for_improvement=None,
        ),
    )

    assert await user_segment_search_graph._check_verification_result(state_valid) == "output"
    assert await user_segment_search_graph._check_verification_result(state_invalid) == "analyse_user_prompt"
