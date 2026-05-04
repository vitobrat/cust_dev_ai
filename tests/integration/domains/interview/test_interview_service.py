"""Integration tests for interview simulation service persistence."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from src.domains.interview.app.usecases.service import InterviewService
from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.interview.schemas import common as interview_common
from src.domains.interview.schemas import final_report as final_report_schema
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
from src.infrastructure.object_storage import client as object_storage_client
from src.schemas.interview import (
    CreateInterviewSchema,
    FinalReportGenerationTaskInputData,
    InterviewSimulationTaskInputData,
)
from src.schemas.persona import CreatePersonaSchema
from src.schemas.user import CreateUserSchema


class _FakeObjectStorageClient:
    """Object storage double used by integration tests that focus on PostgreSQL."""

    async def upload_text(
        self,
        object_key: str,
        markdown_content: str,
        content_type: str,
    ) -> object_storage_client.StoredObject:
        """Return a deterministic object URI for the uploaded report."""
        return object_storage_client.StoredObject(
            bucket_name="custdev-reports",
            object_key=object_key,
            object_uri=f"minio://custdev-reports/{object_key}",
            content_type=content_type,
        )

    async def download_text(
        self,
        object_reference: str,
    ) -> object_storage_client.StoredObjectContent:
        """Return deterministic markdown content."""
        return object_storage_client.StoredObjectContent(
            object_key=object_reference,
            report_content="# Stored report",
            content_type="text/markdown; charset=utf-8",
        )

    async def get_presigned_get_url(self, object_reference: str) -> str:
        """Return deterministic presigned URL."""
        return f"https://storage.example.com/{object_reference}"


async def _persist_interview_with_persona(db_client: DatabaseClient) -> tuple[uuid.UUID, uuid.UUID]:
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
    return interview.id, persona.id


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
            interview_common.SimulatedInterviewSession(
                persona_context=_persona_context(persona_id),
                chat_history=[
                    interview_common.InterviewMessage(
                        speaker="interviewer",
                        content="Tell me about the last failed discovery call.",
                    ),
                    interview_common.InterviewMessage(
                        speaker="persona",
                        content="My notes are scattered after calls.",
                    ),
                ],
                interviewer_notes=interview_common.InterviewNotes(
                    customer_pain_points=["Post-call notes are scattered."],
                ),
                interview_report=_interview_report(),
            ),
        ],
        final_pre_interview_plan=_pre_interview_plan(),
    )


def _persona_context(persona_id: uuid.UUID) -> interview_common.InterviewPersonaContext:
    return interview_common.InterviewPersonaContext(
        persona_id=persona_id,
        name="Alex",
        segment_name="Solo B2B SaaS founders",
        segment_description="Founders who run discovery without a research team.",
        biography="Alex runs customer discovery personally.",
        experiences=_demographic_persona().demographic_info,
    )


def _pre_interview_plan() -> interview_common.PreInterviewPlan:
    return interview_common.PreInterviewPlan(
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


def _interview_report() -> interview_common.InterviewReport:
    return interview_common.InterviewReport(
        target_information=["Alex needs better post-call evidence."],
        important_quotes=["My notes are scattered."],
        outcomes_or_agreements=["Alex agreed to share one failed-call artifact."],
        recommendations_for_next_interviews=["Probe budget ownership earlier."],
        is_successful=True,
        success_score=0.82,
        success_reasoning="Concrete pain and next step were captured.",
    )


def _final_report() -> final_report_schema.FinalInterviewReport:
    opening = final_report_schema.FinalReportOpening(
        title="Custdev interview report",
        introduction="This report summarizes completed simulated interviews.",
        report_scope="One persisted simulated interview.",
    )
    section = final_report_schema.FinalReportSection(
        section_kind="main_body",
        title="Main report",
        markdown_content="## Main report\n\nAlex has scattered notes.",
        evidence_quotes=["My notes are scattered."],
        data_points=["1 of 1 respondent mentioned scattered notes."],
    )
    return final_report_schema.FinalInterviewReport(
        opening=opening,
        planning_analysis=final_report_schema.FinalReportPlanningAnalysis(
            report_goal="Explain customer evidence.",
            writing_plan=["Quantify repeated pain."],
        ),
        core_sections=final_report_schema.FinalReportCoreSections(
            user_persona_map=section,
            pain_points=section,
            key_insights=section,
            failure_risk_analysis=section,
            recommendations=section,
        ),
        main_body=section,
        conclusion=final_report_schema.FinalReportConclusion(
            key_takeaways=["Scattered notes are the strongest signal."],
            conclusion="Validate budget ownership next.",
        ),
        markdown_content="# Custdev interview report\n\n## Main report\n\nAlex has scattered notes.",
        source_interview_count=1,
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
    interview_id, persona_id = await _persist_interview_with_persona(db_client)
    sub_interviews_repository = SubInterviewRepository(db_client)
    orchestrator_graph = MagicMock()
    orchestrator_graph.process = AsyncMock(return_value=_graph_output(persona_id))
    service = InterviewService(
        interviews_repository=InterviewRepository(db_client),
        interview_orchestrator_graph=orchestrator_graph,
        sub_interviews_repository=sub_interviews_repository,
    )

    await service.simulate_interviews(_task_input(interview_id))

    sub_interviews = await sub_interviews_repository.get_all()
    payload = sub_interviews[0].chat_history
    assert len(sub_interviews) == 1
    assert sub_interviews[0].status == SubInterviewStatus.COMPLETED
    assert payload["interview_report"] == _interview_report().model_dump(mode="json")
    assert payload["chat_history"][1]["content"] == "My notes are scattered after calls."
    assert payload["rewritten_user_request"] == _task_input(interview_id).rewritten_user_request


async def test_interview_service_persists_final_report_from_completed_sessions(db_client: DatabaseClient) -> None:
    """The service should load completed session reports from DB and persist final_report JSONB."""
    interview_id, persona_id = await _persist_interview_with_persona(db_client)
    interview_repository = InterviewRepository(db_client)
    orchestrator_graph = MagicMock()
    orchestrator_graph.process = AsyncMock(return_value=_graph_output(persona_id))
    simulation_service = InterviewService(
        interviews_repository=interview_repository,
        interview_orchestrator_graph=orchestrator_graph,
        sub_interviews_repository=SubInterviewRepository(db_client),
    )
    await simulation_service.simulate_interviews(_task_input(interview_id))
    final_report_graph = MagicMock()
    final_report_graph.process = AsyncMock(return_value=MagicMock(final_report=_final_report()))
    report_service = InterviewService(
        interviews_repository=interview_repository,
        final_report_generation_graph=final_report_graph,
        object_storage_client=_FakeObjectStorageClient(),
    )

    await report_service.generate_final_report(
        FinalReportGenerationTaskInputData(interview_id=interview_id),
    )

    updated_interview = await interview_repository.get_by_id(interview_id)
    graph_call = final_report_graph.process.await_args
    assert graph_call is not None
    report_input = graph_call.args[0]
    assert updated_interview is not None
    assert updated_interview.final_report == _final_report().model_dump(mode="json")
    assert updated_interview.report_content_url == f"minio://custdev-reports/interviews/{interview_id}/final-report.md"
    assert report_input.interview_sessions[0].interview_report == _interview_report()
