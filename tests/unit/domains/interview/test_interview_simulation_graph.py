"""Unit tests for the interview simulation graph."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.configs.consts import PROJECT_ROOT
from src.domains.interview.infrastructure.graph.interview_simulation import (
    InterviewSimulationGraph,
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
)
from src.domains.interview.schemas.interview_simulation import (
    InterviewCompletionDecision,
    InterviewQuestionGeneration,
    InterviewSimulationContextRequest,
    InterviewSimulationInputData,
    InterviewSimulationSchema,
    PersonaAnswerGeneration,
)
from src.infrastructure.llm.llm_adapter import LLMAdapter


def _mock_llm_adapter() -> MagicMock:
    llm_adapter = MagicMock(spec=LLMAdapter)
    llm_adapter.structured_ainvoke = AsyncMock()
    return llm_adapter


def _mock_prompt_builder() -> MagicMock:
    return MagicMock(spec=InterviewPromptManager)


def _graph() -> InterviewSimulationGraph:
    return InterviewSimulationGraph(
        llm_adapter=_mock_llm_adapter(),
        prompt_builder=_mock_prompt_builder(),
    )


def _graph_with_mocks(
    llm_adapter: MagicMock,
    prompt_builder: MagicMock,
) -> InterviewSimulationGraph:
    return InterviewSimulationGraph(
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


def _chat_history() -> list[InterviewMessage]:
    return [
        InterviewMessage(
            speaker="interviewer",
            content="Tell me about the last discovery call that did not produce useful evidence.",
        ),
        InterviewMessage(
            speaker="persona",
            content="Last Thursday I had a call and left with unclear notes.",
        ),
    ]


def _interviewer_notes() -> InterviewNotes:
    return InterviewNotes(
        key_facts=["Founder runs discovery calls personally."],
        customer_pain_points=["Call notes are scattered."],
    )


def _interview_report() -> InterviewReport:
    return InterviewReport(
        target_information=["Discovery call prep is painful when the founder has back-to-back calls."],
        important_quotes=["I left the call with unclear notes and no next step."],
        outcomes_or_agreements=["Agreed to share a sanitized discovery-call template."],
        recommendations_for_next_interviews=["Probe willingness to pay before discussing features."],
        is_successful=True,
        success_score=0.82,
        success_reasoning="The interview produced a recent concrete pain and a next-step commitment.",
    )


def _get_structured_interview_response(_prompt: object, schema: object) -> object:
    structured_responses: dict[object, object] = {
        InterviewQuestionGeneration: InterviewQuestionGeneration(
            current_question="Tell me about the last discovery call that failed to produce useful evidence.",
            reasoning="Start from a recent concrete event.",
        ),
        InterviewSimulationContextRequest: InterviewSimulationContextRequest(
            persona_context_query="Alex Morgan recent failed customer discovery call scattered notes",
            retrieved_persona_context="Alex runs discovery personally and often loses weak signals in notes.",
            external_search_required=False,
            reasoning="The persona biography already has enough context for this first answer.",
        ),
        PersonaAnswerGeneration: PersonaAnswerGeneration(
            current_answer="Last Thursday I had a demo call and realized afterwards that my notes were useless.",
        ),
        InterviewCompletionDecision: InterviewCompletionDecision(
            should_finish=False,
            reasoning="The answer is concrete, but one follow-up would normally help.",
            notes_to_add=InterviewNotes(
                key_facts=["The concrete failed call happened last Thursday."],
                customer_pain_points=["Notes were useless after the call."],
            ),
        ),
        InterviewReport: _interview_report(),
    }
    return structured_responses[schema]


def _get_finishing_interview_response(_prompt: object, schema: object) -> object:
    structured_responses: dict[object, object] = {
        InterviewQuestionGeneration: InterviewQuestionGeneration(
            current_question="Tell me about the last discovery call that failed to produce useful evidence.",
            reasoning="Start from a recent concrete event.",
        ),
        InterviewSimulationContextRequest: InterviewSimulationContextRequest(
            persona_context_query="Alex Morgan recent failed customer discovery call scattered notes",
            retrieved_persona_context="Alex runs discovery personally and often loses weak signals in notes.",
            external_search_required=False,
            reasoning="The persona biography already has enough context for this first answer.",
        ),
        PersonaAnswerGeneration: PersonaAnswerGeneration(
            current_answer="I agreed to send my messy notes because that is exactly the painful artifact.",
        ),
        InterviewCompletionDecision: InterviewCompletionDecision(
            should_finish=True,
            reasoning="The answer produced a concrete commitment.",
            notes_to_add=InterviewNotes(
                key_facts=["The persona agreed to send messy notes."],
                customer_pain_points=["The artifact is painful because notes are messy."],
            ),
        ),
        InterviewReport: _interview_report(),
    }
    return structured_responses[schema]


def _persona_context() -> InterviewPersonaContext:
    return InterviewPersonaContext(
        name="Alex Morgan",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders doing customer discovery without a research team.",
        biography="I sell annual contracts and still run discovery interviews myself.",
        experiences="I lose track of weak signals after calls and rely on scattered notes.",
    )


def _input_data(max_iterations: int = 5) -> InterviewSimulationInputData:
    return InterviewSimulationInputData(
        pre_interview_plan=_pre_interview_plan(),
        rewritten_user_request="Check whether AI interview preparation creates value.",
        persona_context=_persona_context(),
        max_iterations=max_iterations,
    )


def test_interview_prompt_manager_loads_interview_simulation_templates() -> None:
    """The second-stage graph should have all prompt templates available."""
    prompt_builder = _real_prompt_builder()
    template_names = [
        "generate_interviewer_question",
        "generate_interviewer_question_output_example",
        "build_persona_context_query",
        "build_persona_context_query_output_example",
        "generate_persona_answer",
        "generate_persona_answer_output_example",
        "validate_interview_completion",
        "validate_interview_completion_output_example",
        "analyze_interview",
        "analyze_interview_output_example",
    ]

    assert all(prompt_builder.has_template("interview_simulation", template_name) for template_name in template_names)


def test_interview_simulation_graph_uses_expected_output_contract() -> None:
    """The second-stage graph must expose the interview report output contract."""
    graph = _graph()

    assert graph.output_schema is not None
    assert graph.output_schema.__name__ == "InterviewSimulationOutputSchema"


async def test_generate_interviewer_question_invokes_structured_llm() -> None:
    """Question node should generate one unbiased interviewer question."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_generate_interviewer_question_prompt.return_value = ["question prompt"]
    llm_adapter.structured_ainvoke.return_value = InterviewQuestionGeneration(
        current_question="Tell me about the last failed discovery call.",
        reasoning="Past behavior is more useful than opinions.",
    )
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = InterviewSimulationSchema(
        input_data=_input_data(),
        chat_history=_chat_history(),
        interviewer_notes=_interviewer_notes(),
        iteration=1,
    )

    node_result = await graph._generate_interviewer_question(state)

    prompt_builder.build_generate_interviewer_question_prompt.assert_called_once_with(
        input_data=_input_data(),
        chat_history=_chat_history(),
        interviewer_notes=_interviewer_notes(),
        iteration=1,
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(
        ["question prompt"],
        InterviewQuestionGeneration,
    )
    assert node_result == {"current_question": "Tell me about the last failed discovery call."}


async def test_build_persona_context_query_invokes_structured_llm() -> None:
    """Persona-context node should prepare context for the simulated answer."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    context_request = InterviewSimulationContextRequest(
        persona_context_query="Alex failed discovery call scattered notes",
        retrieved_persona_context="Alex loses weak signals after calls.",
        external_search_required=False,
        reasoning="Persona biography is enough.",
    )
    prompt_builder.build_persona_context_query_prompt.return_value = ["context prompt"]
    llm_adapter.structured_ainvoke.return_value = context_request
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = InterviewSimulationSchema(
        input_data=_input_data(),
        chat_history=_chat_history(),
        current_question="Tell me about the last failed discovery call.",
    )

    node_result = await graph._build_persona_context_query(state)

    prompt_builder.build_persona_context_query_prompt.assert_called_once_with(
        input_data=_input_data(),
        chat_history=_chat_history(),
        current_question="Tell me about the last failed discovery call.",
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(
        ["context prompt"],
        InterviewSimulationContextRequest,
    )
    assert node_result == {
        "persona_context_query": context_request.persona_context_query,
        "retrieved_persona_context": context_request.retrieved_persona_context,
        "persona_context_external_search_required": False,
    }


async def test_generate_persona_answer_invokes_structured_llm() -> None:
    """Persona-answer node should answer as the simulated customer."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_generate_persona_answer_prompt.return_value = ["answer prompt"]
    llm_adapter.structured_ainvoke.return_value = PersonaAnswerGeneration(
        current_answer="Last Thursday I had a call and my notes were useless afterwards.",
    )
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = InterviewSimulationSchema(
        input_data=_input_data(),
        chat_history=_chat_history(),
        current_question="Tell me about the last failed discovery call.",
        persona_context_query="Alex failed discovery call scattered notes",
        retrieved_persona_context="Alex loses weak signals after calls.",
    )

    node_result = await graph._generate_persona_answer(state)

    prompt_builder.build_generate_persona_answer_prompt.assert_called_once_with(
        input_data=_input_data(),
        chat_history=_chat_history(),
        current_question="Tell me about the last failed discovery call.",
        persona_context_query="Alex failed discovery call scattered notes",
        retrieved_persona_context="Alex loses weak signals after calls.",
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["answer prompt"], PersonaAnswerGeneration)
    assert node_result == {"current_answer": "Last Thursday I had a call and my notes were useless afterwards."}


async def test_append_dialogue_turn_records_question_answer_and_iteration() -> None:
    """Each interview loop must append one interviewer and one persona message."""
    state = InterviewSimulationSchema(
        input_data=_input_data(),
        current_question="Tell me about the last failed discovery call.",
        current_answer="Last Thursday I left a call with no clear next step.",
        iteration=2,
    )
    graph = _graph()

    node_result = await graph._append_dialogue_turn(state)
    messages = node_result["chat_history"]

    assert node_result["iteration"] == 3
    assert len(messages) == 2
    assert messages[0].speaker == "interviewer"
    assert messages[0].content == "Tell me about the last failed discovery call."
    assert messages[1].speaker == "persona"
    assert messages[1].content == "Last Thursday I left a call with no clear next step."


async def test_validate_interview_completion_invokes_structured_llm() -> None:
    """Completion validator should decide whether the dialogue has enough signal."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    decision = InterviewCompletionDecision(
        should_finish=True,
        reasoning="A concrete commitment was collected.",
        notes_to_add=InterviewNotes(key_facts=["Customer agreed to send an artifact."]),
    )
    prompt_builder.build_validate_interview_completion_prompt.return_value = ["validator prompt"]
    llm_adapter.structured_ainvoke.return_value = decision
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = InterviewSimulationSchema(
        input_data=_input_data(),
        chat_history=_chat_history(),
        interviewer_notes=_interviewer_notes(),
        iteration=2,
    )

    node_result = await graph._validate_interview_completion(state)

    prompt_builder.build_validate_interview_completion_prompt.assert_called_once_with(
        input_data=_input_data(),
        chat_history=_chat_history(),
        interviewer_notes=_interviewer_notes(),
        iteration=2,
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(
        ["validator prompt"],
        InterviewCompletionDecision,
    )
    assert node_result == {"completion_decision": decision}


@pytest.mark.parametrize(
    ("state", "expected_route"),
    [
        (
            InterviewSimulationSchema(
                input_data=_input_data(),
                iteration=1,
                completion_decision=InterviewCompletionDecision(
                    should_finish=True,
                    reasoning="The interview collected a hard commitment.",
                ),
            ),
            "analyze_interview",
        ),
        (
            InterviewSimulationSchema(
                input_data=_input_data(max_iterations=3),
                iteration=3,
                completion_decision=InterviewCompletionDecision(
                    should_finish=False,
                    reasoning="More follow-up would be useful.",
                ),
            ),
            "analyze_interview",
        ),
        (
            InterviewSimulationSchema(
                input_data=_input_data(max_iterations=4),
                iteration=2,
                completion_decision=InterviewCompletionDecision(
                    should_finish=False,
                    reasoning="Need one more concrete example.",
                ),
            ),
            "generate_interviewer_question",
        ),
    ],
)
async def test_route_after_notes_update_selects_next_step(
    state: InterviewSimulationSchema,
    expected_route: str,
) -> None:
    """The graph should route only after validator notes are merged."""
    assert await _graph()._route_after_notes_update(state) == expected_route


async def test_update_interview_notes_merges_existing_and_new_notes() -> None:
    """The note-update node should preserve previous findings and append new observations."""
    state = InterviewSimulationSchema(
        interviewer_notes=InterviewNotes(
            key_facts=["Founder runs all discovery calls personally."],
            customer_pain_points=["Call notes are scattered."],
        ),
        completion_decision=InterviewCompletionDecision(
            should_finish=False,
            reasoning="Need more detail.",
            notes_to_add=InterviewNotes(
                key_facts=["The last failed call happened on Thursday."],
                customer_pain_points=["No clear next step after the call."],
                customer_ideas_or_suggestions=["A pre-call checklist could help."],
                jobs_to_be_done=["Turn conversations into reliable evidence."],
                emotional_signals=["Frustrated but not angry."],
            ),
        ),
    )

    node_result = await _graph()._update_interview_notes(state)
    notes = node_result["interviewer_notes"]

    assert notes.key_facts == [
        "Founder runs all discovery calls personally.",
        "The last failed call happened on Thursday.",
    ]
    assert notes.customer_pain_points == [
        "Call notes are scattered.",
        "No clear next step after the call.",
    ]
    assert notes.customer_ideas_or_suggestions == ["A pre-call checklist could help."]
    assert notes.jobs_to_be_done == ["Turn conversations into reliable evidence."]
    assert notes.emotional_signals == ["Frustrated but not angry."]


async def test_analyze_interview_invokes_structured_llm() -> None:
    """Final analysis node should create the interview report output contract."""
    llm_adapter = _mock_llm_adapter()
    prompt_builder = _mock_prompt_builder()
    prompt_builder.build_analyze_interview_prompt.return_value = ["analysis prompt"]
    llm_adapter.structured_ainvoke.return_value = _interview_report()
    graph = _graph_with_mocks(llm_adapter, prompt_builder)
    state = InterviewSimulationSchema(
        input_data=_input_data(),
        chat_history=_chat_history(),
        interviewer_notes=_interviewer_notes(),
    )

    node_result = await graph._analyze_interview(state)

    prompt_builder.build_analyze_interview_prompt.assert_called_once_with(
        input_data=_input_data(),
        chat_history=_chat_history(),
        interviewer_notes=_interviewer_notes(),
    )
    llm_adapter.structured_ainvoke.assert_awaited_once_with(["analysis prompt"], InterviewReport)
    assert node_result == {
        "interview_report": _interview_report(),
        "interviewer_notes": _interviewer_notes(),
    }


async def test_interview_simulation_process_runs_one_turn_and_reports() -> None:
    """The graph should run a complete interview turn and produce a final report."""
    llm_adapter = _mock_llm_adapter()
    llm_adapter.structured_ainvoke.side_effect = _get_structured_interview_response
    graph = InterviewSimulationGraph(
        llm_adapter=llm_adapter,
        prompt_builder=_real_prompt_builder(),
    )

    graph_output = await graph.process(_input_data(max_iterations=1))

    assert graph_output.interview_report == _interview_report()
    assert graph_output.interviewer_notes == InterviewNotes(
        key_facts=["The concrete failed call happened last Thursday."],
        customer_pain_points=["Notes were useless after the call."],
    )
    assert graph_output.chat_history == [
        InterviewMessage(
            speaker="interviewer",
            content="Tell me about the last discovery call that failed to produce useful evidence.",
        ),
        InterviewMessage(
            speaker="persona",
            content="Last Thursday I had a demo call and realized afterwards that my notes were useless.",
        ),
    ]


async def test_interview_simulation_preserves_final_notes_when_validator_finishes() -> None:
    """Final validator notes must be merged before the report analysis node runs."""
    llm_adapter = _mock_llm_adapter()
    llm_adapter.structured_ainvoke.side_effect = _get_finishing_interview_response
    graph = InterviewSimulationGraph(
        llm_adapter=llm_adapter,
        prompt_builder=_real_prompt_builder(),
    )

    graph_output = await graph.process(_input_data(max_iterations=5))

    assert graph_output.interviewer_notes == InterviewNotes(
        key_facts=["The persona agreed to send messy notes."],
        customer_pain_points=["The artifact is painful because notes are messy."],
    )
