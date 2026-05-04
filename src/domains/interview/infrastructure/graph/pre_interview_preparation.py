"""Pre-interview preparation graph."""

from typing import TypeGuard

from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START

from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
)
from src.domains.interview.schemas import pre_interview
from src.domains.interview.schemas.common import (
    BusinessContextReport,
    PreInterviewPlan,
)
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter

PRE_INTERVIEW_PREPARATION_RECURSION_LIMIT = 10


class PreInterviewPreparationGraph(
    BaseGraph[
        pre_interview.PreInterviewPreparationInputData,
        pre_interview.PreInterviewPreparationSchema,
        pre_interview.PreInterviewPreparationOutputSchema,
        pre_interview.PreInterviewPreparationOutputData,
    ],
):
    """LangGraph agent for preparing the interview briefing."""

    _prompt_builder: InterviewPromptManager

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        prompt_builder: InterviewPromptManager,
        recursion_limit: int = PRE_INTERVIEW_PREPARATION_RECURSION_LIMIT,
        langfuse_handler: CallbackHandler | None = None,
    ) -> None:
        """Initialize the graph with shared infrastructure dependencies."""
        super().__init__(
            state_schema=pre_interview.PreInterviewPreparationSchema,
            output_schema=pre_interview.PreInterviewPreparationOutputSchema,
            output_data_model=pre_interview.PreInterviewPreparationOutputData,
            llm_adapter=llm_adapter,
            prompt_builder=prompt_builder,
            recursion_limit=recursion_limit,
            langfuse_handler=langfuse_handler,
        )

    def _configurate_graph(self) -> None:
        self._add_pre_interview_nodes()
        self._add_pre_interview_edges()

    def _add_pre_interview_nodes(self) -> None:
        """Add processing nodes to the pre-interview graph."""
        self.add_node("build_context_research_query", self._build_context_research_query)
        self.add_node("study_segment_and_industry", self._study_segment_and_industry)
        self.add_node("analyse_main_customer_concerns", self._analyse_main_customer_concerns)
        self.add_node("analyse_hidden_risks", self._analyse_hidden_risks)
        self.add_node("define_expected_ideal_result", self._define_expected_ideal_result)
        self.add_node("define_information_goals", self._define_information_goals)
        self.add_node("aggregate_analysis_results", self._aggregate_analysis_results)
        self.add_node("generate_pre_interview_report", self._generate_pre_interview_report)

    def _add_pre_interview_edges(self) -> None:
        """Add transitions between pre-interview graph nodes."""
        self.add_edge(START, "build_context_research_query")
        self.add_edge("build_context_research_query", "study_segment_and_industry")
        self._add_pre_interview_analysis_edges()
        self.add_edge("aggregate_analysis_results", "generate_pre_interview_report")
        self.add_edge("generate_pre_interview_report", END)

    def _add_pre_interview_analysis_edges(self) -> None:
        """Add fan-out and fan-in transitions for parallel analysis branches."""
        self.add_edge("study_segment_and_industry", "analyse_main_customer_concerns")
        self.add_edge("study_segment_and_industry", "analyse_hidden_risks")
        self.add_edge("study_segment_and_industry", "define_expected_ideal_result")
        self.add_edge("study_segment_and_industry", "define_information_goals")
        self.add_edge("analyse_main_customer_concerns", "aggregate_analysis_results")
        self.add_edge("analyse_hidden_risks", "aggregate_analysis_results")
        self.add_edge("define_expected_ideal_result", "aggregate_analysis_results")
        self.add_edge("define_information_goals", "aggregate_analysis_results")

    async def _build_context_research_query(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Build a search plan for internal knowledge or external context."""
        input_data = self._get_input_data(state)
        prompt = self._prompt_builder.build_context_research_query_prompt(input_data=input_data)
        research_plan: pre_interview.PreInterviewResearchPlan = await self._llm_adapter.structured_ainvoke(
            prompt,
            pre_interview.PreInterviewResearchPlan,
        )
        return {
            "research_query": research_plan.research_query,
            "external_search_required": input_data.allow_external_search and research_plan.external_search_required,
        }

    async def _study_segment_and_industry(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Synthesize segment and industry context into a compact report."""
        prompt = self._prompt_builder.build_study_segment_and_industry_prompt(
            input_data=self._get_input_data(state),
            research_query=self._get_required_str(state, "research_query"),
            external_search_required=self._get_required_bool(state, "external_search_required"),
        )
        business_context: BusinessContextReport = await self._llm_adapter.structured_ainvoke(
            prompt,
            BusinessContextReport,
        )
        return {"business_context": business_context}

    async def _analyse_main_customer_concerns(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Analyze what likely worries the customer most."""
        business_context = self._get_business_context(state)
        prompt = self._prompt_builder.build_main_customer_concerns_prompt(business_context=business_context)
        analysis: pre_interview.MainCustomerConcernsAnalysis = await self._llm_adapter.structured_ainvoke(
            prompt,
            pre_interview.MainCustomerConcernsAnalysis,
        )
        return {"main_customer_concerns": analysis.main_customer_concerns}

    async def _analyse_hidden_risks(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Analyze implicit risks in the segment and industry."""
        business_context = self._get_business_context(state)
        prompt = self._prompt_builder.build_hidden_risks_prompt(business_context=business_context)
        analysis: pre_interview.HiddenRisksAnalysis = await self._llm_adapter.structured_ainvoke(
            prompt,
            pre_interview.HiddenRisksAnalysis,
        )
        return {"hidden_risks": analysis.hidden_risks}

    async def _define_expected_ideal_result(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Define the ideal result and customer commitments expected from interviews."""
        business_context = self._get_business_context(state)
        prompt = self._prompt_builder.build_expected_ideal_result_prompt(business_context=business_context)
        analysis: pre_interview.ExpectedIdealResultAnalysis = await self._llm_adapter.structured_ainvoke(
            prompt,
            pre_interview.ExpectedIdealResultAnalysis,
        )
        return {"expected_ideal_result": analysis.expected_ideal_result}

    async def _define_information_goals(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Define three information goals and three base interview questions."""
        business_context = self._get_business_context(state)
        prompt = self._prompt_builder.build_information_goals_prompt(business_context=business_context)
        analysis: pre_interview.InformationGoalsAnalysis = await self._llm_adapter.structured_ainvoke(
            prompt,
            pre_interview.InformationGoalsAnalysis,
        )
        return {
            "information_collection_goals": analysis.information_collection_goals,
            "base_questions": analysis.base_questions,
        }

    async def _aggregate_analysis_results(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationSchema:
        """Aggregate the four analysis branches into one validated bundle."""
        return {
            "analysis_bundle": pre_interview.PreInterviewAnalysisBundle(
                information_collection_goals=self._get_required_list(state, "information_collection_goals"),
                main_customer_concerns=self._get_required_list(state, "main_customer_concerns"),
                hidden_risks=self._get_required_list(state, "hidden_risks"),
                expected_ideal_result=self._get_required_str(state, "expected_ideal_result"),
                base_questions=self._get_required_list(state, "base_questions"),
            ),
        }

    async def _generate_pre_interview_report(
        self,
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationOutputSchema:
        """Generate the final short briefing consumed by the interview agent."""
        analysis_bundle = self._get_analysis_bundle(state)
        prompt = self._prompt_builder.build_generate_pre_interview_report_prompt(
            input_data=self._get_input_data(state),
            business_context=self._get_business_context(state),
            analysis_bundle=analysis_bundle,
        )
        pre_interview_plan: PreInterviewPlan = await self._llm_adapter.structured_ainvoke(
            prompt,
            PreInterviewPlan,
        )
        return {"pre_interview_plan": pre_interview_plan}

    @classmethod
    def _get_required_list(cls, state: pre_interview.PreInterviewPreparationSchema, key: str) -> list[str]:
        """Return a non-empty string list from state or raise a clear error."""
        raw_sequence: object = state.get(key)
        if not cls._is_non_empty_str_list(raw_sequence):
            raise ValueError(f"Pre-interview preparation state is missing non-empty list '{key}'.")
        return raw_sequence

    @staticmethod
    def _get_required_str(state: pre_interview.PreInterviewPreparationSchema, key: str) -> str:
        """Return a non-empty string from state or raise a clear error."""
        raw_text: object = state.get(key)
        if not isinstance(raw_text, str) or not raw_text:
            raise ValueError(f"Pre-interview preparation state is missing non-empty string '{key}'.")
        return raw_text

    @staticmethod
    def _get_required_bool(state: pre_interview.PreInterviewPreparationSchema, key: str) -> bool:
        """Return a boolean from state or raise a clear error."""
        raw_flag: object = state.get(key)
        if not isinstance(raw_flag, bool):
            raise ValueError(f"Pre-interview preparation state is missing boolean '{key}'.")
        return raw_flag

    @staticmethod
    def _is_non_empty_str_list(raw_sequence: object) -> TypeGuard[list[str]]:
        """Check that a state value is a non-empty list of non-empty strings."""
        if not isinstance(raw_sequence, list) or not raw_sequence:
            return False
        for raw_candidate in raw_sequence:
            if not isinstance(raw_candidate, str) or not raw_candidate:
                return False
        return True

    @staticmethod
    def _get_input_data(
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewPreparationInputData:
        """Return validated input data from LangGraph state."""
        input_data: object = state.get("input_data")
        if isinstance(input_data, pre_interview.PreInterviewPreparationInputData):
            return input_data
        if isinstance(input_data, dict):
            return pre_interview.PreInterviewPreparationInputData.model_validate(input_data)
        raise ValueError("Pre-interview preparation state is missing 'input_data'.")

    @staticmethod
    def _get_business_context(state: pre_interview.PreInterviewPreparationSchema) -> BusinessContextReport:
        """Return validated business context from LangGraph state."""
        business_context: object = state.get("business_context")
        if isinstance(business_context, BusinessContextReport):
            return business_context
        if isinstance(business_context, dict):
            return BusinessContextReport.model_validate(business_context)
        raise ValueError("Pre-interview preparation state is missing 'business_context'.")

    @staticmethod
    def _get_analysis_bundle(
        state: pre_interview.PreInterviewPreparationSchema,
    ) -> pre_interview.PreInterviewAnalysisBundle:
        """Return the aggregated branch output from state."""
        analysis_bundle: object = state.get("analysis_bundle")
        if isinstance(analysis_bundle, pre_interview.PreInterviewAnalysisBundle):
            return analysis_bundle
        if isinstance(analysis_bundle, dict):
            return pre_interview.PreInterviewAnalysisBundle.model_validate(analysis_bundle)
        raise ValueError("Pre-interview preparation state is missing 'analysis_bundle'.")
