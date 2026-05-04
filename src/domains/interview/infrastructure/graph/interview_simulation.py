"""Interview simulation graph."""

from typing import Literal

from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START

from src.configs.consts import INTERVIEW_SIMULATION_RECURSION_LIMIT
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas.common import (
    InterviewMessage,
    InterviewNotes,
    InterviewReport,
)
from src.domains.interview.schemas.interview_simulation import (
    InterviewCompletionDecision,
    InterviewQuestionGeneration,
    InterviewSimulationContextRequest,
    InterviewSimulationInputData,
    InterviewSimulationOutputData,
    InterviewSimulationOutputSchema,
    InterviewSimulationSchema,
    PersonaAnswerGeneration,
)
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter


class InterviewSimulationGraph(
    BaseGraph[
        InterviewSimulationInputData,
        InterviewSimulationSchema,
        InterviewSimulationOutputSchema,
        InterviewSimulationOutputData,
    ],
):
    """LangGraph agent for running one simulated customer interview."""

    _prompt_builder: InterviewPromptManager

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        prompt_builder: InterviewPromptManager,
        recursion_limit: int = INTERVIEW_SIMULATION_RECURSION_LIMIT,
        langfuse_handler: CallbackHandler | None = None,
    ) -> None:
        """Initialize the graph with shared infrastructure dependencies."""
        super().__init__(
            state_schema=InterviewSimulationSchema,
            output_schema=InterviewSimulationOutputSchema,
            output_data_model=InterviewSimulationOutputData,
            llm_adapter=llm_adapter,
            prompt_builder=prompt_builder,
            recursion_limit=recursion_limit,
            langfuse_handler=langfuse_handler,
        )

    def _configurate_graph(self) -> None:
        self._add_interview_nodes()
        self._add_interview_edges()

    def _add_interview_nodes(self) -> None:
        """Add processing nodes to the simulation graph."""
        self.add_node("generate_interviewer_question", self._generate_interviewer_question)
        self.add_node("build_persona_context_query", self._build_persona_context_query)
        self.add_node("generate_persona_answer", self._generate_persona_answer)
        self.add_node("append_dialogue_turn", self._append_dialogue_turn)
        self.add_node("validate_interview_completion", self._validate_interview_completion)
        self.add_node("update_interview_notes", self._update_interview_notes)
        self.add_node("analyze_interview", self._analyze_interview)

    def _add_interview_edges(self) -> None:
        """Add transitions between simulation graph nodes."""
        self.add_edge(START, "generate_interviewer_question")
        self.add_edge("generate_interviewer_question", "build_persona_context_query")
        self.add_edge("build_persona_context_query", "generate_persona_answer")
        self.add_edge("generate_persona_answer", "append_dialogue_turn")
        self.add_edge("append_dialogue_turn", "validate_interview_completion")
        self.add_edge("validate_interview_completion", "update_interview_notes")
        self.add_conditional_edges(
            "update_interview_notes",
            self._route_after_notes_update,
            ["generate_interviewer_question", "analyze_interview"],
        )
        self.add_edge("analyze_interview", END)

    async def _generate_interviewer_question(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Generate the next unbiased, context-aware customer interview question."""
        prompt = self._prompt_builder.build_generate_interviewer_question_prompt(
            input_data=self._get_input_data(state),
            chat_history=self._get_chat_history(state),
            interviewer_notes=self._get_interviewer_notes(state),
            iteration=self._get_iteration(state),
        )
        generated_question: InterviewQuestionGeneration = await self._llm_adapter.structured_ainvoke(
            prompt,
            InterviewQuestionGeneration,
        )
        return {"current_question": generated_question.current_question}

    async def _build_persona_context_query(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Build a persona-side context packet for the answer-generation node."""
        prompt = self._prompt_builder.build_persona_context_query_prompt(
            input_data=self._get_input_data(state),
            chat_history=self._get_chat_history(state),
            current_question=self._get_required_str(state, "current_question"),
        )
        context_request: InterviewSimulationContextRequest = await self._llm_adapter.structured_ainvoke(
            prompt,
            InterviewSimulationContextRequest,
        )
        return {
            "persona_context_query": context_request.persona_context_query,
            "retrieved_persona_context": context_request.retrieved_persona_context,
            "persona_context_external_search_required": context_request.external_search_required,
        }

    async def _generate_persona_answer(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Generate the simulated customer answer using persona context."""
        prompt = self._prompt_builder.build_generate_persona_answer_prompt(
            input_data=self._get_input_data(state),
            chat_history=self._get_chat_history(state),
            current_question=self._get_required_str(state, "current_question"),
            persona_context_query=self._get_required_str(state, "persona_context_query"),
            retrieved_persona_context=self._get_required_str(state, "retrieved_persona_context"),
        )
        generated_answer: PersonaAnswerGeneration = await self._llm_adapter.structured_ainvoke(
            prompt,
            PersonaAnswerGeneration,
        )
        return {"current_answer": generated_answer.current_answer}

    async def _append_dialogue_turn(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Append the latest question and answer to the chat history."""
        question = self._get_required_str(state, "current_question")
        answer = self._get_required_str(state, "current_answer")
        return {
            "chat_history": [
                InterviewMessage(speaker="interviewer", content=question),
                InterviewMessage(speaker="persona", content=answer),
            ],
            "iteration": self._get_iteration(state) + 1,
        }

    async def _validate_interview_completion(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Decide whether to stop the interview after the latest answer."""
        prompt = self._prompt_builder.build_validate_interview_completion_prompt(
            input_data=self._get_input_data(state),
            chat_history=self._get_chat_history(state),
            interviewer_notes=self._get_interviewer_notes(state),
            iteration=self._get_iteration(state),
        )
        completion_decision: InterviewCompletionDecision = await self._llm_adapter.structured_ainvoke(
            prompt,
            InterviewCompletionDecision,
        )
        return {"completion_decision": completion_decision}

    async def _route_after_notes_update(
        self,
        state: InterviewSimulationSchema,
    ) -> Literal["generate_interviewer_question", "analyze_interview"]:
        """Route after validator notes have been merged into interview state."""
        if self._is_iteration_limit_reached(state):
            self._logger.warning(
                "Interview simulation reached max_iterations=%s; routing to analysis.",
                self._get_input_data(state).max_iterations,
            )
            return "analyze_interview"

        completion_decision = self._get_completion_decision(state)
        if completion_decision.should_finish:
            self._logger.info("Interview simulation finished by validator decision: %s", completion_decision.reasoning)
            return "analyze_interview"

        self._logger.debug("Interview simulation continuing after iteration=%s.", self._get_iteration(state))
        return "generate_interviewer_question"

    async def _update_interview_notes(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Merge validator notes into the running interviewer notes."""
        return {
            "interviewer_notes": self._merge_notes(
                self._get_interviewer_notes(state),
                self._get_completion_decision(state).notes_to_add,
            ),
        }

    async def _analyze_interview(
        self,
        state: InterviewSimulationSchema,
    ) -> InterviewSimulationSchema:
        """Build the final report for the completed simulated interview."""
        chat_history = self._get_chat_history(state)
        interviewer_notes = self._get_interviewer_notes(state)
        prompt = self._prompt_builder.build_analyze_interview_prompt(
            input_data=self._get_input_data(state),
            chat_history=chat_history,
            interviewer_notes=interviewer_notes,
        )
        interview_report: InterviewReport = await self._llm_adapter.structured_ainvoke(
            prompt,
            InterviewReport,
        )
        return {
            "interview_report": interview_report,
            "interviewer_notes": interviewer_notes,
        }

    @staticmethod
    def _merge_notes(current_notes: InterviewNotes, notes_to_add: InterviewNotes) -> InterviewNotes:
        """Return a merged copy of existing and newly extracted interview notes."""
        return InterviewNotes(
            key_facts=[*current_notes.key_facts, *notes_to_add.key_facts],
            customer_ideas_or_suggestions=[
                *current_notes.customer_ideas_or_suggestions,
                *notes_to_add.customer_ideas_or_suggestions,
            ],
            customer_pain_points=[
                *current_notes.customer_pain_points,
                *notes_to_add.customer_pain_points,
            ],
            jobs_to_be_done=[
                *current_notes.jobs_to_be_done,
                *notes_to_add.jobs_to_be_done,
            ],
            emotional_signals=[
                *current_notes.emotional_signals,
                *notes_to_add.emotional_signals,
            ],
        )

    @staticmethod
    def _get_required_str(state: InterviewSimulationSchema, key: str) -> str:
        """Return a non-empty string from state or raise a clear error."""
        raw_text: object = state.get(key)
        if not isinstance(raw_text, str) or not raw_text:
            raise ValueError(f"Interview simulation state is missing non-empty string '{key}'.")
        return raw_text

    @staticmethod
    def _get_iteration(state: InterviewSimulationSchema) -> int:
        """Return the current zero-based dialogue iteration counter."""
        iteration: object = state.get("iteration", 0)
        if not isinstance(iteration, int) or iteration < 0:
            raise ValueError("Interview simulation state has invalid 'iteration'.")
        return iteration

    @staticmethod
    def _get_input_data(state: InterviewSimulationSchema) -> InterviewSimulationInputData:
        """Return graph input data from state."""
        input_data: object = state.get("input_data")
        if isinstance(input_data, InterviewSimulationInputData):
            return input_data
        if isinstance(input_data, dict):
            return InterviewSimulationInputData.model_validate(input_data)
        raise ValueError("Interview simulation state is missing 'input_data'.")

    @staticmethod
    def _parse_chat_message(raw_message: object) -> InterviewMessage:
        """Return one validated chat message."""
        if isinstance(raw_message, InterviewMessage):
            return raw_message
        if isinstance(raw_message, dict):
            return InterviewMessage.model_validate(raw_message)
        raise ValueError("Interview simulation state has invalid 'chat_history' item.")

    @classmethod
    def _get_chat_history(cls, state: InterviewSimulationSchema) -> list[InterviewMessage]:
        """Return validated chat history from state."""
        chat_history = state.get("chat_history", [])
        if not isinstance(chat_history, list):
            raise ValueError("Interview simulation state has invalid 'chat_history'.")
        return [cls._parse_chat_message(raw_message) for raw_message in chat_history]

    @staticmethod
    def _get_interviewer_notes(state: InterviewSimulationSchema) -> InterviewNotes:
        """Return running interviewer notes from state."""
        interviewer_notes: object = state.get("interviewer_notes")
        if interviewer_notes is None:
            return InterviewNotes()
        if isinstance(interviewer_notes, InterviewNotes):
            return interviewer_notes
        if isinstance(interviewer_notes, dict):
            return InterviewNotes.model_validate(interviewer_notes)
        raise ValueError("Interview simulation state has invalid 'interviewer_notes'.")

    @classmethod
    def _is_iteration_limit_reached(cls, state: InterviewSimulationSchema) -> bool:
        """Check whether the hard dialogue iteration limit has been reached."""
        input_data = cls._get_input_data(state)
        return cls._get_iteration(state) >= input_data.max_iterations

    @staticmethod
    def _get_completion_decision(state: InterviewSimulationSchema) -> InterviewCompletionDecision:
        """Return validator decision from state."""
        completion_decision: object = state.get("completion_decision")
        if isinstance(completion_decision, InterviewCompletionDecision):
            return completion_decision
        if isinstance(completion_decision, dict):
            return InterviewCompletionDecision.model_validate(completion_decision)
        raise ValueError("Interview simulation state is missing 'completion_decision'.")
