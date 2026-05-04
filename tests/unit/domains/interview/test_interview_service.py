"""Unit tests for interview simulation service orchestration and persistence."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domains.interview.app.usecases.service import InterviewService
from src.domains.interview.exceptions import InterviewError
from src.domains.interview.schemas.common import (
    InterviewMessage,
    InterviewNotes,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.final_report import (
    FinalInterviewReport,
    FinalReportConclusion,
    FinalReportCoreSections,
    FinalReportOpening,
    FinalReportPlanningAnalysis,
    FinalReportSection,
)
from src.domains.interview.schemas.final_report_generation import (
    FinalReportGenerationInputData,
    FinalReportGenerationOutputData,
)
from src.domains.interview.schemas.interview_orchestration import (
    InterviewOrchestrationInputData,
    InterviewOrchestrationOutputData,
)
from src.domains.interview.schemas.report_storage import FinalReportFile
from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.infrastructure.object_storage.client import (
    StoredObject,
    StoredObjectContent,
)
from src.schemas.interview import (
    FinalReportGenerationTaskInputData,
    InterviewSimulationTaskInputData,
    UpdateInterviewSchema,
)


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


def _interview_entity_with_sessions(interview_id: uuid.UUID, persona_id: uuid.UUID) -> SimpleNamespace:
    session = _session(persona_id)
    task_input = _task_input(interview_id)
    graph_output = InterviewOrchestrationOutputData(
        interview_reports=[_interview_report()],
        interview_sessions=[session],
        final_pre_interview_plan=_pre_interview_plan(),
    )
    return SimpleNamespace(
        id=interview_id,
        personas=[],
        sub_interviews=[
            SimpleNamespace(
                status=SubInterviewStatus.COMPLETED,
                chat_history=InterviewService._build_session_payload(session, task_input, graph_output),
            ),
        ],
    )


def _interview_entity_with_saved_report(interview_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=interview_id,
        report_content_url=f"minio://custdev-reports/interviews/{interview_id}/final-report.md",
        final_report=None,
    )


def _interview_entity_with_legacy_json_report(interview_id: uuid.UUID) -> SimpleNamespace:
    return SimpleNamespace(
        id=interview_id,
        report_content_url=None,
        final_report=_final_report().model_dump(mode="json"),
    )


def _final_report() -> FinalInterviewReport:
    opening = FinalReportOpening(
        title="Custdev interview report",
        introduction="Short introduction.",
        report_scope="One completed interview.",
    )
    section = FinalReportSection(
        section_kind="main_body",
        title="Main report",
        markdown_content="## Main report\n\nAlex has scattered notes.",
        evidence_quotes=["My notes are scattered."],
        data_points=["1 of 1 respondent mentioned scattered notes."],
    )
    conclusion = FinalReportConclusion(
        key_takeaways=["Scattered notes are the strongest signal."],
        conclusion="Validate budget ownership next.",
    )
    return FinalInterviewReport(
        opening=opening,
        planning_analysis=FinalReportPlanningAnalysis(
            report_goal="Explain customer evidence.",
            writing_plan=["Quantify pain and next steps."],
        ),
        core_sections=FinalReportCoreSections(
            user_persona_map=section,
            pain_points=section,
            key_insights=section,
            failure_risk_analysis=section,
            recommendations=section,
        ),
        main_body=section,
        conclusion=conclusion,
        markdown_content="# Custdev interview report\n\n## Main report\n\nAlex has scattered notes.",
        source_interview_count=1,
    )


class FakeObjectStorageClient:
    """Object storage test double for interview service tests."""

    def __init__(self) -> None:
        self.upload_calls: list[tuple[str, str, str]] = []
        self.download_calls: list[str] = []

    async def upload_text(
        self,
        object_key: str,
        markdown_content: str,
        content_type: str,
    ) -> StoredObject:
        """Record text upload and return a deterministic object URI."""
        self.upload_calls.append((object_key, markdown_content, content_type))
        return StoredObject(
            bucket_name="custdev-reports",
            object_key=object_key,
            object_uri=f"minio://custdev-reports/{object_key}",
            content_type=content_type,
        )

    async def download_text(self, object_reference: str) -> StoredObjectContent:
        """Record text download and return stored markdown."""
        self.download_calls.append(object_reference)
        return StoredObjectContent(
            object_key="interviews/report.md",
            report_content="# Stored report",
            content_type="text/markdown; charset=utf-8",
        )

    async def get_presigned_get_url(self, object_reference: str) -> str:
        """Return deterministic presigned URL."""
        return f"https://storage.example.com/{object_reference}"


def _get_report_generation_call_args(
    final_report_graph: MagicMock,
    interviews_repository: MagicMock,
) -> tuple[object, object]:
    graph_call = final_report_graph.process.await_args
    update_call = interviews_repository.update_by_id.await_args
    assert graph_call is not None
    assert update_call is not None
    return graph_call.args[0], update_call.args[1]


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
    assert persisted_payload.chat_history["rewritten_user_request"] == _task_input(interview_id).rewritten_user_request


async def test_generate_final_report_loads_sessions_from_db_and_persists_report() -> None:
    """Final report generation should upload markdown and persist JSON plus object URI."""
    interview_id = uuid.uuid4()
    persona_id = uuid.uuid4()
    graph_output = FinalReportGenerationOutputData(final_report=_final_report())
    object_storage = FakeObjectStorageClient()
    interviews_repository = MagicMock()
    interviews_repository.get_by_id = AsyncMock(return_value=_interview_entity_with_sessions(interview_id, persona_id))
    interviews_repository.update_by_id = AsyncMock(return_value=SimpleNamespace(id=interview_id))
    final_report_graph = MagicMock()
    final_report_graph.process = AsyncMock(return_value=graph_output)
    service = InterviewService(
        interviews_repository=interviews_repository,
        final_report_generation_graph=final_report_graph,
        object_storage_client=object_storage,
    )

    assert (
        await service.generate_final_report(FinalReportGenerationTaskInputData(interview_id=interview_id))
    ) == graph_output

    graph_input, update_data = _get_report_generation_call_args(final_report_graph, interviews_repository)
    expected_key = f"interviews/{interview_id}/final-report.md"
    assert isinstance(graph_input, FinalReportGenerationInputData)
    assert graph_input.interview_sessions == [_session(persona_id)]
    assert graph_input.final_pre_interview_plan == _pre_interview_plan()
    assert object_storage.upload_calls == [
        (expected_key, _final_report().markdown_content, "text/markdown; charset=utf-8"),
    ]
    assert isinstance(update_data, UpdateInterviewSchema)
    assert update_data.final_report == _final_report().model_dump(mode="json")
    assert update_data.report_content_url == f"minio://custdev-reports/{expected_key}"


async def test_generate_final_report_requires_completed_interview_reports() -> None:
    """The service must fail before calling LLM when no completed interview reports exist."""
    interview_id = uuid.uuid4()
    interviews_repository = MagicMock()
    interviews_repository.get_by_id = AsyncMock(return_value=SimpleNamespace(id=interview_id, sub_interviews=[]))
    final_report_graph = MagicMock()
    final_report_graph.process = AsyncMock()
    service = InterviewService(
        interviews_repository=interviews_repository,
        final_report_generation_graph=final_report_graph,
    )

    with pytest.raises(InterviewError):
        await service.generate_final_report(FinalReportGenerationTaskInputData(interview_id=interview_id))

    final_report_graph.process.assert_not_awaited()


async def test_get_final_report_file_downloads_markdown_from_object_storage() -> None:
    """Final report download should read the object referenced by report_content_url."""
    interview_id = uuid.uuid4()
    object_storage = FakeObjectStorageClient()
    interviews_repository = MagicMock()
    interviews_repository.get_by_id = AsyncMock(return_value=_interview_entity_with_saved_report(interview_id))
    service = InterviewService(
        interviews_repository=interviews_repository,
        object_storage_client=object_storage,
    )

    report_file = await service.get_final_report_file(interview_id)

    assert isinstance(report_file, FinalReportFile)
    assert report_file.report_content == b"# Stored report"
    assert report_file.filename == f"interview-{interview_id}-final-report.md"
    assert report_file.media_type == "text/markdown; charset=utf-8"
    assert object_storage.download_calls == [f"minio://custdev-reports/interviews/{interview_id}/final-report.md"]


async def test_get_final_report_file_falls_back_to_legacy_json_markdown() -> None:
    """Existing rows with only JSONB report content should remain downloadable."""
    interview_id = uuid.uuid4()
    interviews_repository = MagicMock()
    interviews_repository.get_by_id = AsyncMock(return_value=_interview_entity_with_legacy_json_report(interview_id))
    service = InterviewService(interviews_repository=interviews_repository)

    report_file = await service.get_final_report_file(interview_id)

    assert report_file.report_content == _final_report().markdown_content.encode("utf-8")
    assert report_file.filename == f"interview-{interview_id}-final-report.md"
    assert report_file.media_type == "text/markdown; charset=utf-8"
