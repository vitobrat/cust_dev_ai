"""Request schema for final report generation task registration."""

import uuid

from pydantic import BaseModel


class PostFinalReportGenerationTaskRequest(BaseModel):
    """Request schema for registering a final interview report generation task."""

    user_id: uuid.UUID
    interview_id: uuid.UUID
