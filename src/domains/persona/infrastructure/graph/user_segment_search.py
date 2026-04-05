from typing import Any, Literal

from langgraph.graph import END, START

from src.domains.persona.infrastructure.graph.graph_utils import (
    get_analysis_result,
    get_last_segment,
    get_previous_segments,
    get_user_prompt,
    get_verification_result_is_valid,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.user_segment_search import (
    FindUserSegmentOutput,
    UserSegment,
    UserSegmentSearchInputData,
    UserSegmentSearchOutputData,
    UserSegmentSearchOutputSchema,
    UserSegmentSearchSchema,
    VerificationSegmentOutput,
)
from src.infrastructure.graph.base_graph import BaseGraph


class UserSegmentSearchGraph(
    BaseGraph[
        UserSegmentSearchInputData,
        UserSegmentSearchSchema,
        UserSegmentSearchOutputSchema,
        UserSegmentSearchOutputData,
    ],
):
    """
    Graph responsible for searching user segments based on a user prompt.
    The graph consists of the following steps:
    1. Analyse the user prompt to find relevant user segments.
    2. Find user segments based on the analysed user prompt.
    3. Verify the found user segments to ensure they are relevant and accurate.
    4. Output the final user segment search results.
    """

    _prompt_builder: PersonaPromptManager

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the graph with the necessary components."""
        super().__init__(
            state_schema=UserSegmentSearchSchema,
            output_schema=UserSegmentSearchOutputSchema,
            output_data_model=UserSegmentSearchOutputData,
            **kwargs,
        )

    def _configurate_graph(self) -> None:
        self.add_node("analyse_user_prompt", self._analyse_user_prompt)
        self.add_node("find_user_segment", self._find_user_segment)
        self.add_node("verify_user_segment", self._verify_user_segment)
        self.add_node("output", self._output_node)

        self.add_edge(START, "analyse_user_prompt")
        self.add_edge("analyse_user_prompt", "find_user_segment")
        self.add_edge("find_user_segment", "verify_user_segment")
        self.add_conditional_edges(
            "verify_user_segment",
            self._check_verification_result,
            ["analyse_user_prompt", "output"],
        )
        self.add_edge("output", END)

    async def _check_verification_result(
        self,
        state: UserSegmentSearchSchema,
    ) -> Literal["analyse_user_prompt", "output"]:
        """Check if the verification result is valid."""

        if get_verification_result_is_valid(state):
            return "output"
        else:
            return "analyse_user_prompt"

    async def _analyse_user_prompt(self, state: UserSegmentSearchSchema) -> UserSegmentSearchSchema:
        """Analyse the user prompt to find relevant user segments."""

        prompt = self._prompt_builder.build_analyse_user_prompt(
            user_prompt=get_user_prompt(state),
            previous_segments=get_previous_segments(state),
        )

        analyse_user_prompt: str = await self._llm_adapter.ainvoke(prompt)

        return {"analysis_result": analyse_user_prompt}

    async def _find_user_segment(self, state: UserSegmentSearchSchema) -> UserSegmentSearchSchema:
        """Find user segments based on the analysed user prompt."""

        prompt = self._prompt_builder.build_find_user_segment_prompt(
            user_prompt=get_user_prompt(state),
            analysis_result=get_analysis_result(state),
        )

        structured_response: FindUserSegmentOutput = await self._llm_adapter.structured_ainvoke(
            prompt,
            FindUserSegmentOutput,
        )

        return {"segments_history": state["segments_history"] + [UserSegment.from_find_output(structured_response)]}

    async def _verify_user_segment(self, state: UserSegmentSearchSchema) -> UserSegmentSearchSchema:
        """Verify the found user segments to ensure they are relevant and accurate."""
        last_segment: UserSegment = get_last_segment(state)

        prompt = self._prompt_builder.build_verify_user_segment_prompt(
            segment_name=last_segment.segment_name,
            unifying_problem_segment=last_segment.unifying_problem,
            where_to_find_segment=last_segment.where_to_find,
            segment_description=last_segment.segment_description,
        )

        structured_response: VerificationSegmentOutput = await self._llm_adapter.structured_ainvoke(
            prompt,
            VerificationSegmentOutput,
        )

        return {
            "verification_result": structured_response,
        }

    async def _output_node(self, state: UserSegmentSearchSchema) -> UserSegmentSearchOutputSchema:
        """Output the final user segment search results."""
        last_segment: UserSegment = get_last_segment(state)

        return {
            "segment_name": last_segment.segment_name,
            "segment_description": last_segment.segment_description,
        }
