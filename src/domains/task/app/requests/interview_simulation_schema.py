"""Request schema for interview simulation task registration."""

import uuid

from pydantic import BaseModel, Field

from src.configs.consts import INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE


class PostInterviewSimulationTaskRequest(BaseModel):
    """Request schema for registering a full interview simulation task in Redis."""

    user_id: uuid.UUID
    interview_id: uuid.UUID
    rewritten_user_request: str = Field(..., min_length=1)
    segment_name: str = Field(..., min_length=1)
    segment_description: str = Field(..., min_length=1)
    batch_size: int = Field(default=3, ge=1, le=INTERVIEW_ORCHESTRATOR_MAX_BATCH_SIZE)
    max_iterations_per_interview: int = Field(default=8, ge=1)
    user_controlled_knowledge_context: str = ""
    allow_external_search: bool = True
