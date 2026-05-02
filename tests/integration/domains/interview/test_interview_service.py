"""Integration tests for interview simulation service persistence."""

from __future__ import annotations

import uuid
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock

from src.domains.interview.app.usecases.service import InterviewService
from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.interview.schemas.common import (
    InterviewMessage,
    InterviewNotes,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.interview_orchestration import (
    InterviewOrchestrationOutputData,
)
from src.domains.persona.db.postgres.repository import PersonaRepository
from src.domains.persona.schemas.base import Gender, GeographicalLocation
from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.persona_blocks import (
    PersonalInfoBlock,
    ProblemBlock,
    PsychographicBehaviorBlock,
    SocialBlock,
)
from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.domains.user.db.postgres.repository import UserRepository
from src.infrastructure.db.postgres.client import DatabaseClient
from src.schemas.interview import (
    CreateInterviewSchema,
    InterviewSimulationTaskInputData,
)
from src.schemas.persona import CreatePersonaSchema
from src.schemas.user import CreateUserSchema


class _PersistedInterview(NamedTuple):
    interview_id: uuid.UUID
    persona_id: uuid.UUID


async def _persist_interview_with_persona(db_client: DatabaseClient) -> _PersistedInterview:
    user_repository = UserRepository(db_client)
    interview_repository = InterviewRepository(db_client)
    persona_repository = PersonaRepository(db_client)

    user = await user_repository.create(CreateUserSchema(name="integration-user"))
    interview = await interview_repository.create(CreateInterviewSchema(user_id=user.id))
    persona = await persona_repository.create(
        CreatePersonaSchema(
            interview_id=interview.id,
            demographic_state=_demographic_persona(),
            bio_description="Alex runs customer discovery personally.",
        ),
    )
    return _PersistedInterview(interview_id=interview.id, persona_id=persona.id)


def _task_input(interview_id: uuid.UUID) -> InterviewSimulationTaskInputData:
    return InterviewSimulationTaskInputData(
        interview_id=interview_id,
        rewritten_user_request="Validate AI-assisted custdev interviews.",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run discovery without a research team.",
        batch_size=1,
        max_iterations_per_interview=1,
    )


def _graph_output(persona_id: uuid.UUID) -> InterviewOrchestrationOutputData:
    return InterviewOrchestrationOutputData(
        interview_reports=[_interview_report()],
        interview_sessions=[
            SimulatedInterviewSession(
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
            ),
        ],
        final_pre_interview_plan=_pre_interview_plan(),
    )


def _persona_context(persona_id: uuid.UUID) -> InterviewPersonaContext:
    return InterviewPersonaContext(
        persona_id=persona_id,
        name="Alex",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run discovery without a research team.",
        biography="Alex runs customer discovery personally.",
        experiences=_demographic_persona().demographic_info,
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


def _demographic_persona() -> DemographicAttributePersona:
    return DemographicAttributePersona(
        personal_info_block=PersonalInfoBlock(
            name="Alex",
            age=34,
            gender=Gender.MALE,
            marital_status="married",
        ),
        problem_block=ProblemBlock(
            persona_specific_problem="Scattered discovery evidence",
            problem_spendings="Two hours after every sales call",
            person_suffering="High",
            is_manage_budget=True,
        ),
        social_block=SocialBlock(
            geographical_location=GeographicalLocation.CITY,
            education="Master of business administration",
            social_status="Founder-led SaaS lifestyle",
            profession="B2B SaaS founder",
        ),
        psychographic_behavior_block=PsychographicBehaviorBlock(
            psychological_profile="Analytical but time-constrained",
            idealogical_beliefs="Believes customer evidence should drive roadmap decisions",
            technology_adoption="Early adopter",
            communication_style="Direct and concise",
        ),
    )


async def test_interview_service_persists_simulated_session_payload(db_client: DatabaseClient) -> None:
    """The service should persist generated dialogue history and report into sub_interviews JSONB."""
    persisted = await _persist_interview_with_persona(db_client)
    sub_interviews_repository = SubInterviewRepository(db_client)
    orchestrator_graph = MagicMock()
    orchestrator_graph.process = AsyncMock(return_value=_graph_output(persisted.persona_id))
    service = InterviewService(
        interviews_repository=InterviewRepository(db_client),
        interview_orchestrator_graph=orchestrator_graph,
        sub_interviews_repository=sub_interviews_repository,
    )

    await service.simulate_interviews(_task_input(persisted.interview_id))

    sub_interviews = await sub_interviews_repository.get_all()
    payload = sub_interviews[0].chat_history
    assert len(sub_interviews) == 1
    assert sub_interviews[0].status == SubInterviewStatus.COMPLETED
    assert payload["interview_report"] == _interview_report().model_dump(mode="json")
    assert payload["chat_history"][1]["content"] == "My notes are scattered after calls."
