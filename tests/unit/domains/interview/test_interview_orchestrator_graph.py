"""Unit tests for the full interview simulation orchestrator graph."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

import pytest
from langgraph.types import Send
from pydantic import ValidationError

from src.configs.consts import (
    INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE,
    PROJECT_ROOT,
)
from src.domains.interview.infrastructure.graph.interview_orchestrator import (
    InterviewOrchestratorGraph,
)
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import (
    InterviewNotes,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
)
from src.domains.interview.schemas.interview_orchestration import (
    IndustryDescriptionGeneration,
    InterviewOrchestrationInputData,
    InterviewOrchestrationSchema,
)
from src.domains.interview.schemas.interview_simulation import (
    InterviewSimulationInputData,
    InterviewSimulationOutputData,
)
from src.domains.interview.schemas.post_interview_update import (
    PostInterviewUpdateOutputData,
)
from src.domains.interview.schemas.pre_interview import (
    PreInterviewPreparationOutputData,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


class _StageGraphs(NamedTuple):
    pre_interview: MagicMock
    interview_simulation: MagicMock
    post_interview_update: MagicMock


def _mock_llm_adapter() -> MagicMock:
    llm_adapter = MagicMock(spec=LLMAdapter)
    llm_adapter.structured_ainvoke = AsyncMock()
    return llm_adapter


def _mock_prompt_builder() -> MagicMock:
    return MagicMock(spec=InterviewPromptManager)


def _pre_interview_plan(goal: str = "Validate current discovery workflow.") -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal=goal,
        main_customer_concerns=["Discovery calls produce scattered evidence."],
        hidden_risks=["Budget ownership may be unclear."],
        base_questions=[
            "Tell me about the last failed discovery call.",
            "What did that failure cost?",
            "What would make you change the workflow?",
        ],
        expected_ideal_result="Concrete pain plus next-step commitment.",
    )


def _persona(name: str) -> InterviewPersonaContext:
    return InterviewPersonaContext(
        name=name,
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing discovery without a research team.",
        biography=f"{name} runs customer discovery personally.",
        experiences="Scattered notes and weak post-call evidence.",
    )


def _interview_report(label: str) -> InterviewReport:
    return InterviewReport(
        target_information=[f"{label} needs better interview evidence."],
        important_quotes=[f"{label}: notes are too scattered."],
        outcomes_or_agreements=[f"{label} agreed to test a checklist."],
        recommendations_for_next_interviews=["Ask about budget ownership."],
        is_successful=True,
        success_score=0.8,
        success_reasoning="Concrete pain and next step were captured.",
    )


def _industry_description_generation() -> IndustryDescriptionGeneration:
    return IndustryDescriptionGeneration(
        industry_description=(
            "Early-stage B2B SaaS customer-discovery tooling where founders balance speed, evidence quality, "
            "sales pressure, and limited budget."
        ),
        external_search_required=True,
        reasoning="Current sales-tech alternatives and buying triggers can materially affect the interview plan.",
    )


def _input_data(batch_size: int = 2) -> InterviewOrchestrationInputData:
    return InterviewOrchestrationInputData(
        rewritten_user_request="Check whether founders need AI interview preparation.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing discovery without a research team.",
        personas=[_persona("Alex"), _persona("Sam"), _persona("Nora")],
        batch_size=batch_size,
        max_iterations_per_interview=5,
    )


def _real_prompt_builder() -> InterviewPromptManager:
    return InterviewPromptManager(
        prompts_dir=Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt"),
    )


def _mock_stage_graphs(
    initial_plan: PreInterviewPlan,
    updated_plan: PreInterviewPlan,
    interview_report: InterviewReport,
) -> _StageGraphs:
    pre_interview_graph = MagicMock()
    pre_interview_graph.process = AsyncMock(
        return_value=PreInterviewPreparationOutputData(pre_interview_plan=initial_plan),
    )
    interview_simulation_graph = MagicMock()
    interview_simulation_graph.process = AsyncMock(
        return_value=InterviewSimulationOutputData(
            interview_report=interview_report,
            chat_history=[],
            interviewer_notes=InterviewNotes(),
        ),
    )
    post_interview_update_graph = MagicMock()
    post_interview_update_graph.process = AsyncMock(
        return_value=PostInterviewUpdateOutputData(updated_pre_interview_plan=updated_plan),
    )
    return _StageGraphs(
        pre_interview=pre_interview_graph,
        interview_simulation=interview_simulation_graph,
        post_interview_update=post_interview_update_graph,
    )


def _graph(
    pre_interview_graph: MagicMock | None = None,
    interview_simulation_graph: MagicMock | None = None,
    post_interview_update_graph: MagicMock | None = None,
    llm_adapter: MagicMock | None = None,
    prompt_builder: MagicMock | InterviewPromptManager | None = None,
) -> InterviewOrchestratorGraph:
    return InterviewOrchestratorGraph(
        pre_interview_preparation_graph=pre_interview_graph or MagicMock(),
        interview_simulation_graph=interview_simulation_graph or MagicMock(),
        post_interview_update_graph=post_interview_update_graph or MagicMock(),
        llm_adapter=llm_adapter or _mock_llm_adapter(),
        prompt_builder=prompt_builder or _mock_prompt_builder(),
        recursion_limit=20,
    )


def test_interview_prompt_manager_loads_orchestration_templates() -> None:
    """The orchestration graph should have its industry-context prompt templates available."""
    prompt_builder = _real_prompt_builder()

    assert prompt_builder.has_template("interview_orchestration", "generate_industry_description")
    assert prompt_builder.has_template("interview_orchestration", "generate_industry_description_output_example")


def test_generate_industry_description_prompt_uses_bounded_persona_context() -> None:
    """The first orchestration prompt must not serialize full JSON for every persona."""
    prompt_builder = _real_prompt_builder()
    input_data = _input_data(batch_size=1).model_copy(
        update={
            "personas": [
                _persona(f"Persona {persona_index}").model_copy(
                    update={
                        "biography": f"Persona {persona_index} FULL_BIOGRAPHY_TOKEN {'long biography ' * 40}",
                        "experiences": f"Persona {persona_index} FULL_EXPERIENCES_TOKEN {'long experience ' * 40}",
                    },
                )
                for persona_index in range(50)
            ],
        },
    )

    prompt = prompt_builder.build_generate_industry_description_prompt(input_data=input_data)
    prompt_text = str(prompt[0].content)

    assert '"biography"' not in prompt_text
    assert '"experiences"' not in prompt_text
    assert "Persona 49 FULL_BIOGRAPHY_TOKEN" not in prompt_text
    assert "Persona 49 FULL_EXPERIENCES_TOKEN" not in prompt_text
    assert len(prompt_text) < 6000


def test_interview_orchestrator_graph_uses_expected_output_contract() -> None:
    """The full-cycle graph must expose all generated interview reports."""
    graph = _graph()

    assert graph.output_schema is not None
    assert graph.output_schema.__name__ == "InterviewOrchestrationOutputSchema"


def test_interview_orchestration_input_rejects_unsafe_batch_size() -> None:
    """Batch size must be capped to avoid unbounded LangGraph fan-out."""
    with pytest.raises(ValidationError):
        _input_data(batch_size=INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE + 1)


async def test_generate_industry_description_invokes_structured_llm() -> None:
    """The first node should generate compact industry context for the pre-interview graph."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_generate_industry_description_prompt.return_value = ["industry prompt"]
    llm_adapter.structured_ainvoke.return_value = _industry_description_generation()
    graph = _graph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    state = InterviewOrchestrationSchema(input_data=_input_data())

    node_result = await graph._generate_industry_description(state)

    prompt_builder.build_generate_industry_description_prompt.assert_called_once_with(input_data=_input_data())
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["industry prompt"], IndustryDescriptionGeneration)
    assert node_result == {
        "industry_description": _industry_description_generation().industry_description,
        "industry_external_search_required": True,
    }


async def test_generate_industry_description_honors_external_search_permission() -> None:
    """The industry-context node must not request external search when the caller forbids it."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_generate_industry_description_prompt.return_value = ["industry prompt"]
    llm_adapter.structured_ainvoke.return_value = _industry_description_generation()
    graph = _graph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    input_data = _input_data().model_copy(update={"allow_external_search": False})

    node_result = await graph._generate_industry_description(InterviewOrchestrationSchema(input_data=input_data))

    assert node_result["industry_external_search_required"] is False


async def test_map_interview_batch_sends_next_unprocessed_personas() -> None:
    """Batch mapping should fan out only personas that do not have reports yet."""
    state = InterviewOrchestrationSchema(
        input_data=_input_data(batch_size=2),
        pre_interview_plan=_pre_interview_plan(),
        interview_reports=[_interview_report("Alex")],
    )

    sends = await _graph()._map_interview_batch(state)

    assert len(sends) == 2
    for send in sends:
        assert isinstance(send, Send)
        assert send.node == "run_interview_simulation"
    assert sends[0].arg["active_persona_context"].name == "Sam"
    assert sends[1].arg["active_persona_context"].name == "Nora"
    assert sends[0].arg["pre_interview_plan"] == _pre_interview_plan()


async def test_route_after_plan_update_finishes_when_all_personas_interviewed() -> None:
    """After N reports are collected, the orchestrator should finish."""
    state = InterviewOrchestrationSchema(
        input_data=_input_data(batch_size=2),
        pre_interview_plan=_pre_interview_plan(),
        interview_reports=[
            _interview_report("Alex"),
            _interview_report("Sam"),
            _interview_report("Nora"),
        ],
    )

    route = await _graph()._route_after_plan_update(state)

    assert route == "finish_interview_cycle"


async def test_run_pre_interview_preparation_delegates_to_first_stage_graph() -> None:
    """The orchestrator should call the first-stage graph with generated industry context."""
    pre_interview_graph = MagicMock()
    pre_interview_graph.process = AsyncMock(
        return_value=PreInterviewPreparationOutputData(pre_interview_plan=_pre_interview_plan()),
    )
    state = InterviewOrchestrationSchema(
        input_data=_input_data(),
        industry_description="B2B SaaS discovery tooling.",
    )

    node_result = await _graph(pre_interview_graph=pre_interview_graph)._run_pre_interview_preparation(state)

    assert node_result["pre_interview_plan"] == _pre_interview_plan()
    call_args = pre_interview_graph.process.await_args
    assert call_args is not None
    call_input = call_args.args[0]
    assert call_input.industry_description == "B2B SaaS discovery tooling."
    assert call_input.rewritten_user_request == _input_data().rewritten_user_request


async def test_run_interview_simulation_delegates_to_second_stage_graph() -> None:
    """Each batch item should call the interview graph and append one report."""
    interview_simulation_graph = MagicMock()
    interview_simulation_graph.process = AsyncMock(
        return_value=InterviewSimulationOutputData(
            interview_report=_interview_report("Alex"),
            chat_history=[],
            interviewer_notes=InterviewNotes(),
        ),
    )
    state = InterviewOrchestrationSchema(
        input_data=_input_data(),
        pre_interview_plan=_pre_interview_plan(),
        active_persona_context=_persona("Alex"),
    )

    node_result = await _graph(interview_simulation_graph=interview_simulation_graph)._run_interview_simulation(state)

    assert node_result["interview_reports"] == [_interview_report("Alex")]
    call_args = interview_simulation_graph.process.await_args
    assert call_args is not None
    call_input = call_args.args[0]
    assert isinstance(call_input, InterviewSimulationInputData)
    assert call_input.persona_context.name == "Alex"


async def test_run_post_interview_update_delegates_to_third_stage_graph() -> None:
    """After a batch, the orchestrator should update the plan through the third-stage graph."""
    updated_plan = _pre_interview_plan("Validate budget owner and last-call evidence.")
    post_interview_update_graph = MagicMock()
    post_interview_update_graph.process = AsyncMock(
        return_value=PostInterviewUpdateOutputData(updated_pre_interview_plan=updated_plan),
    )
    state = InterviewOrchestrationSchema(
        input_data=_input_data(),
        pre_interview_plan=_pre_interview_plan(),
        interview_reports=[_interview_report("Alex")],
    )

    node_result = await _graph(post_interview_update_graph=post_interview_update_graph)._run_post_interview_update(
        state,
    )

    assert node_result["pre_interview_plan"] == updated_plan
    assert node_result["final_pre_interview_plan"] == updated_plan
    call_args = post_interview_update_graph.process.await_args
    assert call_args is not None
    call_input = call_args.args[0]
    assert call_input.previous_pre_interview_plan == _pre_interview_plan()
    assert call_input.interview_reports == [_interview_report("Alex")]


async def test_run_post_interview_update_uses_only_latest_batch_reports() -> None:
    """Plan updates should not resend accumulated reports from previous batches."""
    updated_plan = _pre_interview_plan("Validate only latest batch evidence.")
    post_interview_update_graph = MagicMock()
    post_interview_update_graph.process = AsyncMock(
        return_value=PostInterviewUpdateOutputData(updated_pre_interview_plan=updated_plan),
    )
    state = InterviewOrchestrationSchema(
        input_data=_input_data(batch_size=1),
        pre_interview_plan=_pre_interview_plan(),
        interview_reports=[_interview_report("Alex"), _interview_report("Sam")],
    )

    await _graph(post_interview_update_graph=post_interview_update_graph)._run_post_interview_update(state)

    call_args = post_interview_update_graph.process.await_args
    assert call_args is not None
    call_input = call_args.args[0]
    assert call_input.interview_reports == [_interview_report("Sam")]


async def test_finish_interview_cycle_returns_reports_and_latest_plan() -> None:
    """The final node should expose the latest plan without duplicating report reducer state."""
    state = InterviewOrchestrationSchema(
        input_data=_input_data(),
        pre_interview_plan=_pre_interview_plan("Latest goal"),
        interview_reports=[_interview_report("Alex")],
    )

    node_result = await _graph()._finish_interview_cycle(state)

    assert node_result["final_pre_interview_plan"] == _pre_interview_plan("Latest goal")


async def test_interview_orchestrator_process_runs_one_persona_cycle() -> None:
    """The graph should run industry context, preparation, one interview, update, and finish."""
    initial_plan = _pre_interview_plan()
    updated_plan = _pre_interview_plan("Validate budget owner and next-step commitment.")
    interview_report = _interview_report("Alex")
    llm_adapter = _mock_llm_adapter()
    llm_adapter.structured_ainvoke.return_value = _industry_description_generation()
    stage_graphs = _mock_stage_graphs(
        initial_plan=initial_plan,
        updated_plan=updated_plan,
        interview_report=interview_report,
    )
    graph = _graph(
        pre_interview_graph=stage_graphs.pre_interview,
        interview_simulation_graph=stage_graphs.interview_simulation,
        post_interview_update_graph=stage_graphs.post_interview_update,
        llm_adapter=llm_adapter,
        prompt_builder=_real_prompt_builder(),
    )

    graph_output = await graph.process(
        _input_data(batch_size=1).model_copy(
            update={"personas": [_persona("Alex")]},
        ),
    )

    assert graph_output.interview_reports == [interview_report]
    assert graph_output.final_pre_interview_plan == updated_plan
    pre_call_args = stage_graphs.pre_interview.process.await_args
    interview_call_args = stage_graphs.interview_simulation.process.await_args
    post_call_args = stage_graphs.post_interview_update.process.await_args
    assert pre_call_args is not None
    assert interview_call_args is not None
    assert post_call_args is not None
    assert pre_call_args.args[0].industry_description == _industry_description_generation().industry_description
    assert interview_call_args.args[0].persona_context == _persona("Alex")
    assert interview_call_args.args[0].pre_interview_plan == initial_plan
    assert post_call_args.args[0].previous_pre_interview_plan == initial_plan
    assert post_call_args.args[0].interview_reports == [interview_report]
