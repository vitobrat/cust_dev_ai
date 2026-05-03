"""Prompt manager for interview simulation agents."""

import json

from langchain_core.messages import BaseMessage, SystemMessage

from src.configs.consts import (
    FINAL_REPORT_PROMPT_FIELD_LIMIT,
    FINAL_REPORT_PROMPT_LIST_LIMIT,
    INTERVIEW_PERSONA_PROMPT_FIELD_LIMIT,
    INTERVIEW_PERSONA_PROMPT_SAMPLE_SIZE,
)
from src.domains.interview.schemas.common import (
    BusinessContextReport,
    InterviewMessage,
    InterviewNotes,
    InterviewPersonaContext,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.final_report import (
    FinalReportCoreSections,
    FinalReportPlanningAnalysis,
    FinalReportSection,
)
from src.domains.interview.schemas.final_report_generation import (
    FinalReportGenerationInputData,
)
from src.domains.interview.schemas.interview_orchestration import (
    InterviewOrchestrationInputData,
)
from src.domains.interview.schemas.interview_simulation import (
    InterviewSimulationInputData,
)
from src.domains.interview.schemas.post_interview_update import (
    PostInterviewUpdateInputData,
)
from src.domains.interview.schemas.pre_interview import (
    PreInterviewAnalysisBundle,
    PreInterviewPreparationInputData,
)
from src.infrastructure.prompt.base_prompt_manager import BasePromptManager

_PRE_INTERVIEW_CATEGORY = "pre_interview_preparation"
_INTERVIEW_SIMULATION_CATEGORY = "interview_simulation"
_POST_INTERVIEW_UPDATE_CATEGORY = "post_interview_update"
_INTERVIEW_ORCHESTRATION_CATEGORY = "interview_orchestration"
_FINAL_REPORT_CATEGORY = "final_report_generation"


class InterviewPromptManager(BasePromptManager):
    """Build prompts for interview-domain LangGraph agents."""

    def build_generate_industry_description_prompt(
        self,
        input_data: InterviewOrchestrationInputData,
    ) -> list[BaseMessage]:
        """Build a prompt that generates compact industry context for the full interview cycle."""
        template = self.get_template(_INTERVIEW_ORCHESTRATION_CATEGORY, "generate_industry_description")
        output_example = self.get_template(
            _INTERVIEW_ORCHESTRATION_CATEGORY,
            "generate_industry_description_output_example",
        )
        system_prompt = template.format(
            rewritten_user_request=input_data.rewritten_user_request,
            segment_name=input_data.segment_name,
            segment_description=input_data.segment_description,
            personas=self._format_persona_segment_summary(input_data),
            user_controlled_knowledge_context=self._truncate_text(input_data.user_controlled_knowledge_context),
            allow_external_search=input_data.allow_external_search,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_context_research_query_prompt(
        self,
        input_data: PreInterviewPreparationInputData,
    ) -> list[BaseMessage]:
        """Build a prompt that decides what context should be researched."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "build_context_research_query")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "build_context_research_query_output_example")
        system_prompt = template.format(
            segment_name=input_data.segment_name,
            segment_description=input_data.segment_description,
            industry_description=input_data.industry_description,
            rewritten_user_request=input_data.rewritten_user_request,
            user_controlled_knowledge_context=input_data.user_controlled_knowledge_context,
            allow_external_search=input_data.allow_external_search,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_study_segment_and_industry_prompt(
        self,
        input_data: PreInterviewPreparationInputData,
        research_query: str,
        external_search_required: bool,
    ) -> list[BaseMessage]:
        """Build a prompt that synthesizes the segment and industry context."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "study_segment_and_industry")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "study_segment_and_industry_output_example")
        system_prompt = template.format(
            segment_name=input_data.segment_name,
            segment_description=input_data.segment_description,
            industry_description=input_data.industry_description,
            rewritten_user_request=input_data.rewritten_user_request,
            user_controlled_knowledge_context=input_data.user_controlled_knowledge_context,
            research_query=research_query,
            external_search_required=external_search_required,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_main_customer_concerns_prompt(
        self,
        business_context: BusinessContextReport,
    ) -> list[BaseMessage]:
        """Build a prompt that analyses likely customer concerns."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "analyse_main_customer_concerns")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "analyse_main_customer_concerns_output_example")
        system_prompt = template.format(
            business_context=business_context.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_hidden_risks_prompt(
        self,
        business_context: BusinessContextReport,
    ) -> list[BaseMessage]:
        """Build a prompt that analyses implicit risks."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "analyse_hidden_risks")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "analyse_hidden_risks_output_example")
        system_prompt = template.format(
            business_context=business_context.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_expected_ideal_result_prompt(
        self,
        business_context: BusinessContextReport,
    ) -> list[BaseMessage]:
        """Build a prompt that defines the ideal interview outcome."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "define_expected_ideal_result")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "define_expected_ideal_result_output_example")
        system_prompt = template.format(
            business_context=business_context.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_information_goals_prompt(
        self,
        business_context: BusinessContextReport,
    ) -> list[BaseMessage]:
        """Build a prompt that defines interview goals and base questions."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "define_information_goals")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "define_information_goals_output_example")
        system_prompt = template.format(
            business_context=business_context.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_generate_pre_interview_report_prompt(
        self,
        input_data: PreInterviewPreparationInputData,
        business_context: BusinessContextReport,
        analysis_bundle: PreInterviewAnalysisBundle,
    ) -> list[BaseMessage]:
        """Build a prompt that synthesizes the final pre-interview plan."""
        template = self.get_template(_PRE_INTERVIEW_CATEGORY, "generate_pre_interview_report")
        output_example = self.get_template(_PRE_INTERVIEW_CATEGORY, "generate_pre_interview_report_output_example")
        system_prompt = template.format(
            segment_name=input_data.segment_name,
            segment_description=input_data.segment_description,
            rewritten_user_request=input_data.rewritten_user_request,
            business_context=business_context.model_dump_json(indent=2),
            analysis_bundle=analysis_bundle.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_generate_interviewer_question_prompt(
        self,
        input_data: InterviewSimulationInputData,
        chat_history: list[InterviewMessage],
        interviewer_notes: InterviewNotes,
        iteration: int,
    ) -> list[BaseMessage]:
        """Build a prompt that generates the next interviewer question."""
        template = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "generate_interviewer_question")
        output_example = self.get_template(
            _INTERVIEW_SIMULATION_CATEGORY,
            "generate_interviewer_question_output_example",
        )
        system_prompt = template.format(
            input_data=input_data.model_dump_json(indent=2),
            chat_history=self._format_chat_history(chat_history),
            interviewer_notes=interviewer_notes.model_dump_json(indent=2),
            iteration=iteration,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_persona_context_query_prompt(
        self,
        input_data: InterviewSimulationInputData,
        chat_history: list[InterviewMessage],
        current_question: str,
    ) -> list[BaseMessage]:
        """Build a prompt that prepares persona-side context for answering."""
        template = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "build_persona_context_query")
        output_example = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "build_persona_context_query_output_example")
        system_prompt = template.format(
            input_data=input_data.model_dump_json(indent=2),
            chat_history=self._format_chat_history(chat_history),
            current_question=current_question,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_generate_persona_answer_prompt(
        self,
        input_data: InterviewSimulationInputData,
        chat_history: list[InterviewMessage],
        current_question: str,
        persona_context_query: str,
        retrieved_persona_context: str,
    ) -> list[BaseMessage]:
        """Build a prompt that generates the simulated persona answer."""
        template = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "generate_persona_answer")
        output_example = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "generate_persona_answer_output_example")
        system_prompt = template.format(
            input_data=input_data.model_dump_json(indent=2),
            chat_history=self._format_chat_history(chat_history),
            current_question=current_question,
            persona_context_query=persona_context_query,
            retrieved_persona_context=retrieved_persona_context,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_validate_interview_completion_prompt(
        self,
        input_data: InterviewSimulationInputData,
        chat_history: list[InterviewMessage],
        interviewer_notes: InterviewNotes,
        iteration: int,
    ) -> list[BaseMessage]:
        """Build a prompt that validates whether the interview should finish."""
        template = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "validate_interview_completion")
        output_example = self.get_template(
            _INTERVIEW_SIMULATION_CATEGORY,
            "validate_interview_completion_output_example",
        )
        system_prompt = template.format(
            input_data=input_data.model_dump_json(indent=2),
            chat_history=self._format_chat_history(chat_history),
            interviewer_notes=interviewer_notes.model_dump_json(indent=2),
            iteration=iteration,
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_analyze_interview_prompt(
        self,
        input_data: InterviewSimulationInputData,
        chat_history: list[InterviewMessage],
        interviewer_notes: InterviewNotes,
    ) -> list[BaseMessage]:
        """Build a prompt that creates the final simulated-interview report."""
        template = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "analyze_interview")
        output_example = self.get_template(_INTERVIEW_SIMULATION_CATEGORY, "analyze_interview_output_example")
        system_prompt = template.format(
            input_data=input_data.model_dump_json(indent=2),
            chat_history=self._format_chat_history(chat_history),
            interviewer_notes=interviewer_notes.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_updated_pre_interview_report_prompt(
        self,
        input_data: PostInterviewUpdateInputData,
    ) -> list[BaseMessage]:
        """Build a prompt that updates the pre-interview plan after interviews."""
        template = self.get_template(_POST_INTERVIEW_UPDATE_CATEGORY, "generate_updated_pre_interview_report")
        output_example = self.get_template(
            _POST_INTERVIEW_UPDATE_CATEGORY,
            "generate_updated_pre_interview_report_output_example",
        )
        system_prompt = template.format(
            previous_pre_interview_plan=input_data.previous_pre_interview_plan.model_dump_json(indent=2),
            interview_reports=self._format_interview_reports(input_data),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_plan_final_report_prompt(
        self,
        input_data: FinalReportGenerationInputData,
    ) -> list[BaseMessage]:
        """Build a prompt that plans the final report structure and analysis."""
        template = self.get_template(_FINAL_REPORT_CATEGORY, "plan_final_report")
        output_example = self.get_template(_FINAL_REPORT_CATEGORY, "plan_final_report_output_example")
        system_prompt = template.format(
            final_report_context=self._format_final_report_context(input_data),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_user_persona_map_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
    ) -> list[BaseMessage]:
        """Build a prompt that generates the user persona map section."""
        return self._build_final_report_section_prompt(
            template_name="generate_user_persona_map",
            input_data=input_data,
            report_plan=report_plan,
        )

    def build_pain_points_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
    ) -> list[BaseMessage]:
        """Build a prompt that generates the customer pains section."""
        return self._build_final_report_section_prompt(
            template_name="generate_pain_points",
            input_data=input_data,
            report_plan=report_plan,
        )

    def build_key_insights_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
    ) -> list[BaseMessage]:
        """Build a prompt that generates key insights."""
        return self._build_final_report_section_prompt(
            template_name="generate_key_insights",
            input_data=input_data,
            report_plan=report_plan,
        )

    def build_failure_risk_analysis_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
    ) -> list[BaseMessage]:
        """Build a prompt that generates the failure-risk analysis."""
        return self._build_final_report_section_prompt(
            template_name="generate_failure_risk_analysis",
            input_data=input_data,
            report_plan=report_plan,
        )

    def build_recommendations_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
    ) -> list[BaseMessage]:
        """Build a prompt that generates prioritized recommendations."""
        return self._build_final_report_section_prompt(
            template_name="generate_recommendations",
            input_data=input_data,
            report_plan=report_plan,
        )

    def build_main_report_body_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
        core_sections: FinalReportCoreSections,
    ) -> list[BaseMessage]:
        """Build a prompt that edits all analytical sections into the main report body."""
        template = self.get_template(_FINAL_REPORT_CATEGORY, "write_main_report_body")
        output_example = self.get_template(_FINAL_REPORT_CATEGORY, "generate_report_section_output_example")
        system_prompt = template.format(
            final_report_context=self._format_final_report_context(input_data),
            report_plan=report_plan.model_dump_json(indent=2),
            core_sections=core_sections.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_report_opening_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        main_body: FinalReportSection,
    ) -> list[BaseMessage]:
        """Build a prompt that writes the report opening."""
        template = self.get_template(_FINAL_REPORT_CATEGORY, "write_report_opening")
        output_example = self.get_template(_FINAL_REPORT_CATEGORY, "write_report_opening_output_example")
        system_prompt = template.format(
            final_report_context=self._format_final_report_context(input_data),
            main_body=main_body.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def build_report_conclusion_prompt(
        self,
        input_data: FinalReportGenerationInputData,
        main_body: FinalReportSection,
    ) -> list[BaseMessage]:
        """Build a prompt that writes the report conclusion."""
        template = self.get_template(_FINAL_REPORT_CATEGORY, "write_report_conclusion")
        output_example = self.get_template(_FINAL_REPORT_CATEGORY, "write_report_conclusion_output_example")
        system_prompt = template.format(
            final_report_context=self._format_final_report_context(input_data),
            main_body=main_body.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    def _build_final_report_section_prompt(
        self,
        template_name: str,
        input_data: FinalReportGenerationInputData,
        report_plan: FinalReportPlanningAnalysis,
    ) -> list[BaseMessage]:
        """Build one of the parallel final-report section prompts."""
        template = self.get_template(_FINAL_REPORT_CATEGORY, template_name)
        output_example = self.get_template(_FINAL_REPORT_CATEGORY, "generate_report_section_output_example")
        system_prompt = template.format(
            final_report_context=self._format_final_report_context(input_data),
            report_plan=report_plan.model_dump_json(indent=2),
            output_example=output_example,
        )
        return [SystemMessage(content=system_prompt)]

    @staticmethod
    def _format_chat_history(chat_history: list[InterviewMessage]) -> str:
        """Format chat messages as JSON for prompt templates."""
        return "\n".join(message.model_dump_json() for message in chat_history) or "[]"

    @staticmethod
    def _format_interview_reports(input_data: PostInterviewUpdateInputData) -> str:
        """Format interview reports as JSON lines for prompt templates."""
        return "\n".join(report.model_dump_json() for report in input_data.interview_reports)

    @classmethod
    def _format_final_report_context(cls, input_data: FinalReportGenerationInputData) -> str:
        """Format bounded final-report context for prompt templates."""
        context_payload = {
            "rewritten_user_request": input_data.rewritten_user_request,
            "segment_name": input_data.segment_name,
            "segment_description": input_data.segment_description,
            "final_pre_interview_plan": input_data.final_pre_interview_plan.model_dump(mode="json"),
            "interview_count": len(input_data.interview_sessions),
            "interview_sessions": [
                cls._format_final_report_session(session_index, session)
                for session_index, session in enumerate(input_data.interview_sessions, start=1)
            ],
        }
        return json.dumps(context_payload, ensure_ascii=False, indent=2)

    @classmethod
    def _format_final_report_session(
        cls,
        session_index: int,
        session: SimulatedInterviewSession,
    ) -> dict[str, object]:
        """Format one compact session summary without serializing full dialogue history."""
        return {
            "session_index": session_index,
            "persona": {
                "name": session.persona_context.name,
                "segment_name": session.persona_context.segment_name,
                "biography_signal": cls._truncate_text(
                    session.persona_context.biography,
                    FINAL_REPORT_PROMPT_FIELD_LIMIT,
                ),
                "experience_signal": cls._truncate_text(
                    session.persona_context.experiences,
                    FINAL_REPORT_PROMPT_FIELD_LIMIT,
                ),
            },
            "target_information": cls._truncate_list(session.interview_report.target_information),
            "important_quotes": cls._truncate_list(session.interview_report.important_quotes),
            "outcomes_or_agreements": cls._truncate_list(session.interview_report.outcomes_or_agreements),
            "recommendations": cls._truncate_list(session.interview_report.recommendations_for_next_interviews),
            "success_score": session.interview_report.success_score,
            "success_reasoning": cls._truncate_text(
                session.interview_report.success_reasoning,
                FINAL_REPORT_PROMPT_FIELD_LIMIT,
            ),
            "notes": {
                "key_facts": cls._truncate_list(session.interviewer_notes.key_facts),
                "customer_pain_points": cls._truncate_list(session.interviewer_notes.customer_pain_points),
                "jobs_to_be_done": cls._truncate_list(session.interviewer_notes.jobs_to_be_done),
                "emotional_signals": cls._truncate_list(session.interviewer_notes.emotional_signals),
            },
        }

    @classmethod
    def _truncate_list(cls, raw_items: list[str]) -> list[str]:
        """Return a bounded list of truncated strings for prompt safety."""
        return [
            cls._truncate_text(raw_item, FINAL_REPORT_PROMPT_FIELD_LIMIT)
            for raw_item in raw_items[:FINAL_REPORT_PROMPT_LIST_LIMIT]
        ]

    @classmethod
    def _format_persona_segment_summary(cls, input_data: InterviewOrchestrationInputData) -> str:
        """Format a bounded persona summary for the orchestration prompt."""
        sampled_personas = input_data.personas[:INTERVIEW_PERSONA_PROMPT_SAMPLE_SIZE]
        sample_lines = [cls._format_persona_summary(persona) for persona in sampled_personas]
        omitted_count = len(input_data.personas) - len(sampled_personas)
        header = (
            f"Total personas: {len(input_data.personas)}. "
            f"Bounded sample size: {len(sampled_personas)}. "
            f"Omitted personas: {max(omitted_count, 0)}."
        )
        return "\n".join([header, *sample_lines])

    @classmethod
    def _format_persona_summary(cls, persona: InterviewPersonaContext) -> str:
        """Format one compact persona line without serializing the full DTO."""
        return (
            f"- name={persona.name}; segment={persona.segment_name}; "
            f"bio_signal={cls._truncate_text(persona.biography)}; "
            f"experience_signal={cls._truncate_text(persona.experiences)}"
        )

    @staticmethod
    def _truncate_text(
        raw_text: str,
        max_length: int = INTERVIEW_PERSONA_PROMPT_FIELD_LIMIT,
    ) -> str:
        """Return a whitespace-normalized text snippet with a hard character limit."""
        normalized_text = " ".join(raw_text.split())
        if len(normalized_text) <= max_length:
            return normalized_text
        return f"{normalized_text[:max_length].rstrip()}..."
