"""Schemas for the full interview orchestration graph."""

import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field

from src.configs.consts import INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE
from src.domains.interview.schemas.common import (
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
)


class InterviewOrchestrationInputData(BaseModel):
    """Input accepted by the full interview simulation orchestration graph."""

    rewritten_user_request: str = Field(..., min_length=1)
    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    personas: list[InterviewPersonaContext] = Field(..., min_length=1)
    batch_size: int = Field(..., ge=1, le=INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE)
    max_iterations_per_interview: int = Field(default=8, ge=1)
    user_controlled_knowledge_context: str = ""
    allow_external_search: bool = True


class IndustryDescriptionGeneration(BaseModel):
    """Structured result of generating the industry context for the full cycle."""

    industry_description: str = Field(..., min_length=1)
    external_search_required: bool
    reasoning: str = Field(..., min_length=1)


class InterviewOrchestrationSchema(TypedDict, total=False):
    """LangGraph state for the full custdev interview simulation cycle."""

    input_data: InterviewOrchestrationInputData
    industry_description: str
    industry_external_search_required: bool
    pre_interview_plan: PreInterviewPlan
    active_persona_context: InterviewPersonaContext
    interview_reports: Annotated[list[InterviewReport], operator.add]
    final_pre_interview_plan: PreInterviewPlan


class InterviewOrchestrationOutputSchema(TypedDict):
    """Filtered output emitted by the full interview simulation graph."""

    interview_reports: list[InterviewReport]
    final_pre_interview_plan: PreInterviewPlan


class InterviewOrchestrationOutputData(BaseModel):
    """Validated output returned by ``InterviewOrchestratorGraph.process``."""

    interview_reports: list[InterviewReport]
    final_pre_interview_plan: PreInterviewPlan
