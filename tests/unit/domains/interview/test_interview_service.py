"""Unit tests for interview simulation service orchestration and persistence."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from src.domains.interview.app.usecases.service import InterviewService
from src.domains.interview.schemas.common import (
    InterviewMessage,
    InterviewNotes,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.interview_orchestration import (
    InterviewOrchestrationInputData,
    InterviewOrchestrationOutputData,
)
from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.schemas.interview import InterviewSimulationTaskInputData


def _task_input(interview_id: uuid.UUID) -> InterviewSimulationTaskInputData:
    return InterviewSimulationTaskInputData(
        interview_id=interview_id,
        rewritten_user_request="Validate AI-assisted custdev interviews.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run customer discovery without a research team.",
        batch_size=1,
        max_iterations_per_interview=3,
    )


def _pre_interview_plan() -> PreInterviewPlan:
    return PreInterviewPlan(
        information_collection_goal="Validate concrete workflow pain.",
        main_customer_concerns=["Discovery evidence is scattered."],
        hidden_risks=["Founders may praise automation without buying."],
        base_questions=[
            "Tell me about the last failed discovery call.",
            "What did it cost you?",
            "What would make you change the workflow?",
        ],
        expected_ideal_result="The persona commits to a concrete next step.",
    )


def _persona_context(persona_id: uuid.UUID) -> InterviewPersonaContext:
    return InterviewPersonaContext(
        persona_id=persona_id,
        name="Alex",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run customer discovery without a research team.",
        biography="Alex runs customer discovery personally.",
        experiences="Persona Profile: Alex\nMain Problem: scattered notes.",
    )


def _interview_report() -> InterviewReport:
    return InterviewReport(
        target_information=["Alex needs better post-call evidence."],
        important_quotes=["My notes are scattered."],
        outcomes_or_agreements=["Alex agreed to share one failed-call artifact."],
        recommendations_for_next_interviews=["Probe budget ownership earlier."],
        is_successful=True,
        success_score=0.82,
        success_reasoning="Concrete pain and next step were captured.",
    )


def _session(persona_id: uuid.UUID) -> SimulatedInterviewSession:
    return SimulatedInterviewSession(
        persona_context=_persona_context(persona_id),
        chat_history=[
            InterviewMessage(
                speaker="interviewer",
                content="Tell me about the last failed discovery call.",
            ),
            InterviewMessage(
                speaker="persona",
                content="My notes are scattered after calls.",
            ),
        ],
        interviewer_notes=InterviewNotes(customer_pain_points=["Post-call notes are scattered."]),
        interview_report=_interview_report(),
    )


def _interview_entity(interview_id: uuid.UUID, persona_id: uuid.UUID) -> SimpleNamespace:
    demographic_state = SimpleNamespace(
        personal_info_block=SimpleNamespace(name="Alex"),
        demographic_info="Persona Profile: Alex\nMain Problem: scattered notes.",
    )
    persona = SimpleNamespace(
        id=persona_id,
        demographic_state=demographic_state,
        bio_description="Alex runs customer discovery personally.",
    )
    return SimpleNamespace(id=interview_id, personas=[persona])


async def test_simulate_interviews_runs_graph_and_persists_each_session() -> None:
    """Simulation service should load personas, run the graph, and save each generated session."""
    interview_id = uuid.uuid4()
    persona_id = uuid.uuid4()
    graph_output = InterviewOrchestrationOutputData(
        interview_reports=[_interview_report()],
        interview_sessions=[_session(persona_id)],
        final_pre_interview_plan=_pre_interview_plan(),
    )
    interviews_repository = MagicMock()
    interviews_repository.get_by_id = AsyncMock(return_value=_interview_entity(interview_id, persona_id))
    sub_interviews_repository = MagicMock()
    sub_interviews_repository.create = AsyncMock()
    orchestrator_graph = MagicMock()
    orchestrator_graph.process = AsyncMock(return_value=graph_output)
    service = InterviewService(
        interviews_repository=interviews_repository,
        interview_orchestrator_graph=orchestrator_graph,
        sub_interviews_repository=sub_interviews_repository,
    )

    assert await service.simulate_interviews(_task_input(interview_id)) == graph_output

    graph_call_args = orchestrator_graph.process.await_args
    persist_call_args = sub_interviews_repository.create.await_args
    assert graph_call_args is not None
    assert persist_call_args is not None
    persisted_payload = persist_call_args.args[0]
    assert isinstance(graph_call_args.args[0], InterviewOrchestrationInputData)
    assert graph_call_args.args[0].personas == [_persona_context(persona_id)]
    assert persisted_payload.interview_id == interview_id
    assert persisted_payload.status == SubInterviewStatus.COMPLETED
    assert persisted_payload.chat_history["interview_report"] == _interview_report().model_dump(mode="json")
    assert persisted_payload.chat_history["chat_history"][1]["content"] == "My notes are scattered after calls."
