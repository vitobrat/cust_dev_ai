"""Shared schemas used by interview-domain graph agents."""

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """Source summary used while studying the segment and industry."""

    title: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    url: Optional[str] = None


class BusinessContextReport(BaseModel):
    """Synthesized context collected from user knowledge, RAG, or web resources."""

    segment_summary: str = Field(..., min_length=1)
    industry_summary: str = Field(..., min_length=1)
    rewritten_user_request: str = Field(..., min_length=1)
    evidence_summary: str = Field(..., min_length=1)
    data_freshness_warning: str = Field(..., min_length=1)
    quick_swot: str = Field(..., min_length=1)
    sources: list[ResearchSource] = Field(default_factory=list)


class PreInterviewPlan(BaseModel):
    """Final short report used as a briefing for the interview simulator."""

    information_collection_goal: str = Field(..., min_length=1)
    main_customer_concerns: list[str] = Field(..., min_length=1)
    hidden_risks: list[str] = Field(..., min_length=1)
    base_questions: list[str] = Field(..., min_length=3, max_length=3)
    expected_ideal_result: str = Field(..., min_length=1)


class InterviewPersonaContext(BaseModel):
    """Persona context used by the simulated customer agent."""

    persona_id: Optional[uuid.UUID] = None
    name: str = Field(..., min_length=1)
    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    biography: str = Field(..., min_length=1)
    experiences: str = Field(..., min_length=1)


class InterviewMessage(BaseModel):
    """Single message in the interview dialogue."""

    speaker: Literal["interviewer", "persona"]
    content: str = Field(..., min_length=1)  # noqa: WPS110


class InterviewNotes(BaseModel):
    """Running interviewer notes extracted from the dialogue."""

    key_facts: list[str] = Field(default_factory=list)
    customer_ideas_or_suggestions: list[str] = Field(default_factory=list)
    customer_pain_points: list[str] = Field(default_factory=list)
    jobs_to_be_done: list[str] = Field(default_factory=list)
    emotional_signals: list[str] = Field(default_factory=list)


class InterviewReport(BaseModel):
    """Final report produced for one simulated interview."""

    target_information: list[str] = Field(..., min_length=1)
    important_quotes: list[str] = Field(default_factory=list)
    outcomes_or_agreements: list[str] = Field(default_factory=list)
    recommendations_for_next_interviews: list[str] = Field(default_factory=list)
    is_successful: bool
    success_score: float = Field(..., ge=0, le=1)
    success_reasoning: str = Field(..., min_length=1)
