"""Business logic service for the Interview domain."""

import uuid

from src.configs.log.logger import get_logger
from src.domains.interview.db.postgres.repository import InterviewRepository
from src.domains.interview.exceptions import (
    InterviewDeletionFailed,
    InterviewError,
    InterviewGetFailed,
    InterviewUpdateFailed,
)
from src.domains.interview.infrastructure.graph.interview_orchestrator import (
    InterviewOrchestratorGraph,
)
from src.domains.interview.schemas.common import (
    InterviewPersonaContext,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.interview_orchestration import (
    InterviewOrchestrationInputData,
    InterviewOrchestrationOutputData,
)
from src.domains.sub_interview.app.constants import SubInterviewStatus
from src.domains.sub_interview.db.postgres.repository import (
    SubInterviewRepository,
)
from src.schemas.interview import (
    CreateInterviewSchema,
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
        _sub_interviews_repository: Repository used to persist per-persona interview sessions.
    """

    def __init__(
        self,
        interviews_repository: InterviewRepository,
        interview_orchestrator_graph: InterviewOrchestratorGraph | None = None,
        sub_interviews_repository: SubInterviewRepository | None = None,
    ) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._interviews_repository = interviews_repository
        self._interview_orchestrator_graph = interview_orchestrator_graph
        self._sub_interviews_repository = sub_interviews_repository

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
        await self._persist_interview_sessions(task_input.interview_id, graph_output)
        self._logger.info(
            "Interview simulation completed: interview_id=%s sessions=%s reports=%s.",
            task_input.interview_id,
            len(graph_output.interview_sessions),
            len(graph_output.interview_reports),
        )
        return graph_output

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
                        graph_output=graph_output,
                    ),
                ),
            )

    @staticmethod
    def _build_session_payload(
        session: SimulatedInterviewSession,
        graph_output: InterviewOrchestrationOutputData,
    ) -> dict[str, object]:
        """Build the JSONB payload stored in ``sub_interviews.chat_history``."""
        return {
            "schema_version": 1,
            "type": "custdev_interview_simulation",
            "persona_context": session.persona_context.model_dump(mode="json"),
            "chat_history": [message.model_dump(mode="json") for message in session.chat_history],
            "interviewer_notes": session.interviewer_notes.model_dump(mode="json"),
            "interview_report": session.interview_report.model_dump(mode="json"),
            "final_pre_interview_plan": graph_output.final_pre_interview_plan.model_dump(mode="json"),
        }
