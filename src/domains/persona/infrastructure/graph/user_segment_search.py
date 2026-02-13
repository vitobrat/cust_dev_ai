from typing import Any, Literal

from langgraph.graph import END, START

from src.domains.persona.infrastructure.graph.graph_utils import (
    get_last_segment,
)
from src.domains.persona.infrastructure.prompt.prompt_manager import (
    PersonaPromptManager,
)
from src.domains.persona.schemas.user_segment_search import (
    FindUserSegmentOutput,
    UserSegment,
    UserSegmentSearchOutputSchema,
    UserSegmentSearchSchema,
    VerificationSegmentOutput,
)
from src.infrastructure.graph.base_graph import BaseGraph


class UserSegmentSearchGraph(BaseGraph):
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
        if state.verification_result and state.verification_result.is_valid:
            return "output"
        else:
            return "analyse_user_prompt"

    async def _analyse_user_prompt(self, state: UserSegmentSearchSchema) -> UserSegmentSearchSchema:
        """Analyse the user prompt to find relevant user segments."""
        prompt = self._prompt_builder.build_analyse_user_prompt(
            user_prompt=state.input_data.user_prompt,
            previous_segments=";\n".join([segment.segment_info for segment in state.segments_history]),
        )

        response: str = await self._llm_adapter.ainvoke(prompt)

        state.analysis_result = response
        return state

    async def _find_user_segment(self, state: UserSegmentSearchSchema) -> UserSegmentSearchSchema:
        """Find user segments based on the analysed user prompt."""
        prompt = self._prompt_builder.build_find_user_segment_prompt(
            user_prompt=state.input_data.user_prompt,
            analysis_result=state.analysis_result,
        )

        structured_response: FindUserSegmentOutput = await self._llm_adapter.structured_ainvoke(
            prompt,
            FindUserSegmentOutput,
        )

        state.segments_history.append(UserSegment.from_find_output(structured_response))
        return state

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

        state.verification_result = structured_response
        return state

    async def _output_node(self, state: UserSegmentSearchSchema) -> UserSegmentSearchOutputSchema:
        """Output the final user segment search results."""
        last_segment: UserSegment = get_last_segment(state)

        return UserSegmentSearchOutputSchema(
            segment_name=last_segment.segment_name,
            segment_description=last_segment.segment_description,
        )
