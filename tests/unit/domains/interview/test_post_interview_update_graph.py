"""Unit tests for the post-interview update graph."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.post_interview_update import (
    PostInterviewUpdateGraph,
)
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import (
    InterviewReport,
    PreInterviewPlan,
)
from src.domains.interview.schemas.post_interview_update import (
    PostInterviewUpdateInputData,
    PostInterviewUpdateSchema,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


def _mock_llm_adapter() -> MagicMock:
    llm_adapter = MagicMock(spec=LLMAdapter)
    llm_adapter.structured_ainvoke = AsyncMock()
    return llm_adapter


def _mock_prompt_builder() -> MagicMock:
    return MagicMock(spec=InterviewPromptManager)


def _graph() -> PostInterviewUpdateGraph:
    return PostInterviewUpdateGraph(
        llm_adapter=_mock_llm_adapter(),
        prompt_builder=_mock_prompt_builder(),
    )


def _graph_with_mocks(
    llm_adapter: MagicMock,
    prompt_builder: MagicMock,
) -> PostInterviewUpdateGraph:
    return PostInterviewUpdateGraph(
        llm_adapter=llm_adapter,
        prompt_builder=prompt_builder,
    )


def _real_prompt_builder() -> InterviewPromptManager:
    return InterviewPromptManager(
        prompts_dir=Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt"),
    )


def _pre_interview_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Validate whether discovery-call prep is urgent.",
        main_customer_concerns=["Wasting scarce founder-led sales calls."],
        hidden_risks=["Founder may prefer manual control despite saying automation is useful."],
        base_questions=[
            "Tell me about the last discovery call that did not produce useful evidence.",
            "What did that failure cost you?",
            "What would make you commit to changing the workflow?",
        ],
        expected_ideal_result="A concrete workflow pain and a next-step commitment.",
    )


def _updated_pre_interview_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Validate buying authority and willingness to change the discovery workflow.",
        main_customer_concerns=["Wasting scarce founder-led sales calls."],
        hidden_risks=[
            "Founder may prefer manual control despite saying automation is useful.",
            "Positive feedback may hide lack of budget ownership.",
        ],
        base_questions=[
            "Who would need to approve a paid change to your discovery workflow?",
            "Tell me about the last time poor discovery notes affected a product or sales decision.",
            "What concrete step would you take if this workflow problem was solved next week?",
        ],
        expected_ideal_result="A concrete workflow pain, clear budget ownership, and a next-step commitment.",
    )


def _interview_report() -> InterviewReport:
    return InterviewReport(
        target_information=["Founder loses evidence after discovery calls."],
        important_quotes=["I leave calls with scattered notes and no next step."],
        outcomes_or_agreements=["Agreed to test a structured prep checklist."],
        recommendations_for_next_interviews=[
            "Ask more directly about who owns the budget.",
            "Replace broad workflow questions with last-call reconstruction.",
        ],
        is_successful=True,
        success_score=0.8,
        success_reasoning="The persona gave a concrete pain and agreed to a next step.",
    )


def _input_data() -> PostInterviewUpdateInputData:
    return PostInterviewUpdateInputData(
        previous_pre_interview_plan=_pre_interview_plan(),
        interview_reports=[_interview_report()],
    )


def test_interview_prompt_manager_loads_post_interview_update_templates() -> None:
    """The third-stage graph should have all prompt templates available."""
    prompt_builder = _real_prompt_builder()

    assert prompt_builder.has_template("post_interview_update", "generate_updated_pre_interview_report")
    assert prompt_builder.has_template("post_interview_update", "generate_updated_pre_interview_report_output_example")


def test_post_interview_update_graph_uses_expected_output_contract() -> None:
    """The third-stage graph must expose the updated pre-interview report contract."""
    graph = _graph()

    assert graph.output_schema is not None
    assert graph.output_schema.__name__ == "PostInterviewUpdateOutputSchema"


def test_post_interview_update_input_requires_at_least_one_report() -> None:
    """Plan update must be based on at least one completed interview report."""
    with pytest.raises(ValidationError):
        PostInterviewUpdateInputData(
            previous_pre_interview_plan=_pre_interview_plan(),
            interview_reports=[],
        )


def test_post_interview_update_input_preserves_previous_plan_and_reports() -> None:
    """Input data should carry the old briefing plus all interview reports."""
    input_data = _input_data()

    assert input_data.previous_pre_interview_plan == _pre_interview_plan()
    assert input_data.interview_reports == [_interview_report()]


async def test_generate_updated_pre_interview_report_invokes_structured_llm() -> None:
    """The update node should produce a refreshed pre-interview plan."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_updated_pre_interview_report_prompt.return_value = ["update prompt"]
    llm_adapter.structured_ainvoke.return_value = _updated_pre_interview_plan()
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = PostInterviewUpdateSchema(input_data=_input_data())

    node_result = await graph._generate_updated_pre_interview_report(state)

    prompt_builder.build_updated_pre_interview_report_prompt.assert_called_once_with(
        input_data=_input_data(),
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["update prompt"], PreInterviewPlan)
    assert node_result == {"updated_pre_interview_plan": _updated_pre_interview_plan()}


async def test_post_interview_update_process_runs_full_graph() -> None:
    """The graph should execute the third-stage workflow end to end."""
    llm_adapter = _mock_llm_adapter()
    llm_adapter.structured_ainvoke.return_value = _updated_pre_interview_plan()
    graph = PostInterviewUpdateGraph(
        llm_adapter=llm_adapter,
        prompt_builder=_real_prompt_builder(),
    )

    graph_result = await graph.process(_input_data())

    assert graph_result.updated_pre_interview_plan == _updated_pre_interview_plan()
