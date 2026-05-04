"""Schemas for the final interview report generation graph."""

from typing import TypedDict

from pydantic import BaseModel, Field

from src.configs.consts import FINAL_REPORT_MAX_INTERVIEW_SESSIONS
from src.domains.interview.schemas.common import (
    PreInterviewPlan,
    SimulatedInterviewSession,
)
from src.domains.interview.schemas.final_report import (
    FinalInterviewReport,
    FinalReportConclusion,
    FinalReportOpening,
    FinalReportPlanningAnalysis,
    FinalReportSection,
)


class FinalReportGenerationInputData(BaseModel):
    """Input accepted by the final report generation graph."""

    rewritten_user_request: str = Field(..., min_length=1)
    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    final_pre_interview_plan: PreInterviewPlan
    interview_sessions: list[SimulatedInterviewSession] = Field(
        ...,
        min_length=1,
        max_length=FINAL_REPORT_MAX_INTERVIEW_SESSIONS,
    )


class FinalReportGenerationSchema(TypedDict, total=False):
    """LangGraph state for final report generation."""

    input_data: FinalReportGenerationInputData
    report_plan: FinalReportPlanningAnalysis
    user_persona_map: FinalReportSection
    pain_points: FinalReportSection
    key_insights: FinalReportSection
    failure_risk_analysis: FinalReportSection
    recommendations: FinalReportSection
    main_body: FinalReportSection
    opening: FinalReportOpening
    conclusion: FinalReportConclusion
    final_report: FinalInterviewReport


class FinalReportGenerationOutputSchema(TypedDict):
    """Filtered output emitted by the final report generation graph."""

    final_report: FinalInterviewReport


class FinalReportGenerationOutputData(BaseModel):
    """Validated output returned by ``FinalReportGenerationGraph.process``."""

    final_report: FinalInterviewReport
