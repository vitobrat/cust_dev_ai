"""Integration tests for interview-domain LangGraph agents."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import BaseMessage

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.interview_orchestrator import (
    InterviewOrchestratorGraph,
)
from src.domains.interview.infrastructure.graph.interview_simulation import (
    InterviewSimulationGraph,
)
from src.domains.interview.infrastructure.graph.post_interview_update import (
    PostInterviewUpdateGraph,
)
from src.domains.interview.infrastructure.graph.pre_interview_preparation import (
    PreInterviewPreparationGraph,
)
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import (
    BusinessContextReport,
    InterviewMessage,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
    ResearchSource,
)
from src.domains.interview.schemas.interview_orchestration import (
    IndustryDescriptionGeneration,
    InterviewOrchestrationInputData,
)
from src.domains.interview.schemas.interview_simulation import (
    InterviewCompletionDecision,
    InterviewQuestionGeneration,
    InterviewSimulationContextRequest,
    InterviewSimulationInputData,
    PersonaAnswerGeneration,
)
from src.domains.interview.schemas.post_interview_update import (
    PostInterviewUpdateInputData,
)
from src.domains.interview.schemas.pre_interview import (
    ExpectedIdealResultAnalysis,
    HiddenRisksAnalysis,
    InformationGoalsAnalysis,
    MainCustomerConcernsAnalysis,
    PreInterviewPreparationInputData,
    PreInterviewResearchPlan,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


class _GraphSuite(NamedTuple):
    llm_adapter: MagicMock
    pre_interview: PreInterviewPreparationGraph
    interview_simulation: InterviewSimulationGraph
    post_interview_update: PostInterviewUpdateGraph
    orchestrator: InterviewOrchestratorGraph


def _prompt_builder() -> InterviewPromptManager:
    return InterviewPromptManager(
        prompts_dir=Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt"),
    )


def _mock_llm_adapter() -> MagicMock:
    llm_adapter = MagicMock(spec=LLMAdapter)
    llm_adapter.structured_ainvoke = AsyncMock(side_effect=_structured_response)
    return llm_adapter


def _graph_suite() -> _GraphSuite:
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _prompt_builder()
    pre_interview = PreInterviewPreparationGraph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    interview_simulation = InterviewSimulationGraph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    post_interview_update = PostInterviewUpdateGraph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    orchestrator = InterviewOrchestratorGraph(
        pre_interview_preparation_graph=pre_interview,
        interview_simulation_graph=interview_simulation,
        post_interview_update_graph=post_interview_update,
        llm_adapter=llm_adapter,
        prompt_builder=prompt_builder,
    )
    return _GraphSuite(
        llm_adapter=llm_adapter,
        pre_interview=pre_interview,
        interview_simulation=interview_simulation,
        post_interview_update=post_interview_update,
        orchestrator=orchestrator,
    )


def _pre_interview_input() -> PreInterviewPreparationInputData:
    return PreInterviewPreparationInputData(
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing customer discovery without a research team.",
        industry_description="Early-stage B2B SaaS discovery and sales workflow tooling.",
        rewritten_user_request="Check whether AI interview preparation creates value.",
        user_controlled_knowledge_context="Internal notes show founders lose evidence after calls.",
    )


def _simulation_input(max_iterations: int = 1) -> InterviewSimulationInputData:
    return InterviewSimulationInputData(
        pre_interview_plan=_initial_plan(),
        rewritten_user_request="Check whether AI interview preparation creates value.",
        persona_context=_persona("Alex"),
        max_iterations=max_iterations,
    )


def _orchestration_input() -> InterviewOrchestrationInputData:
    return InterviewOrchestrationInputData(
        rewritten_user_request="Check whether founders need AI interview preparation.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing discovery without a research team.",
        personas=[_persona("Alex"), _persona("Sam")],
        batch_size=1,
        max_iterations_per_interview=1,
    )


def _post_update_input() -> PostInterviewUpdateInputData:
    return PostInterviewUpdateInputData(
        previous_pre_interview_plan=_initial_plan(),
        interview_reports=[_interview_report()],
    )


def _persona(name: str) -> InterviewPersonaContext:
    return InterviewPersonaContext(
        name=name,
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing customer discovery without a research team.",
        biography=f"{name} sells annual contracts and runs discovery calls personally.",
        experiences="Scattered notes, weak follow-up evidence, and back-to-back founder-led sales calls.",
    )


def _initial_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Validate workflow frequency, cost of weak evidence, and buying authority.",
        main_customer_concerns=["Discovery calls consume scarce founder time without reliable evidence."],
        hidden_risks=["The founder may praise automation without being willing to change workflow."],
        base_questions=[
            "Tell me about the last discovery call that failed to produce useful evidence.",
            "What did you do after that call, and what did the workaround cost?",
            "Who would need to approve a paid change to this workflow?",
        ],
        expected_ideal_result="A recent costly failure plus a concrete next-step commitment.",
    )


def _updated_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Validate budget ownership and willingness to replace the current workaround.",
        main_customer_concerns=["Discovery calls consume scarce founder time without reliable evidence."],
        hidden_risks=[
            "The founder may praise automation without being willing to change workflow.",
            "Interest may be curiosity unless tied to budget or a calendar commitment.",
        ],
        base_questions=[
            "Who owns budget for improving your discovery workflow?",
            "Tell me about the last time poor notes changed a sales or product decision.",
            "What concrete next step would you take if this problem was solved next week?",
        ],
        expected_ideal_result="Clear budget ownership and a commitment to share a workflow artifact.",
    )


def _business_context() -> BusinessContextReport:
    return BusinessContextReport(
        segment_summary="Solo B2B SaaS founders personally running discovery.",
        industry_summary="Founder-led B2B SaaS discovery, sales workflow, and lightweight AI tooling.",
        rewritten_user_request="Check whether AI interview preparation creates value.",
        evidence_summary="Internal notes point to scattered evidence and weak post-call decisions.",
        data_freshness_warning="No live external snippets were provided; verify market assumptions before decisions.",
        quick_swot="Strength: urgent learning pressure. Threat: generic notes and CRM tools may feel sufficient.",
        sources=[
            ResearchSource(
                title="Internal discovery notes",
                summary="Founders lose evidence after customer calls.",
            ),
        ],
    )


def _interview_report() -> InterviewReport:
    return InterviewReport(
        target_information=["Founder loses evidence after discovery calls."],
        important_quotes=["My notes are scattered and I cannot defend the decision later."],
        outcomes_or_agreements=["Agreed to share a sanitized discovery-call template."],
        recommendations_for_next_interviews=["Probe budget ownership before discussing features."],
        is_successful=True,
        success_score=0.82,
        success_reasoning="The interview captured a recent pain and a concrete next step.",
    )


def _structured_response(prompt: object, schema: object) -> object:
    if schema is IndustryDescriptionGeneration:
        return IndustryDescriptionGeneration(
            industry_description="Early-stage B2B SaaS discovery and sales workflow tooling.",
            external_search_required=True,
            reasoning="Market alternatives and buying triggers can affect the interview plan.",
        )
    if schema is PreInterviewPlan:
        return _plan_response(prompt)
    return _schema_responses()[schema]


def _schema_responses() -> dict[object, object]:
    return {
        PreInterviewResearchPlan: PreInterviewResearchPlan(
            research_query="solo B2B SaaS founder customer discovery workflow",
            external_search_required=True,
            reasoning="Fresh context can improve the interview brief.",
        ),
        BusinessContextReport: _business_context(),
        MainCustomerConcernsAnalysis: MainCustomerConcernsAnalysis(
            main_customer_concerns=["Discovery calls consume scarce founder time without reliable evidence."],
        ),
        HiddenRisksAnalysis: HiddenRisksAnalysis(
            hidden_risks=["The founder may praise automation without being willing to change workflow."],
        ),
        ExpectedIdealResultAnalysis: ExpectedIdealResultAnalysis(
            expected_ideal_result="A recent costly failure plus a concrete next-step commitment.",
        ),
        InformationGoalsAnalysis: InformationGoalsAnalysis(
            information_collection_goals=[
                "Validate workflow frequency",
                "Quantify cost of weak evidence",
                "Identify buying authority",
            ],
            base_questions=_initial_plan().base_questions,
        ),
        InterviewQuestionGeneration: InterviewQuestionGeneration(
            current_question="Tell me about the last discovery call that failed to produce useful evidence.",
            reasoning="Start from a recent concrete event.",
        ),
        InterviewSimulationContextRequest: InterviewSimulationContextRequest(
            persona_context_query="recent founder-led discovery call scattered notes",
            retrieved_persona_context="The founder runs discovery personally and loses weak signals after calls.",
            external_search_required=False,
            reasoning="Persona context is enough for this answer.",
        ),
        PersonaAnswerGeneration: PersonaAnswerGeneration(
            current_answer="Last Thursday I had a demo call and my notes were useless afterwards.",
        ),
        InterviewCompletionDecision: InterviewCompletionDecision(
            should_finish=False,
            reasoning="The iteration limit will stop this integration fixture after one turn.",
        ),
        InterviewReport: _interview_report(),
    }


def _plan_response(prompt: object) -> PreInterviewPlan:
    if "Previous pre-interview plan" in _prompt_text(prompt):
        return _updated_plan()
    return _initial_plan()


def _prompt_text(prompt: object) -> str:
    if not isinstance(prompt, list):
        return str(prompt)
    return "\n".join(message.content for message in prompt if isinstance(message, BaseMessage))


def _schema_calls(llm_adapter: MagicMock) -> list[object]:
    return [call_args.args[1] for call_args in llm_adapter.structured_ainvoke.await_args_list]


async def test_pre_interview_preparation_graph_integrates_templates_and_langgraph() -> None:
    """First-stage graph should run all prompt-backed nodes through the compiled graph."""
    graph_suite = _graph_suite()

    graph_output = await graph_suite.pre_interview.process(_pre_interview_input())
    schema_calls = _schema_calls(graph_suite.llm_adapter)

    assert graph_output.pre_interview_plan == _initial_plan()
    assert schema_calls[:2] == [PreInterviewResearchPlan, BusinessContextReport]
    assert set(schema_calls[2:6]) == {
        MainCustomerConcernsAnalysis,
        HiddenRisksAnalysis,
        ExpectedIdealResultAnalysis,
        InformationGoalsAnalysis,
    }
    assert schema_calls[-1] is PreInterviewPlan


async def test_interview_simulation_graph_integrates_dialogue_loop_and_report() -> None:
    """Second-stage graph should run one full interview turn and produce a report."""
    graph_suite = _graph_suite()

    graph_output = await graph_suite.interview_simulation.process(_simulation_input())

    assert graph_output.interview_report == _interview_report()
    assert graph_output.chat_history == [
        InterviewMessage(
            speaker="interviewer",
            content="Tell me about the last discovery call that failed to produce useful evidence.",
        ),
        InterviewMessage(
            speaker="persona",
            content="Last Thursday I had a demo call and my notes were useless afterwards.",
        ),
    ]
    assert _schema_calls(graph_suite.llm_adapter) == [
        InterviewQuestionGeneration,
        InterviewSimulationContextRequest,
        PersonaAnswerGeneration,
        InterviewCompletionDecision,
        InterviewReport,
    ]


async def test_post_interview_update_graph_integrates_prompt_and_output_contract() -> None:
    """Third-stage graph should update a pre-interview plan from completed interview reports."""
    graph_suite = _graph_suite()

    graph_output = await graph_suite.post_interview_update.process(_post_update_input())

    assert graph_output.updated_pre_interview_plan == _updated_plan()
    assert _schema_calls(graph_suite.llm_adapter) == [PreInterviewPlan]


async def test_interview_orchestrator_graph_integrates_all_stage_graphs_over_batches() -> None:
    """Full orchestrator should run real child graphs over multiple persona batches."""
    graph_suite = _graph_suite()

    graph_output = await graph_suite.orchestrator.process(_orchestration_input())
    schema_calls = _schema_calls(graph_suite.llm_adapter)

    assert graph_output.interview_reports == [_interview_report(), _interview_report()]
    assert graph_output.final_pre_interview_plan == _updated_plan()
    assert schema_calls.count(IndustryDescriptionGeneration) == 1
    assert schema_calls.count(InterviewReport) == 2
    assert schema_calls.count(PreInterviewPlan) == 3
