"""Post-interview plan update graph."""

from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START

from src.configs.consts import DEFAULT_GRAPH_RECURSION_LIMIT
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import PreInterviewPlan
from src.domains.interview.schemas.post_interview_update import (
    PostInterviewUpdateInputData,
    PostInterviewUpdateOutputData,
    PostInterviewUpdateOutputSchema,
    PostInterviewUpdateSchema,
)
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter


class PostInterviewUpdateGraph(
    BaseGraph[
        PostInterviewUpdateInputData,
        PostInterviewUpdateSchema,
        PostInterviewUpdateOutputSchema,
        PostInterviewUpdateOutputData,
    ],
):
    """LangGraph agent for updating the pre-interview briefing after interviews."""

    _prompt_builder: InterviewPromptManager

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        prompt_builder: InterviewPromptManager,
        recursion_limit: int = DEFAULT_GRAPH_RECURSION_LIMIT,
        langfuse_handler: CallbackHandler | None = None,
    ) -> None:
        """Initialize the graph with shared infrastructure dependencies."""
        super().__init__(
            state_schema=PostInterviewUpdateSchema,
            output_schema=PostInterviewUpdateOutputSchema,
            output_data_model=PostInterviewUpdateOutputData,
            llm_adapter=llm_adapter,
            prompt_builder=prompt_builder,
            recursion_limit=recursion_limit,
            langfuse_handler=langfuse_handler,
        )

    def _configurate_graph(self) -> None:
        self._add_post_interview_nodes()
        self._add_post_interview_edges()

    def _add_post_interview_nodes(self) -> None:
        """Add processing nodes to the post-interview graph."""
        self.add_node("generate_updated_pre_interview_report", self._generate_updated_pre_interview_report)

    def _add_post_interview_edges(self) -> None:
        """Add transitions between post-interview graph nodes."""
        self.add_edge(START, "generate_updated_pre_interview_report")
        self.add_edge("generate_updated_pre_interview_report", END)

    async def _generate_updated_pre_interview_report(
        self,
        state: PostInterviewUpdateSchema,
    ) -> PostInterviewUpdateOutputSchema:
        """Generate an updated pre-interview plan from prior plan and reports."""
        prompt = self._prompt_builder.build_updated_pre_interview_report_prompt(
            input_data=self._get_input_data(state),
        )
        updated_pre_interview_plan: PreInterviewPlan = await self._llm_adapter.structured_ainvoke(
            prompt,
            PreInterviewPlan,
        )
        return {"updated_pre_interview_plan": updated_pre_interview_plan}

    @staticmethod
    def _get_input_data(state: PostInterviewUpdateSchema) -> PostInterviewUpdateInputData:
        """Return validated input data from LangGraph state."""
        input_data: object = state.get("input_data")
        if isinstance(input_data, PostInterviewUpdateInputData):
            return input_data
        if isinstance(input_data, dict):
            return PostInterviewUpdateInputData.model_validate(input_data)
        raise ValueError("Post-interview update state is missing 'input_data'.")
