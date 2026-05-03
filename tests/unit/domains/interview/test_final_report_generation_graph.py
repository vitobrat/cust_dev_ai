"""Unit tests for the final interview report generation graph."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.final_report_generation import (
    FinalReportGenerationGraph,
)
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import (
    InterviewMessage,
    InterviewNotes,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.final_report import (
    CustomerContradiction,
    CustomerProblemStat,
    FinalInterviewReport,
    FinalReportConclusion,
    FinalReportCoreSections,
    FinalReportOpening,
    FinalReportPlanningAnalysis,
    FinalReportSection,
)
from src.domains.interview.schemas.final_report_generation import (
    FinalReportGenerationInputData,
    FinalReportGenerationSchema,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


def _mock_llm_adapter() -> MagicMock:
    llm_adapter = MagicMock(spec=LLMAdapter)
    llm_adapter.structured_ainvoke = AsyncMock()
    return llm_adapter


def _mock_prompt_builder() -> MagicMock:
    return MagicMock(spec=InterviewPromptManager)


def _real_prompt_builder() -> InterviewPromptManager:
    return InterviewPromptManager(
        prompts_dir=Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt"),
    )


def _graph(
    llm_adapter: MagicMock | None = None,
    prompt_builder: MagicMock | InterviewPromptManager | None = None,
) -> FinalReportGenerationGraph:
    return FinalReportGenerationGraph(
        llm_adapter=llm_adapter or _mock_llm_adapter(),
        prompt_builder=prompt_builder or _mock_prompt_builder(),
    )


def _pre_interview_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Validate whether founders will change discovery workflow.",
        main_customer_concerns=["Discovery evidence is scattered."],
        hidden_risks=["Positive feedback may hide no budget."],
        base_questions=[
            "Tell me about the last failed discovery call.",
            "What did it cost?",
            "Who would approve a workflow change?",
        ],
        expected_ideal_result="Concrete pain, budget owner, and next-step commitment.",
    )


def _interview_report(label: str) -> InterviewReport:
    return InterviewReport(
        target_information=[f"{label} loses discovery evidence after calls."],
        important_quotes=[f"{label}: my notes are scattered after calls."],
        outcomes_or_agreements=[f"{label} agreed to share one failed-call artifact."],
        recommendations_for_next_interviews=["Probe budget ownership earlier."],
        is_successful=True,
        success_score=0.82,
        success_reasoning="Concrete pain and a next step were captured.",
    )


def _session(label: str) -> SimulatedInterviewSession:
    return SimulatedInterviewSession(
        persona_context=InterviewPersonaContext(
            name=label,
            segment_name="Solo B2B SaaS founders",
            segment_description="Founders who run discovery without a research team.",
            biography=f"{label} runs founder-led sales and discovery.",
            experiences="They lose evidence after customer calls and struggle to decide next actions.",
        ),
        chat_history=[
            InterviewMessage(
                speaker="interviewer",
                content="Tell me about the last failed discovery call.",
            ),
            InterviewMessage(
                speaker="persona",
                content=f"{label}: my notes are scattered after calls.",
            ),
        ],
        interviewer_notes=InterviewNotes(
            customer_pain_points=["Scattered post-call notes."],
            jobs_to_be_done=["Turn calls into reliable evidence."],
        ),
        interview_report=_interview_report(label),
    )


def _input_data() -> FinalReportGenerationInputData:
    return FinalReportGenerationInputData(
        rewritten_user_request="Validate AI-assisted custdev interview workflow.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run discovery without a research team.",
        final_pre_interview_plan=_pre_interview_plan(),
        interview_sessions=[_session("Alex"), _session("Sam")],
    )


def _planning_analysis() -> FinalReportPlanningAnalysis:
    return FinalReportPlanningAnalysis(
        report_goal="Explain whether founders have a paid discovery-evidence problem.",
        writing_plan=[
            "Cluster respondents by evidence workflow.",
            "Quantify repeated pains and contradictions.",
            "Prioritize next product and research actions.",
        ],
        problem_statistics=[
            CustomerProblemStat(
                problem_name="Scattered post-call notes",
                mention_count=2,
                affected_persona_count=2,
                intensity_score=0.78,
                supporting_quotes=["my notes are scattered after calls"],
            ),
        ],
        contradictions=[
            CustomerContradiction(
                topic="Automation trust",
                contradiction_summary="Respondents want automation but still want manual control.",
                evidence_quotes=["I want help", "I still need to control the notes"],
                implication="The product must support reviewable automation.",
            ),
        ],
        evidence_quality_notes=["Two interviews are directionally useful but still a small sample."],
    )


def _section(section_kind: str = "key_insights", title: str = "Key insights") -> FinalReportSection:
    return FinalReportSection(
        section_kind=section_kind,
        title=title,
        markdown_content=f"## {title}\n\nFounders repeatedly lose evidence after calls.",
        evidence_quotes=["my notes are scattered after calls"],
        data_points=["2 of 2 respondents mentioned scattered notes."],
    )


def _core_sections() -> FinalReportCoreSections:
    return FinalReportCoreSections(
        user_persona_map=_section("user_persona_map", "User persona map"),
        pain_points=_section("pain_points", "Pain points"),
        key_insights=_section("key_insights", "Key insights"),
        failure_risk_analysis=_section("failure_risk_analysis", "Failure risks"),
        recommendations=_section("recommendations", "Recommendations"),
    )


def _get_structured_response(_prompt: object, schema: object) -> object:
    responses: dict[object, object] = {
        FinalReportPlanningAnalysis: _planning_analysis(),
        FinalReportSection: _section(),
        FinalReportOpening: _opening(),
        FinalReportConclusion: _conclusion(),
    }
    return responses[schema]


def _opening() -> FinalReportOpening:
    return FinalReportOpening(
        title="Custdev interview report",
        introduction="This report summarizes simulated interviews with solo B2B SaaS founders.",
        report_scope="Two simulated interviews were analyzed.",
    )


def _conclusion() -> FinalReportConclusion:
    return FinalReportConclusion(
        key_takeaways=[
            "Scattered evidence is the strongest repeated pain.",
            "Budget ownership still needs direct validation.",
        ],
        conclusion="The product direction is promising only if the next interviews confirm budget authority.",
    )


def test_interview_prompt_manager_loads_final_report_templates() -> None:
    """The final-report graph should have all prompt templates available."""
    prompt_builder = _real_prompt_builder()
    template_names = [
        "plan_final_report",
        "plan_final_report_output_example",
        "generate_user_persona_map",
        "generate_pain_points",
        "generate_key_insights",
        "generate_failure_risk_analysis",
        "generate_recommendations",
        "generate_report_section_output_example",
        "write_main_report_body",
        "write_report_opening",
        "write_report_opening_output_example",
        "write_report_conclusion",
        "write_report_conclusion_output_example",
    ]

    assert all(
        prompt_builder.has_template("final_report_generation", template_name) for template_name in template_names
    )


def test_final_report_output_examples_are_valid_json() -> None:
    """Output examples must stay valid JSON because models tend to copy their shape."""
    prompt_dir = Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt")
    example_files = sorted((prompt_dir / "final_report_generation").glob("*output_example.md"))

    assert example_files
    for example_file in example_files:
        json.loads(example_file.read_text(encoding="utf-8"))


def test_final_report_generation_input_requires_interviews() -> None:
    """Final reports must be generated from at least one completed interview."""
    with pytest.raises(ValidationError):
        FinalReportGenerationInputData(
            rewritten_user_request="Validate a product.",
            segment_name="Founders",
            segment_description="Founder-led discovery.",
            final_pre_interview_plan=_pre_interview_plan(),
            interview_sessions=[],
        )


def test_final_report_generation_graph_uses_expected_output_contract() -> None:
    """The final-report graph must expose the structured final report."""
    graph = _graph()

    assert graph.output_schema is not None
    assert graph.output_schema.__name__ == "FinalReportGenerationOutputSchema"


async def test_plan_final_report_invokes_structured_llm() -> None:
    """The planning node should create a plan with contradictions and problem counts."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_plan_final_report_prompt.return_value = ["planning prompt"]
    llm_adapter.structured_ainvoke.return_value = _planning_analysis()
    graph = _graph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)

    node_result = await graph._plan_final_report(FinalReportGenerationSchema(input_data=_input_data()))

    prompt_builder.build_plan_final_report_prompt.assert_called_once_with(input_data=_input_data())
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["planning prompt"], FinalReportPlanningAnalysis)
    assert node_result == {"report_plan": _planning_analysis()}


async def test_generate_user_persona_map_invokes_structured_llm() -> None:
    """The persona-map branch should generate one structured report section."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_user_persona_map_prompt.return_value = ["persona-map prompt"]
    llm_adapter.structured_ainvoke.return_value = _section("user_persona_map", "User persona map")
    graph = _graph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    state = FinalReportGenerationSchema(input_data=_input_data(), report_plan=_planning_analysis())

    node_result = await graph._generate_user_persona_map(state)

    prompt_builder.build_user_persona_map_prompt.assert_called_once_with(
        input_data=_input_data(),
        report_plan=_planning_analysis(),
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["persona-map prompt"], FinalReportSection)
    assert node_result == {"user_persona_map": _section("user_persona_map", "User persona map")}


async def test_write_main_report_body_uses_all_parallel_sections() -> None:
    """The editor node should merge every generated section into the main body."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_main_report_body_prompt.return_value = ["main body prompt"]
    main_body = _section("main_body", "Main report")
    llm_adapter.structured_ainvoke.return_value = main_body
    graph = _graph(llm_adapter=llm_adapter, prompt_builder=prompt_builder)
    state = FinalReportGenerationSchema(
        input_data=_input_data(),
        report_plan=_planning_analysis(),
        **_core_sections().model_dump(),
    )

    node_result = await graph._write_main_report_body(state)

    prompt_builder.build_main_report_body_prompt.assert_called_once_with(
        input_data=_input_data(),
        report_plan=_planning_analysis(),
        core_sections=_core_sections(),
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["main body prompt"], FinalReportSection)
    assert node_result == {"main_body": main_body}


async def test_assemble_final_report_returns_markdown_document() -> None:
    """The final glue node should return a structured report and markdown content."""
    state = FinalReportGenerationSchema(
        input_data=_input_data(),
        report_plan=_planning_analysis(),
        **_core_sections().model_dump(),
        main_body=_section("main_body", "Main report"),
        opening=_opening(),
        conclusion=_conclusion(),
    )

    node_result = await _graph()._assemble_final_report(state)

    final_report = node_result["final_report"]
    assert isinstance(final_report, FinalInterviewReport)
    assert final_report.opening == _opening()
    assert final_report.planning_analysis == _planning_analysis()
    assert "Custdev interview report" in final_report.markdown_content
    assert "Scattered evidence is the strongest repeated pain." in final_report.markdown_content


async def test_final_report_generation_process_runs_full_graph() -> None:
    """The graph should execute planning, section generation, editing, and final assembly."""
    llm_adapter = _mock_llm_adapter()
    graph = FinalReportGenerationGraph(
        llm_adapter=llm_adapter,
        prompt_builder=_real_prompt_builder(),
    )

    llm_adapter.structured_ainvoke.side_effect = _get_structured_response

    graph_output = await graph.process(_input_data())

    assert graph_output.final_report.opening == _opening()
    assert graph_output.final_report.conclusion == _conclusion()
    assert graph_output.final_report.source_interview_count == 2
    assert llm_adapter.structured_ainvoke.await_count == 9
