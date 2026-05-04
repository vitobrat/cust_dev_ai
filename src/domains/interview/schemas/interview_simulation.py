"""Schemas for the interview simulation graph."""

import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field

from src.domains.interview.schemas.common import (
    InterviewMessage,
    InterviewNotes,
    InterviewPersonaContext,
    InterviewReport,
    PreInterviewPlan,
)


class InterviewQuestionGeneration(BaseModel):
    """Generated interviewer question with short internal rationale."""

    current_question: str = Field(..., min_length=1)
    reasoning: str = Field(..., min_length=1)


class InterviewSimulationContextRequest(BaseModel):
    """Persona-side context request and synthesized retrieved context."""

    persona_context_query: str = Field(..., min_length=1)
    retrieved_persona_context: str = Field(..., min_length=1)
    external_search_required: bool
    reasoning: str = Field(..., min_length=1)


class PersonaAnswerGeneration(BaseModel):
    """Generated answer from the simulated customer persona."""

    current_answer: str = Field(..., min_length=1)


class InterviewCompletionDecision(BaseModel):
    """Validator result after one interview turn."""

    should_finish: bool
    reasoning: str = Field(..., min_length=1)
    notes_to_add: InterviewNotes = Field(default_factory=InterviewNotes)


class InterviewSimulationInputData(BaseModel):
    """Input accepted by the interview simulation graph."""

    pre_interview_plan: PreInterviewPlan
    rewritten_user_request: str = Field(..., min_length=1)
    persona_context: InterviewPersonaContext
    max_iterations: int = Field(default=8, ge=1)
    user_controlled_knowledge_context: str = ""
    allow_external_search: bool = True


class InterviewSimulationSchema(TypedDict, total=False):
    """LangGraph state for the simulated interview workflow."""

    input_data: InterviewSimulationInputData
    chat_history: Annotated[list[InterviewMessage], operator.add]
    interviewer_notes: InterviewNotes
    current_question: str
    persona_context_query: str
    persona_context_external_search_required: bool
    retrieved_persona_context: str
    current_answer: str
    iteration: int
    completion_decision: InterviewCompletionDecision
    interview_report: InterviewReport


class InterviewSimulationOutputSchema(TypedDict):
    """Filtered output emitted by the interview simulation graph."""

    interview_report: InterviewReport
    chat_history: list[InterviewMessage]
    interviewer_notes: InterviewNotes


class InterviewSimulationOutputData(BaseModel):
    """Validated output returned by ``InterviewSimulationGraph.process``."""

    interview_report: InterviewReport
    chat_history: list[InterviewMessage]
    interviewer_notes: InterviewNotes
