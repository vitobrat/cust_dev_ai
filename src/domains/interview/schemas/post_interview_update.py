"""Schemas for the post-interview update graph."""

from typing import TypedDict

from pydantic import BaseModel, Field

from src.domains.interview.schemas.common import (
    InterviewReport,
    PreInterviewPlan,
)


class PostInterviewUpdateInputData(BaseModel):
    """Input accepted by the post-interview report update graph."""

    previous_pre_interview_plan: PreInterviewPlan
    interview_reports: list[InterviewReport] = Field(..., min_length=1)


class PostInterviewUpdateSchema(TypedDict, total=False):
    """LangGraph state for the third post-interview stage."""

    input_data: PostInterviewUpdateInputData
    updated_pre_interview_plan: PreInterviewPlan


class PostInterviewUpdateOutputSchema(TypedDict):
    """Filtered output emitted by the post-interview update graph."""

    updated_pre_interview_plan: PreInterviewPlan


class PostInterviewUpdateOutputData(BaseModel):
    """Validated output returned by ``PostInterviewUpdateGraph.process``."""

    updated_pre_interview_plan: PreInterviewPlan
