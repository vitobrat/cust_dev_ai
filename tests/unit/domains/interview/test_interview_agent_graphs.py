"""Unit tests for the pre-interview preparation graph."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.pre_interview_preparation import (
    PreInterviewPreparationGraph,
)
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import (
    BusinessContextReport,
    PreInterviewPlan,
    ResearchSource,
)
from src.domains.interview.schemas.pre_interview import (
    ExpectedIdealResultAnalysis,
    HiddenRisksAnalysis,
    InformationGoalsAnalysis,
    MainCustomerConcernsAnalysis,
    PreInterviewAnalysisBundle,
    PreInterviewPreparationInputData,
    PreInterviewPreparationSchema,
    PreInterviewResearchPlan,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


def _mock_llm_adapter() -> MagicMock:
    llm_adapter = MagicMock(spec=LLMAdapter)
    llm_adapter.structured_ainvoke = AsyncMock()
    return llm_adapter


def _mock_prompt_builder() -> MagicMock:
    return MagicMock(spec=InterviewPromptManager)


def _graph() -> PreInterviewPreparationGraph:
    return PreInterviewPreparationGraph(
        llm_adapter=_mock_llm_adapter(),
        prompt_builder=_mock_prompt_builder(),
    )


def _graph_with_mocks(
    llm_adapter: MagicMock,
    prompt_builder: MagicMock,
) -> PreInterviewPreparationGraph:
    return PreInterviewPreparationGraph(
        llm_adapter=llm_adapter,
        prompt_builder=prompt_builder,
    )


def _input_data() -> PreInterviewPreparationInputData:
    return PreInterviewPreparationInputData(
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing customer discovery without a research team.",
        industry_description="B2B SaaS discovery tooling",
        rewritten_user_request="Check whether AI interview prep is valuable.",
        user_controlled_knowledge_context="Internal calls show founders lose evidence after discovery.",
        allow_external_search=True,
    )


def _pre_interview_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Understand urgent buying triggers.",
        main_customer_concerns=["Manual discovery takes too long."],
        hidden_risks=["Budget ownership may be fragmented."],
        base_questions=[
            "How do you solve this now?",
            "When did this last happen?",
            "What did it cost you?",
        ],
        expected_ideal_result="Clear evidence of an urgent, paid problem.",
    )


def _analysis_bundle() -> PreInterviewAnalysisBundle:
    return PreInterviewAnalysisBundle(
        information_collection_goals=[
            "Validate current workflow",
            "Quantify wasted time and money",
            "Identify buying authority",
        ],
        main_customer_concerns=["They fear wasting scarce founder-led sales calls."],
        hidden_risks=["Founders may say they want automation but still prefer manual control."],
        expected_ideal_result="A founder agrees the pain is urgent enough to test a paid workflow.",
        base_questions=[
            "Tell me about the last discovery call that went badly.",
            "What did you do after that call to recover the insight?",
            "What would have to happen for you to pay for a better workflow?",
        ],
    )


def _business_context_report() -> BusinessContextReport:
    return BusinessContextReport(
        segment_summary="Solo B2B SaaS founders who run discovery themselves.",
        industry_summary="Early-stage B2B SaaS discovery and sales tooling.",
        rewritten_user_request="Understand whether founders need AI help preparing discovery calls.",
        evidence_summary="Internal knowledge and web context suggest discovery quality varies heavily.",
        data_freshness_warning="External data may be incomplete and must not be treated as decisive.",
        quick_swot="Strength: urgent revenue pressure. Threat: crowded sales tooling market.",
        sources=[
            ResearchSource(
                title="Internal notes",
                summary="Founders struggle to turn calls into structured evidence.",
            ),
        ],
    )


def _real_prompt_builder() -> InterviewPromptManager:
    return InterviewPromptManager(
        prompts_dir=Path(PROJECT_ROOT, "src", "domains", "interview", "infrastructure", "prompt"),
    )


def _structured_pre_interview_responses() -> dict[object, object]:
    return {
        PreInterviewResearchPlan: PreInterviewResearchPlan(
            research_query="solo B2B SaaS founder customer discovery workflow",
            external_search_required=True,
            reasoning="Fresh context can improve the interview brief.",
        ),
        BusinessContextReport: _business_context_report(),
        MainCustomerConcernsAnalysis: MainCustomerConcernsAnalysis(
            main_customer_concerns=["Discovery calls are expensive to waste."],
        ),
        HiddenRisksAnalysis: HiddenRisksAnalysis(
            hidden_risks=["The founder may praise automation without changing their workflow."],
        ),
        ExpectedIdealResultAnalysis: ExpectedIdealResultAnalysis(
            expected_ideal_result="The persona agrees to share a real failed-call example.",
        ),
        InformationGoalsAnalysis: InformationGoalsAnalysis(
            information_collection_goals=[
                "Validate workflow frequency",
                "Quantify the cost of poor interviews",
                "Identify buying authority",
            ],
            base_questions=[
                "Tell me about the last customer interview that failed to produce useful evidence.",
                "What did you do after that call?",
                "What would need to happen for you to try a different workflow?",
            ],
        ),
        PreInterviewPlan: PreInterviewPlan(
            information_collection_goal=(
                "Validate workflow frequency; Quantify the cost of poor interviews; Identify buying authority"
            ),
            main_customer_concerns=["Discovery calls are expensive to waste."],
            hidden_risks=["The founder may praise automation without changing their workflow."],
            base_questions=[
                "Tell me about the last customer interview that failed to produce useful evidence.",
                "What did you do after that call?",
                "What would need to happen for you to try a different workflow?",
            ],
            expected_ideal_result="The persona agrees to share a real failed-call example.",
        ),
    }


def _get_structured_pre_interview_response(_prompt: object, schema: object) -> object:
    return _structured_pre_interview_responses()[schema]


def test_interview_prompt_manager_loads_pre_interview_templates() -> None:
    """The first-stage graph should have all prompt templates available."""
    prompt_builder = _real_prompt_builder()
    template_names = [
        "build_context_research_query",
        "build_context_research_query_output_example",
        "study_segment_and_industry",
        "study_segment_and_industry_output_example",
        "analyse_main_customer_concerns",
        "analyse_main_customer_concerns_output_example",
        "analyse_hidden_risks",
        "analyse_hidden_risks_output_example",
        "define_expected_ideal_result",
        "define_expected_ideal_result_output_example",
        "define_information_goals",
        "define_information_goals_output_example",
        "generate_pre_interview_report",
        "generate_pre_interview_report_output_example",
    ]

    assert all(
        prompt_builder.has_template("pre_interview_preparation", template_name) for template_name in template_names
    )


async def test_build_context_research_query_invokes_structured_llm() -> None:
    """Research-query node should turn input context into a search plan."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt = ["research prompt"]
    research_plan = PreInterviewResearchPlan(
        research_query="solo B2B SaaS founder discovery workflow market pain points",
        external_search_required=True,
        reasoning="The provided internal context is thin and current market context is useful.",
    )
    prompt_builder.build_context_research_query_prompt.return_value = prompt
    llm_adapter.structured_ainvoke.return_value = research_plan
    graph = _graph_with_mocks(llm_adapter, prompt_builder)

    node_result = await graph._build_context_research_query(
        PreInterviewPreparationSchema(input_data=_input_data()),
    )

    prompt_builder.build_context_research_query_prompt.assert_called_once_with(input_data=_input_data())
    llm_adapter.structured_ainvoke.assert_awaited_once_with(prompt, PreInterviewResearchPlan)
    assert node_result == {
        "research_query": research_plan.research_query,
        "external_search_required": True,
    }


async def test_build_context_research_query_disables_external_search_when_forbidden() -> None:
    """Research-query node must honor the caller's external-search permission."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    input_data = _input_data().model_copy(update={"allow_external_search": False})
    prompt_builder.build_context_research_query_prompt.return_value = ["research prompt"]
    llm_adapter.structured_ainvoke.return_value = PreInterviewResearchPlan(
        research_query="internal customer-discovery notes",
        external_search_required=True,
        reasoning="External search would help, but the caller disabled it.",
    )
    graph = _graph_with_mocks(llm_adapter, prompt_builder)

    node_result = await graph._build_context_research_query(
        PreInterviewPreparationSchema(input_data=input_data),
    )

    assert node_result["external_search_required"] is False


async def test_study_segment_and_industry_invokes_structured_llm() -> None:
    """Context-study node should produce the business-context report."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    business_context = _business_context_report()
    prompt_builder.build_study_segment_and_industry_prompt.return_value = ["study prompt"]
    llm_adapter.structured_ainvoke.return_value = business_context
    graph = _graph_with_mocks(llm_adapter, prompt_builder)

    node_result = await graph._study_segment_and_industry(
        PreInterviewPreparationSchema(
            input_data=_input_data(),
            research_query="solo B2B SaaS discovery",
            external_search_required=True,
        ),
    )

    prompt_builder.build_study_segment_and_industry_prompt.assert_called_once_with(
        input_data=_input_data(),
        research_query="solo B2B SaaS discovery",
        external_search_required=True,
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["study prompt"], BusinessContextReport)
    assert node_result == {"business_context": business_context}


async def test_parallel_analysis_nodes_use_business_context() -> None:
    """Four branch nodes should extract concerns, risks, ideal result, goals, and questions."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    business_context = _business_context_report()
    prompt_builder.build_main_customer_concerns_prompt.return_value = ["concerns prompt"]
    prompt_builder.build_hidden_risks_prompt.return_value = ["risks prompt"]
    prompt_builder.build_expected_ideal_result_prompt.return_value = ["ideal prompt"]
    prompt_builder.build_information_goals_prompt.return_value = ["goals prompt"]
    llm_adapter.structured_ainvoke.side_effect = [
        MainCustomerConcernsAnalysis(main_customer_concerns=["Discovery calls are expensive to waste."]),
        HiddenRisksAnalysis(hidden_risks=["The buyer may not own the sales-process budget."]),
        ExpectedIdealResultAnalysis(expected_ideal_result="The persona agrees to test a paid workflow."),
        InformationGoalsAnalysis(
            information_collection_goals=[
                "Validate workflow frequency",
                "Quantify the cost of poor interviews",
                "Identify buying authority",
            ],
            base_questions=[
                "Tell me about the last interview that failed to produce useful evidence.",
                "What did that failure cost your team?",
                "What did you do next to solve the problem?",
            ],
        ),
    ]
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = PreInterviewPreparationSchema(business_context=business_context)

    concerns = await graph._analyse_main_customer_concerns(state)
    risks = await graph._analyse_hidden_risks(state)
    ideal_result = await graph._define_expected_ideal_result(state)
    goals = await graph._define_information_goals(state)

    prompt_builder.build_main_customer_concerns_prompt.assert_called_once_with(business_context=business_context)
    prompt_builder.build_hidden_risks_prompt.assert_called_once_with(business_context=business_context)
    prompt_builder.build_expected_ideal_result_prompt.assert_called_once_with(business_context=business_context)
    prompt_builder.build_information_goals_prompt.assert_called_once_with(business_context=business_context)
    assert concerns == {"main_customer_concerns": ["Discovery calls are expensive to waste."]}
    assert risks == {"hidden_risks": ["The buyer may not own the sales-process budget."]}
    assert ideal_result == {"expected_ideal_result": "The persona agrees to test a paid workflow."}
    assert goals == {
        "information_collection_goals": [
            "Validate workflow frequency",
            "Quantify the cost of poor interviews",
            "Identify buying authority",
        ],
        "base_questions": [
            "Tell me about the last interview that failed to produce useful evidence.",
            "What did that failure cost your team?",
            "What did you do next to solve the problem?",
        ],
    }


async def test_pre_interview_preparation_process_runs_full_graph() -> None:
    """The graph should execute the full first-stage workflow with structured LLM outputs."""
    llm_adapter = _mock_llm_adapter()
    llm_adapter.structured_ainvoke.side_effect = _get_structured_pre_interview_response
    graph = PreInterviewPreparationGraph(
        llm_adapter=llm_adapter,
        prompt_builder=_real_prompt_builder(),
    )

    graph_output = await graph.process(_input_data())

    assert graph_output.pre_interview_plan.information_collection_goal == (
        "Validate workflow frequency; Quantify the cost of poor interviews; Identify buying authority"
    )
    assert graph_output.pre_interview_plan.main_customer_concerns == ["Discovery calls are expensive to waste."]
    assert graph_output.pre_interview_plan.hidden_risks == [
        "The founder may praise automation without changing their workflow.",
    ]
    assert graph_output.pre_interview_plan.base_questions == [
        "Tell me about the last customer interview that failed to produce useful evidence.",
        "What did you do after that call?",
        "What would need to happen for you to try a different workflow?",
    ]
    assert graph_output.pre_interview_plan.expected_ideal_result == (
        "The persona agrees to share a real failed-call example."
    )


def test_pre_interview_preparation_graph_uses_expected_output_contract() -> None:
    """The first-stage graph must expose a pre-interview report output contract."""
    graph = _graph()

    assert graph.output_schema is not None
    assert graph.output_schema.__name__ == "PreInterviewPreparationOutputSchema"


def test_pre_interview_plan_requires_three_base_questions() -> None:
    """The output contract must always keep exactly three interview questions."""
    plan = _pre_interview_plan()

    assert len(plan.base_questions) == 3


async def test_aggregate_analysis_results_builds_output_plan_from_state() -> None:
    """Aggregation node should combine completed branch outputs into one bundle."""
    state = PreInterviewPreparationSchema(
        input_data=PreInterviewPreparationInputData(
            segment_name="Solo B2B SaaS founders",
            segment_description="Founders doing customer discovery without a research team.",
            industry_description="B2B SaaS discovery tooling",
            rewritten_user_request="Check whether AI interview prep is valuable.",
        ),
        business_context=_business_context_report(),
        main_customer_concerns=["They fear wasting scarce founder-led sales calls."],
        hidden_risks=["Founders may say they want automation but still prefer manual control."],
        expected_ideal_result="A founder agrees the pain is urgent enough to test a paid workflow.",
        information_collection_goals=[
            "Validate current workflow",
            "Quantify wasted time and money",
            "Identify buying authority",
        ],
        base_questions=[
            "Tell me about the last discovery call that went badly.",
            "What did you do after that call to recover the insight?",
            "What would have to happen for you to pay for a better workflow?",
        ],
    )
    graph = _graph()

    node_result = await graph._aggregate_analysis_results(state)
    bundle = node_result["analysis_bundle"]

    assert bundle.information_collection_goals == state["information_collection_goals"]
    assert bundle.main_customer_concerns == state["main_customer_concerns"]
    assert bundle.hidden_risks == state["hidden_risks"]
    assert bundle.base_questions == state["base_questions"]
    assert bundle.expected_ideal_result == state["expected_ideal_result"]


async def test_generate_pre_interview_report_invokes_structured_llm() -> None:
    """Final node should synthesize the branch outputs into one interview brief."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    final_plan = _pre_interview_plan()
    prompt_builder.build_generate_pre_interview_report_prompt.return_value = ["report prompt"]
    llm_adapter.structured_ainvoke.return_value = final_plan
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = PreInterviewPreparationSchema(
        input_data=_input_data(),
        business_context=_business_context_report(),
        analysis_bundle=_analysis_bundle(),
    )

    node_result = await graph._generate_pre_interview_report(state)
    plan = node_result["pre_interview_plan"]

    prompt_builder.build_generate_pre_interview_report_prompt.assert_called_once_with(
        input_data=_input_data(),
        business_context=_business_context_report(),
        analysis_bundle=_analysis_bundle(),
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["report prompt"], PreInterviewPlan)
    assert plan == final_plan
