"""Final interview report generation graph."""

from langfuse.langchain import CallbackHandler
from langgraph.graph import END, START

from src.configs.consts import FINAL_REPORT_GENERATION_RECURSION_LIMIT
from src.domains.interview.infrastructure.prompt.prompt_manager import (
    InterviewPromptManager,
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
    FinalReportGenerationOutputSchema,
    FinalReportGenerationSchema,
)
from src.infrastructure.graph.base_graph import BaseGraph
from src.infrastructure.llm.llm_adapter import LLMAdapter


class FinalReportGenerationGraph(
    BaseGraph[
        FinalReportGenerationInputData,
        FinalReportGenerationSchema,
        FinalReportGenerationOutputSchema,
        FinalReportGenerationOutputData,
    ],
):
    """LangGraph agent for generating the final analytics report from all interviews."""

    _prompt_builder: InterviewPromptManager

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        prompt_builder: InterviewPromptManager,
        recursion_limit: int = FINAL_REPORT_GENERATION_RECURSION_LIMIT,
        langfuse_handler: CallbackHandler | None = None,
    ) -> None:
        """Initialize the graph with shared infrastructure dependencies."""
        super().__init__(
            state_schema=FinalReportGenerationSchema,
            output_schema=FinalReportGenerationOutputSchema,
            output_data_model=FinalReportGenerationOutputData,
            llm_adapter=llm_adapter,
            prompt_builder=prompt_builder,
            recursion_limit=recursion_limit,
            langfuse_handler=langfuse_handler,
        )

    def _configurate_graph(self) -> None:
        self._add_final_report_nodes()
        self._add_final_report_edges()

    def _add_final_report_nodes(self) -> None:
        """Add processing nodes to the final report graph."""
        self._add_analysis_nodes()
        self._add_editor_nodes()

    def _add_analysis_nodes(self) -> None:
        """Add planning and parallel analysis nodes."""
        self.add_node("plan_final_report", self._plan_final_report)
        self.add_node("generate_user_persona_map", self._generate_user_persona_map)
        self.add_node("generate_pain_points", self._generate_pain_points)
        self.add_node("generate_key_insights", self._generate_key_insights)
        self.add_node("generate_failure_risk_analysis", self._generate_failure_risk_analysis)
        self.add_node("generate_recommendations", self._generate_recommendations)

    def _add_editor_nodes(self) -> None:
        """Add final editing and assembly nodes."""
        self.add_node("write_main_report_body", self._write_main_report_body)
        self.add_node("write_report_opening", self._write_report_opening)
        self.add_node("write_report_conclusion", self._write_report_conclusion)
        self.add_node("assemble_final_report", self._assemble_final_report)

    def _add_final_report_edges(self) -> None:
        """Add transitions between final report graph nodes."""
        self.add_edge(START, "plan_final_report")
        self._add_parallel_section_edges()
        self.add_edge("write_main_report_body", "write_report_opening")
        self.add_edge("write_main_report_body", "write_report_conclusion")
        self.add_edge("write_report_opening", "assemble_final_report")
        self.add_edge("write_report_conclusion", "assemble_final_report")
        self.add_edge("assemble_final_report", END)

    def _add_parallel_section_edges(self) -> None:
        """Add fan-out and fan-in transitions for core analytical report sections."""
        section_nodes = (
            "generate_user_persona_map",
            "generate_pain_points",
            "generate_key_insights",
            "generate_failure_risk_analysis",
            "generate_recommendations",
        )
        for section_node in section_nodes:
            self.add_edge("plan_final_report", section_node)
            self.add_edge(section_node, "write_main_report_body")

    async def _plan_final_report(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Plan final report generation and identify counts and contradictions."""
        input_data = self._get_input_data(state)
        prompt = self._prompt_builder.build_plan_final_report_prompt(input_data=input_data)
        report_plan: FinalReportPlanningAnalysis = await self._llm_adapter.structured_ainvoke(
            prompt,
            FinalReportPlanningAnalysis,
        )
        self._logger.info(
            "Final report planning completed: sessions=%s problems=%s contradictions=%s.",
            len(input_data.interview_sessions),
            len(report_plan.problem_statistics),
            len(report_plan.contradictions),
        )
        return {"report_plan": report_plan}

    async def _generate_user_persona_map(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Generate the User Persona Map section."""
        section = await self._generate_report_section(state, "build_user_persona_map_prompt")
        return {"user_persona_map": section}

    async def _generate_pain_points(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Generate the customer pain points section."""
        section = await self._generate_report_section(state, "build_pain_points_prompt")
        return {"pain_points": section}

    async def _generate_key_insights(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Generate the key insights section."""
        section = await self._generate_report_section(state, "build_key_insights_prompt")
        return {"key_insights": section}

    async def _generate_failure_risk_analysis(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Generate the failure-risk analysis section."""
        section = await self._generate_report_section(state, "build_failure_risk_analysis_prompt")
        return {"failure_risk_analysis": section}

    async def _generate_recommendations(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Generate the recommendations section."""
        section = await self._generate_report_section(state, "build_recommendations_prompt")
        return {"recommendations": section}

    async def _write_main_report_body(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Edit the parallel analytical sections into one coherent main report body."""
        prompt = self._prompt_builder.build_main_report_body_prompt(
            input_data=self._get_input_data(state),
            report_plan=self._get_report_plan(state),
            core_sections=self._get_core_sections(state),
        )
        main_body: FinalReportSection = await self._llm_adapter.structured_ainvoke(
            prompt,
            FinalReportSection,
        )
        return {"main_body": main_body}

    async def _write_report_opening(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Write the short introduction and report scope."""
        prompt = self._prompt_builder.build_report_opening_prompt(
            input_data=self._get_input_data(state),
            main_body=self._get_main_body(state),
        )
        opening: FinalReportOpening = await self._llm_adapter.structured_ainvoke(
            prompt,
            FinalReportOpening,
        )
        return {"opening": opening}

    async def _write_report_conclusion(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationSchema:
        """Write the final takeaways and conclusion."""
        prompt = self._prompt_builder.build_report_conclusion_prompt(
            input_data=self._get_input_data(state),
            main_body=self._get_main_body(state),
        )
        conclusion: FinalReportConclusion = await self._llm_adapter.structured_ainvoke(
            prompt,
            FinalReportConclusion,
        )
        return {"conclusion": conclusion}

    async def _assemble_final_report(
        self,
        state: FinalReportGenerationSchema,
    ) -> FinalReportGenerationOutputSchema:
        """Assemble the final structured report and markdown document."""
        input_data = self._get_input_data(state)
        opening = self._get_opening(state)
        report_plan = self._get_report_plan(state)
        core_sections = self._get_core_sections(state)
        main_body = self._get_main_body(state)
        conclusion = self._get_conclusion(state)
        final_report = FinalInterviewReport(
            opening=opening,
            planning_analysis=report_plan,
            core_sections=core_sections,
            main_body=main_body,
            conclusion=conclusion,
            markdown_content=self._assemble_markdown(opening, main_body, conclusion),
            source_interview_count=len(input_data.interview_sessions),
        )
        return {"final_report": final_report}

    async def _generate_report_section(
        self,
        state: FinalReportGenerationSchema,
        prompt_builder_method: str,
    ) -> FinalReportSection:
        """Generate one structured final-report section with a selected prompt builder."""
        prompt_builder = getattr(self._prompt_builder, prompt_builder_method)
        prompt = prompt_builder(
            input_data=self._get_input_data(state),
            report_plan=self._get_report_plan(state),
        )
        section: FinalReportSection = await self._llm_adapter.structured_ainvoke(
            prompt,
            FinalReportSection,
        )
        return section

    @staticmethod
    def _assemble_markdown(
        opening: FinalReportOpening,
        main_body: FinalReportSection,
        conclusion: FinalReportConclusion,
    ) -> str:
        """Return the final markdown document from generated sections."""
        takeaways = "\n".join(f"- {takeaway}" for takeaway in conclusion.key_takeaways)
        return "\n\n".join(
            (
                f"# {opening.title}",
                opening.introduction,
                f"## Scope\n\n{opening.report_scope}",
                main_body.markdown_content,
                f"## Key Takeaways\n\n{takeaways}",
                f"## Conclusion\n\n{conclusion.conclusion}",
            ),
        )

    @staticmethod
    def _get_input_data(state: FinalReportGenerationSchema) -> FinalReportGenerationInputData:
        """Return validated input data from LangGraph state."""
        input_data: object = state.get("input_data")
        if isinstance(input_data, FinalReportGenerationInputData):
            return input_data
        if isinstance(input_data, dict):
            return FinalReportGenerationInputData.model_validate(input_data)
        raise ValueError("Final report generation state is missing 'input_data'.")

    @staticmethod
    def _get_report_plan(state: FinalReportGenerationSchema) -> FinalReportPlanningAnalysis:
        """Return validated planning analysis from state."""
        report_plan: object = state.get("report_plan")
        if isinstance(report_plan, FinalReportPlanningAnalysis):
            return report_plan
        if isinstance(report_plan, dict):
            return FinalReportPlanningAnalysis.model_validate(report_plan)
        raise ValueError("Final report generation state is missing 'report_plan'.")

    @classmethod
    def _get_core_sections(cls, state: FinalReportGenerationSchema) -> FinalReportCoreSections:
        """Return all validated core sections from state."""
        return FinalReportCoreSections(
            user_persona_map=cls._get_section(state, "user_persona_map"),
            pain_points=cls._get_section(state, "pain_points"),
            key_insights=cls._get_section(state, "key_insights"),
            failure_risk_analysis=cls._get_section(state, "failure_risk_analysis"),
            recommendations=cls._get_section(state, "recommendations"),
        )

    @staticmethod
    def _get_section(state: FinalReportGenerationSchema, key: str) -> FinalReportSection:
        """Return one validated section from state."""
        raw_section: object = state.get(key)
        if isinstance(raw_section, FinalReportSection):
            return raw_section
        if isinstance(raw_section, dict):
            return FinalReportSection.model_validate(raw_section)
        raise ValueError(f"Final report generation state is missing '{key}'.")

    @classmethod
    def _get_main_body(cls, state: FinalReportGenerationSchema) -> FinalReportSection:
        """Return the validated main body section from state."""
        return cls._get_section(state, "main_body")

    @staticmethod
    def _get_opening(state: FinalReportGenerationSchema) -> FinalReportOpening:
        """Return validated report opening from state."""
        opening: object = state.get("opening")
        if isinstance(opening, FinalReportOpening):
            return opening
        if isinstance(opening, dict):
            return FinalReportOpening.model_validate(opening)
        raise ValueError("Final report generation state is missing 'opening'.")

    @staticmethod
    def _get_conclusion(state: FinalReportGenerationSchema) -> FinalReportConclusion:
        """Return validated report conclusion from state."""
        conclusion: object = state.get("conclusion")
        if isinstance(conclusion, FinalReportConclusion):
            return conclusion
        if isinstance(conclusion, dict):
            return FinalReportConclusion.model_validate(conclusion)
        raise ValueError("Final report generation state is missing 'conclusion'.")
