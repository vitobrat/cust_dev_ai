"""Business logic service for the Interview domain."""

import uuid

from pydantic import JsonValue

from src.configs.consts import FINAL_REPORT_MARKDOWN_CONTENT_TYPE
from src.configs.log.logger import get_logger
from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.interview.exceptions import (
    InterviewDeletionFailed,
    InterviewError,
    InterviewFinalReportNotFound,
    InterviewGetFailed,
    InterviewUpdateFailed,
)
from src.domains.interview.infrastructure.graph.final_report_generation import (
    FinalReportGenerationGraph,
)
from src.domains.interview.infrastructure.graph.interview_orchestrator import (
    InterviewOrchestratorGraph,
)
from src.domains.interview.schemas.common import (
    InterviewPersonaContext,
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.final_report import FinalInterviewReport
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
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.infrastructure.object_storage.client import ObjectStorageClientProtocol
from src.schemas.interview import (
    CreateInterviewSchema,
    FinalReportGenerationTaskInputData,
    InterviewRelEntitySchema,
    InterviewSimulationTaskInputData,
    UpdateInterviewSchema,
)
from src.schemas.persona import PersonaEntitySchema
from src.schemas.sub_interview import CreateSubInterviewSchema


class InterviewService:
    """Service layer for interview business logic.

    Encapsulates CRUD operations for interview entities, acting as the boundary
    between the HTTP layer and the persistence layer.

    Attributes:
        _interviews_repository: Repository for interview persistence operations.
        _interview_orchestrator_graph: Full-cycle graph for simulated interviews.
        _final_report_generation_graph: Graph that produces final analytics reports.
        _sub_interviews_repository: Repository used to persist per-persona interview sessions.
        _object_storage_client: Object storage client used for generated report files.
    """

    def __init__(
        self,
        interviews_repository: InterviewRepository,
        interview_orchestrator_graph: InterviewOrchestratorGraph | None = None,
        final_report_generation_graph: FinalReportGenerationGraph | None = None,
        sub_interviews_repository: SubInterviewRepository | None = None,
        object_storage_client: ObjectStorageClientProtocol | None = None,
    ) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._interviews_repository = interviews_repository
        self._interview_orchestrator_graph = interview_orchestrator_graph
        self._final_report_generation_graph = final_report_generation_graph
        self._sub_interviews_repository = sub_interviews_repository
        self._object_storage_client = object_storage_client

    async def simulate_interviews(
        self,
        task_input: InterviewSimulationTaskInputData,
    ) -> InterviewOrchestrationOutputData:
        """Run the full simulated interview cycle and persist every generated session.

        Args:
            task_input: Redis task payload with interview id, segment context, and graph controls.

        Returns:
            Validated orchestration graph output.

        Raises:
            InterviewError: If simulation dependencies are not configured or no personas exist.
        """
        if self._interview_orchestrator_graph is None or self._sub_interviews_repository is None:
            raise InterviewError("Interview simulation dependencies are not configured.")

        interview = await self.get_interview(task_input.interview_id)
        graph_input = self._build_orchestration_input(task_input, interview)
        self._logger.info(
            "Starting interview simulation: interview_id=%s personas=%s batch_size=%s.",
            task_input.interview_id,
            len(graph_input.personas),
            task_input.batch_size,
        )
        graph_output = await self._interview_orchestrator_graph.process(graph_input)
        await self._persist_interview_sessions(task_input.interview_id, task_input, graph_output)
        self._logger.info(
            "Interview simulation completed: interview_id=%s sessions=%s reports=%s.",
            task_input.interview_id,
            len(graph_output.interview_sessions),
            len(graph_output.interview_reports),
        )
        return graph_output

    async def generate_final_report(
        self,
        task_input: FinalReportGenerationTaskInputData,
    ) -> FinalReportGenerationOutputData:
        """Generate and persist a final analytics report from stored simulated interviews.

        Args:
            task_input: Redis task payload with interview id.

        Returns:
            Validated final report graph output.

        Raises:
            InterviewError: If dependencies are missing or no completed interview reports exist.
        """
        if self._final_report_generation_graph is None:
            raise InterviewError("Final report generation dependencies are not configured.")

        interview = await self.get_interview(task_input.interview_id)
        graph_input = self._build_final_report_input(task_input.interview_id, interview)
        self._logger.info(
            "Starting final report generation: interview_id=%s sessions=%s.",
            task_input.interview_id,
            len(graph_input.interview_sessions),
        )
        graph_output = await self._final_report_generation_graph.process(graph_input)
        await self._persist_generated_final_report(task_input.interview_id, graph_output.final_report)
        self._logger.info(
            "Final report generation completed: interview_id=%s source_sessions=%s report_url_saved=%s.",
            task_input.interview_id,
            graph_output.final_report.source_interview_count,
            True,
        )
        return graph_output

    async def get_final_report_file(self, interview_id: uuid.UUID) -> FinalReportFile:
        """Return the generated final report as a downloadable markdown file.

        Args:
            interview_id: UUID of the interview whose report should be downloaded.

        Returns:
            Markdown report file payload.

        Raises:
            InterviewFinalReportNotFound: If the interview has no generated report.
            InterviewError: If object storage is required but not configured.
        """
        interview = await self.get_interview(interview_id)
        if interview.report_content_url:
            return await self._download_stored_final_report(interview_id, interview.report_content_url)
        return self._build_legacy_final_report_file(interview_id, interview.final_report)

    async def create_interview(self, create_interview_data: CreateInterviewSchema) -> InterviewRelEntitySchema:
        """Persist a new interview entity.

        Args:
            create_interview_data: Validated creation payload.

        Returns:
            Newly created interview entity with generated ID and timestamps.
        """
        return await self._interviews_repository.create(create_interview_data)

    async def get_interview(self, interview_id: uuid.UUID) -> InterviewRelEntitySchema:
        """Retrieve a single interview by its identifier.

        Args:
            interview_id: UUID of the interview to retrieve.

        Returns:
            Interview entity with loaded relations if found.

        Raises:
            InterviewGetFailed: If no interview with the given ID exists.
        """
        interview = await self._interviews_repository.get_by_id(interview_id)

        if interview is None:
            self._logger.error("Interview not found: %s", interview_id)
            raise InterviewGetFailed(f"Interview with id={interview_id} does not exist.")

        return interview

    async def get_interviews(self, limit: int = 10, offset: int = 0) -> list[InterviewRelEntitySchema]:
        """Retrieve a paginated list of interviews.

        Args:
            limit: Maximum number of records to return. Defaults to 10.
            offset: Number of records to skip. Defaults to 0.

        Returns:
            List of interview entities (may be empty).
        """
        return await self._interviews_repository.get_all(limit, offset)

    async def count_interviews(self) -> int:
        """Return the total number of stored interviews.

        Returns:
            Integer count of interview records.
        """
        return await self._interviews_repository.get_count()

    async def update_interview(
        self,
        interview_id: uuid.UUID,
        update_interview_data: UpdateInterviewSchema,
    ) -> InterviewRelEntitySchema:
        """Apply a partial update to an existing interview.

        Args:
            interview_id: UUID of the interview to update.
            update_interview_data: Partial schema; only set fields are applied.

        Returns:
            Updated interview entity.

        Raises:
            InterviewUpdateFailed: If no interview with the given ID exists.
        """
        updated_interview = await self._interviews_repository.update_by_id(interview_id, update_interview_data)

        if updated_interview is None:
            self._logger.error("Interview not found for update: %s", interview_id)
            raise InterviewUpdateFailed(f"Interview with id={interview_id} does not exist.")

        return updated_interview

    async def delete_interview(self, interview_id: uuid.UUID) -> None:
        """Delete an interview by its identifier.

        Args:
            interview_id: UUID of the interview to delete.

        Raises:
            InterviewDeletionFailed: If no interview with the given ID exists.
        """
        deleted_id = await self._interviews_repository.delete_by_id(interview_id)

        if deleted_id is None:
            self._logger.error("Interview not found for deletion: %s", interview_id)
            raise InterviewDeletionFailed(f"Interview with id={interview_id} does not exist.")

    async def _persist_generated_final_report(
        self,
        interview_id: uuid.UUID,
        final_report: FinalInterviewReport,
    ) -> None:
        """Persist the generated report in object storage and keep JSONB as structured fallback."""
        if self._object_storage_client is None:
            raise InterviewError("Object storage client is not configured for final report generation.")

        stored_object = await self._object_storage_client.upload_text(
            self._build_final_report_object_key(interview_id),
            final_report.markdown_content,
            FINAL_REPORT_MARKDOWN_CONTENT_TYPE,
        )
        await self.update_interview(
            interview_id,
            UpdateInterviewSchema(
                report_content_url=stored_object.object_uri,
                final_report=final_report.model_dump(mode="json"),
            ),
        )

    async def _download_stored_final_report(
        self,
        interview_id: uuid.UUID,
        report_content_url: str,
    ) -> FinalReportFile:
        """Download a report file from object storage."""
        if self._object_storage_client is None:
            raise InterviewError("Object storage client is not configured for final report download.")

        stored_content = await self._object_storage_client.download_text(report_content_url)
        return FinalReportFile(
            report_content=stored_content.report_content.encode("utf-8"),
            filename=self._build_final_report_filename(interview_id),
            media_type=stored_content.content_type,
        )

    def _build_orchestration_input(
        self,
        task_input: InterviewSimulationTaskInputData,
        interview: InterviewRelEntitySchema,
    ) -> InterviewOrchestrationInputData:
        """Build graph input from a persisted interview and task payload."""
        personas = [self._build_persona_context(persona, task_input) for persona in interview.personas]
        if not personas:
            raise InterviewError(f"Interview {task_input.interview_id} has no personas to simulate.")

        return InterviewOrchestrationInputData(
            rewritten_user_request=task_input.rewritten_user_request,
            segment_name=task_input.segment_name,
            segment_description=task_input.segment_description,
            personas=personas,
            batch_size=task_input.batch_size,
            max_iterations_per_interview=task_input.max_iterations_per_interview,
            user_controlled_knowledge_context=task_input.user_controlled_knowledge_context,
            allow_external_search=task_input.allow_external_search,
        )

    @classmethod
    def _build_legacy_final_report_file(
        cls,
        interview_id: uuid.UUID,
        final_report: dict[str, JsonValue] | None,
    ) -> FinalReportFile:
        """Build downloadable markdown from legacy JSONB-only report rows."""
        if final_report is None:
            raise InterviewFinalReportNotFound(f"Interview {interview_id} has no generated final report.")

        markdown_content = final_report.get("markdown_content")
        if not isinstance(markdown_content, str) or not markdown_content.strip():
            raise InterviewFinalReportNotFound(f"Interview {interview_id} has no generated final report content.")

        return FinalReportFile(
            report_content=markdown_content.encode("utf-8"),
            filename=cls._build_final_report_filename(interview_id),
            media_type=FINAL_REPORT_MARKDOWN_CONTENT_TYPE,
        )

    @staticmethod
    def _build_final_report_object_key(interview_id: uuid.UUID) -> str:
        """Build deterministic Minio object key for an interview final report."""
        return f"interviews/{interview_id}/final-report.md"

    @staticmethod
    def _build_final_report_filename(interview_id: uuid.UUID) -> str:
        """Build deterministic download filename for an interview final report."""
        return f"interview-{interview_id}-final-report.md"

    @staticmethod
    def _build_persona_context(
        persona: PersonaEntitySchema,
        task_input: InterviewSimulationTaskInputData,
    ) -> InterviewPersonaContext:
        """Convert a stored persona entity into graph-ready persona context."""
        return InterviewPersonaContext(
            persona_id=persona.id,
            name=persona.demographic_state.personal_info_block.name,
            segment_name=task_input.segment_name,
            segment_description=task_input.segment_description,
            biography=persona.bio_description,
            experiences=persona.demographic_state.demographic_info,
        )

    async def _persist_interview_sessions(
        self,
        interview_id: uuid.UUID,
        task_input: InterviewSimulationTaskInputData,
        graph_output: InterviewOrchestrationOutputData,
    ) -> None:
        """Persist every simulated interview session as a completed sub-interview."""
        if self._sub_interviews_repository is None:
            raise InterviewError("Sub-interview repository is not configured.")

        for session in graph_output.interview_sessions:
            await self._sub_interviews_repository.create(
                CreateSubInterviewSchema(
                    interview_id=interview_id,
                    status=SubInterviewStatus.COMPLETED,
                    chat_history=self._build_session_payload(
                        session=session,
                        task_input=task_input,
                        graph_output=graph_output,
                    ),
                ),
            )

    def _build_final_report_input(
        self,
        interview_id: uuid.UUID,
        interview: InterviewRelEntitySchema,
    ) -> FinalReportGenerationInputData:
        """Build final report graph input from completed persisted sub-interviews."""
        session_payloads = [
            sub_interview.chat_history
            for sub_interview in interview.sub_interviews
            if sub_interview.status == SubInterviewStatus.COMPLETED
            and sub_interview.chat_history.get("type") == "custdev_interview_simulation"
        ]
        if not session_payloads:
            raise InterviewError(f"Interview {interview_id} has no completed interview reports for final reporting.")

        sessions = [self._build_simulated_session(payload, interview_id) for payload in session_payloads]
        first_payload = session_payloads[0]
        first_persona = sessions[0].persona_context
        return FinalReportGenerationInputData(
            rewritten_user_request=self._get_report_user_request(first_payload, interview_id, first_persona),
            segment_name=self._get_payload_text(first_payload, "segment_name", first_persona.segment_name),
            segment_description=self._get_payload_text(
                first_payload,
                "segment_description",
                first_persona.segment_description,
            ),
            final_pre_interview_plan=self._get_pre_interview_plan(first_payload, interview_id),
            interview_sessions=sessions,
        )

    @staticmethod
    def _build_session_payload(
        session: SimulatedInterviewSession,
        task_input: InterviewSimulationTaskInputData,
        graph_output: InterviewOrchestrationOutputData,
    ) -> dict[str, object]:
        """Build the JSONB payload stored in ``sub_interviews.chat_history``."""
        return {
            "schema_version": 1,
            "type": "custdev_interview_simulation",
            "rewritten_user_request": task_input.rewritten_user_request,
            "segment_name": task_input.segment_name,
            "segment_description": task_input.segment_description,
            "persona_context": session.persona_context.model_dump(mode="json"),
            "chat_history": [message.model_dump(mode="json") for message in session.chat_history],
            "interviewer_notes": session.interviewer_notes.model_dump(mode="json"),
            "interview_report": session.interview_report.model_dump(mode="json"),
            "final_pre_interview_plan": graph_output.final_pre_interview_plan.model_dump(mode="json"),
        }

    @staticmethod
    def _build_simulated_session(
        payload: dict[str, object],
        interview_id: uuid.UUID,
    ) -> SimulatedInterviewSession:
        """Restore a simulated interview session from the persisted JSONB payload."""
        try:
            return SimulatedInterviewSession.model_validate(
                {
                    "persona_context": payload["persona_context"],
                    "chat_history": payload["chat_history"],
                    "interviewer_notes": payload["interviewer_notes"],
                    "interview_report": payload["interview_report"],
                },
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise InterviewError(
                f"Interview {interview_id} contains malformed simulated interview payload.",
            ) from exc

    @staticmethod
    def _get_pre_interview_plan(
        payload: dict[str, object],
        interview_id: uuid.UUID,
    ) -> PreInterviewPlan:
        """Restore the final pre-interview plan saved by the simulation task."""
        raw_plan = payload.get("final_pre_interview_plan")
        if raw_plan is None:
            raise InterviewError(f"Interview {interview_id} has no final pre-interview plan saved.")
        return PreInterviewPlan.model_validate(raw_plan)

    @classmethod
    def _get_report_user_request(
        cls,
        payload: dict[str, object],
        interview_id: uuid.UUID,
        persona_context: InterviewPersonaContext,
    ) -> str:
        """Return stored rewritten request or a deterministic DB-derived fallback."""
        fallback = (
            f"Generate final custdev analytics for interview {interview_id} "
            f"and customer segment {persona_context.segment_name}: {persona_context.segment_description}"
        )
        return cls._get_payload_text(payload, "rewritten_user_request", fallback)

    @staticmethod
    def _get_payload_text(
        payload: dict[str, object],
        key: str,
        fallback: str,
    ) -> str:
        """Return non-empty text from payload, otherwise use fallback."""
        payload_text = payload.get(key)
        if isinstance(payload_text, str) and payload_text.strip():
            return payload_text
        return fallback
