"""Schemas for the pre-interview preparation graph."""

from typing import TypedDict

from pydantic import BaseModel, Field

from src.domains.interview.schemas.common import (
    BusinessContextReport,
    PreInterviewPlan,
)


class PreInterviewResearchPlan(BaseModel):
    """Search plan for collecting context before analysis."""

    research_query: str = Field(..., min_length=1)
    external_search_required: bool
    reasoning: str = Field(..., min_length=1)


class MainCustomerConcernsAnalysis(BaseModel):
    """Likely customer concerns extracted from the business context."""

    main_customer_concerns: list[str] = Field(..., min_length=1)


class HiddenRisksAnalysis(BaseModel):
    """Implicit customer, market, and interview risks extracted from context."""

    hidden_risks: list[str] = Field(..., min_length=1)


class ExpectedIdealResultAnalysis(BaseModel):
    """Ideal interview result and concrete customer commitments to seek."""

    expected_ideal_result: str = Field(..., min_length=1)


class InformationGoalsAnalysis(BaseModel):
    """Information goals and base interview questions for the next stage."""

    information_collection_goals: list[str] = Field(..., min_length=3, max_length=3)
    base_questions: list[str] = Field(..., min_length=3, max_length=3)


class PreInterviewAnalysisBundle(BaseModel):
    """Aggregated results from the four parallel analysis branches."""

    information_collection_goals: list[str] = Field(..., min_length=3, max_length=3)
    main_customer_concerns: list[str] = Field(..., min_length=1)
    hidden_risks: list[str] = Field(..., min_length=1)
    expected_ideal_result: str = Field(..., min_length=1)
    base_questions: list[str] = Field(..., min_length=3, max_length=3)


class PreInterviewPreparationInputData(BaseModel):
    """Input accepted by the pre-interview preparation graph."""

    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    industry_description: str = Field(..., min_length=1)
    rewritten_user_request: str = Field(..., min_length=1)
    user_controlled_knowledge_context: str = ""
    allow_external_search: bool = True


class PreInterviewPreparationSchema(TypedDict, total=False):
    """LangGraph state for the first interview-simulation stage."""

    input_data: PreInterviewPreparationInputData
    research_query: str
    external_search_required: bool
    business_context: BusinessContextReport
    main_customer_concerns: list[str]
    hidden_risks: list[str]
    expected_ideal_result: str
    information_collection_goals: list[str]
    base_questions: list[str]
    analysis_bundle: PreInterviewAnalysisBundle
    pre_interview_plan: PreInterviewPlan


class PreInterviewPreparationOutputSchema(TypedDict):
    """Filtered output emitted by the pre-interview preparation graph."""

    pre_interview_plan: PreInterviewPlan


class PreInterviewPreparationOutputData(BaseModel):
    """Validated output returned by ``PreInterviewPreparationGraph.process``."""

    pre_interview_plan: PreInterviewPlan
