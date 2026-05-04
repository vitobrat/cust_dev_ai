"""Full custdev interview simulation orchestrator graph.

This graph binds the three interview-stage graph agents into one cycle:
industry-context generation, pre-interview preparation, batched interview
simulation, post-interview plan update, and final report collection.
"""

from typing import Literal

from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START
from langgraph.types import Send

from src.configs.consts import INTERVIEW_ORCHESTRATOR_RECURSION_LIMIT
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
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.interview_orchestration import (
    IndustryDescriptionGeneration,
    InterviewOrchestrationInputData,
    InterviewOrchestrationOutputData,
    InterviewOrchestrationOutputSchema,
    InterviewOrchestrationSchema,
)
from src.domains.interview.schemas.interview_simulation import (
    InterviewSimulationInputData,
)
from src.domains.interview.schemas.post_interview_update import (
    PostInterviewUpdateInputData,
)
from src.domains.interview.schemas.pre_interview import (
    PreInterviewPreparationInputData,
)
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter


class InterviewOrchestratorGraph(
    BaseGraph[
        InterviewOrchestrationInputData,
        InterviewOrchestrationSchema,
        InterviewOrchestrationOutputSchema,
        InterviewOrchestrationOutputData,
    ],
):
    """LangGraph agent that runs the complete custdev interview cycle."""

    _prompt_builder: InterviewPromptManager

    def __init__(
        self,
        pre_interview_preparation_graph: PreInterviewPreparationGraph,
        interview_simulation_graph: InterviewSimulationGraph,
        post_interview_update_graph: PostInterviewUpdateGraph,
        llm_adapter: LLMAdapter,
        prompt_builder: InterviewPromptManager,
        recursion_limit: int = INTERVIEW_ORCHESTRATOR_RECURSION_LIMIT,
        langfuse_handler: CallbackHandler | None = None,
    ) -> None:
        """Initialize the orchestrator with the three stage-specific graph agents."""
        self._pre_interview_preparation_graph = pre_interview_preparation_graph
        self._interview_simulation_graph = interview_simulation_graph
        self._post_interview_update_graph = post_interview_update_graph

        super().__init__(
            state_schema=InterviewOrchestrationSchema,
            output_schema=InterviewOrchestrationOutputSchema,
            output_data_model=InterviewOrchestrationOutputData,
            llm_adapter=llm_adapter,
            prompt_builder=prompt_builder,
            recursion_limit=recursion_limit,
            langfuse_handler=langfuse_handler,
        )

    def _configurate_graph(self) -> None:
        self._add_orchestrator_nodes()
        self._add_orchestrator_edges()

    def _add_orchestrator_nodes(self) -> None:
        """Add processing nodes to the orchestration graph."""
        self.add_node("generate_industry_description", self._generate_industry_description)
        self.add_node("run_pre_interview_preparation", self._run_pre_interview_preparation)
        self.add_node("run_interview_simulation", self._run_interview_simulation)
        self.add_node("run_post_interview_update", self._run_post_interview_update)
        self.add_node("finish_interview_cycle", self._finish_interview_cycle)

    def _add_orchestrator_edges(self) -> None:
        """Add transitions between orchestration graph nodes."""
        self.add_edge(START, "generate_industry_description")
        self.add_edge("generate_industry_description", "run_pre_interview_preparation")
        self.add_conditional_edges(
            "run_pre_interview_preparation",
            self._map_interview_batch,
            ["run_interview_simulation"],
        )
        self.add_edge("run_interview_simulation", "run_post_interview_update")
        self.add_conditional_edges(
            "run_post_interview_update",
            self._route_after_plan_update,
            ["run_interview_simulation", "finish_interview_cycle"],
        )
        self.add_edge("finish_interview_cycle", END)

    async def _generate_industry_description(
        self,
        state: InterviewOrchestrationSchema,
    ) -> InterviewOrchestrationSchema:
        """Generate current industry context from the rewritten user request."""
        input_data = self._get_input_data(state)
        prompt = self._prompt_builder.build_generate_industry_description_prompt(
            input_data=input_data,
        )
        generated_context: IndustryDescriptionGeneration = await self._llm_adapter.structured_ainvoke(
            prompt,
            IndustryDescriptionGeneration,
        )
        return {
            "industry_description": generated_context.industry_description,
            "industry_external_search_required": input_data.allow_external_search
            and generated_context.external_search_required,
        }

    async def _run_pre_interview_preparation(
        self,
        state: InterviewOrchestrationSchema,
    ) -> InterviewOrchestrationSchema:
        """Run the first-stage graph and store the initial pre-interview plan."""
        input_data = self._get_input_data(state)
        industry_description = self._get_required_str(state, "industry_description")

        graph_output = await self._pre_interview_preparation_graph.process(
            PreInterviewPreparationInputData(
                segment_name=input_data.segment_name,
                segment_description=input_data.segment_description,
                industry_description=industry_description,
                rewritten_user_request=input_data.rewritten_user_request,
                user_controlled_knowledge_context=input_data.user_controlled_knowledge_context,
                allow_external_search=input_data.allow_external_search,
            ),
        )

        return {
            "pre_interview_plan": graph_output.pre_interview_plan,
            "final_pre_interview_plan": graph_output.pre_interview_plan,
        }

    async def _map_interview_batch(
        self,
        state: InterviewOrchestrationSchema,
    ) -> list[Send]:
        """Fan out the next batch of personas into interview simulation runs."""
        pre_interview_plan = self._get_pre_interview_plan(state)
        selected_personas = self._select_next_personas(state)
        self._logger.info(
            "Starting interview batch: completed_reports=%s selected_personas=%s batch_size=%s.",
            len(self._get_interview_reports(state)),
            len(selected_personas),
            self._get_input_data(state).batch_size,
        )
        return [
            Send(
                "run_interview_simulation",
                InterviewOrchestrationSchema(
                    input_data=self._get_input_data(state),
                    pre_interview_plan=pre_interview_plan,
                    active_persona_context=persona_context,
                ),
            )
            for persona_context in selected_personas
        ]

    async def _run_interview_simulation(
        self,
        state: InterviewOrchestrationSchema,
    ) -> InterviewOrchestrationSchema:
        """Run the second-stage graph for one persona and append its report."""
        input_data = self._get_input_data(state)
        graph_output = await self._interview_simulation_graph.process(
            InterviewSimulationInputData(
                pre_interview_plan=self._get_pre_interview_plan(state),
                rewritten_user_request=input_data.rewritten_user_request,
                persona_context=self._get_active_persona_context(state),
                max_iterations=input_data.max_iterations_per_interview,
                user_controlled_knowledge_context=input_data.user_controlled_knowledge_context,
                allow_external_search=input_data.allow_external_search,
            ),
        )

        self._logger.debug("Interview simulation produced one report for the current batch.")
        return {
            "interview_reports": [graph_output.interview_report],
            "interview_sessions": [
                SimulatedInterviewSession(
                    persona_context=self._get_active_persona_context(state),
                    chat_history=graph_output.chat_history,
                    interviewer_notes=graph_output.interviewer_notes,
                    interview_report=graph_output.interview_report,
                ),
            ],
        }

    async def _run_post_interview_update(
        self,
        state: InterviewOrchestrationSchema,
    ) -> InterviewOrchestrationSchema:
        """Run the third-stage graph and store the updated pre-interview plan."""
        latest_batch_reports = self._get_latest_batch_reports(state)
        self._logger.info(
            "Updating pre-interview plan from latest batch reports: latest=%s accumulated=%s.",
            len(latest_batch_reports),
            len(self._get_interview_reports(state)),
        )
        graph_output = await self._post_interview_update_graph.process(
            PostInterviewUpdateInputData(
                previous_pre_interview_plan=self._get_pre_interview_plan(state),
                interview_reports=latest_batch_reports,
            ),
        )

        return {
            "pre_interview_plan": graph_output.updated_pre_interview_plan,
            "final_pre_interview_plan": graph_output.updated_pre_interview_plan,
        }

    async def _route_after_plan_update(
        self,
        state: InterviewOrchestrationSchema,
    ) -> list[Send] | Literal["finish_interview_cycle"]:
        """Continue with the next persona batch or finish after all reports are ready."""
        if self._has_remaining_personas(state):
            return await self._map_interview_batch(state)
        return "finish_interview_cycle"

    async def _finish_interview_cycle(
        self,
        state: InterviewOrchestrationSchema,
    ) -> InterviewOrchestrationSchema:
        """Expose the latest plan at graph end without duplicating report reducer state."""
        return {
            "final_pre_interview_plan": self._get_pre_interview_plan(state),
        }

    def _select_next_personas(self, state: InterviewOrchestrationSchema) -> list[InterviewPersonaContext]:
        """Return the next unprocessed persona batch."""
        input_data = self._get_input_data(state)
        completed_count = len(self._get_interview_reports(state))
        batch_end = min(completed_count + input_data.batch_size, len(input_data.personas))
        return input_data.personas[completed_count:batch_end]

    def _get_latest_batch_reports(self, state: InterviewOrchestrationSchema) -> list[InterviewReport]:
        """Return only reports generated by the latest completed batch."""
        input_data = self._get_input_data(state)
        reports = self._get_interview_reports(state)
        if not reports:
            raise ValueError("Interview orchestration state is missing reports for the latest batch.")
        latest_batch_start = ((len(reports) - 1) // input_data.batch_size) * input_data.batch_size
        return reports[latest_batch_start:]

    def _has_remaining_personas(self, state: InterviewOrchestrationSchema) -> bool:
        """Check whether some personas have not yet been interviewed."""
        input_data = self._get_input_data(state)
        return len(self._get_interview_reports(state)) < len(input_data.personas)

    @staticmethod
    def _get_input_data(state: InterviewOrchestrationSchema) -> InterviewOrchestrationInputData:
        """Return graph input data from state."""
        input_data: object = state.get("input_data")
        if isinstance(input_data, InterviewOrchestrationInputData):
            return input_data
        if isinstance(input_data, dict):
            return InterviewOrchestrationInputData.model_validate(input_data)
        raise ValueError("Interview orchestration state is missing 'input_data'.")

    @staticmethod
    def _get_pre_interview_plan(state: InterviewOrchestrationSchema) -> PreInterviewPlan:
        """Return the latest pre-interview plan from state."""
        pre_interview_plan: object = state.get("pre_interview_plan")
        if isinstance(pre_interview_plan, PreInterviewPlan):
            return pre_interview_plan
        if isinstance(pre_interview_plan, dict):
            return PreInterviewPlan.model_validate(pre_interview_plan)
        raise ValueError("Interview orchestration state is missing 'pre_interview_plan'.")

    @staticmethod
    def _get_active_persona_context(state: InterviewOrchestrationSchema) -> InterviewPersonaContext:
        """Return the persona assigned to the current interview simulation run."""
        persona_context: object = state.get("active_persona_context")
        if isinstance(persona_context, InterviewPersonaContext):
            return persona_context
        if isinstance(persona_context, dict):
            return InterviewPersonaContext.model_validate(persona_context)
        raise ValueError("Interview orchestration state is missing 'active_persona_context'.")

    @classmethod
    def _get_interview_reports(cls, state: InterviewOrchestrationSchema) -> list[InterviewReport]:
        """Return accumulated interview reports from state."""
        reports: object = state.get("interview_reports", [])
        if not isinstance(reports, list):
            raise ValueError("Interview orchestration state has invalid 'interview_reports'.")
        return [cls._parse_interview_report(raw_report) for raw_report in reports]

    @staticmethod
    def _get_required_str(state: InterviewOrchestrationSchema, key: str) -> str:
        """Return a non-empty string from state or raise a clear error."""
        raw_text: object = state.get(key)
        if not isinstance(raw_text, str) or not raw_text:
            raise ValueError(f"Interview orchestration state is missing non-empty string '{key}'.")
        return raw_text

    @staticmethod
    def _parse_interview_report(raw_report: object) -> InterviewReport:
        """Return one validated interview report from graph state."""
        if isinstance(raw_report, InterviewReport):
            return raw_report
        if isinstance(raw_report, dict):
            return InterviewReport.model_validate(raw_report)
        raise ValueError("Interview orchestration state has invalid 'interview_reports' item.")
