"""Request and response schemas for the Interview API endpoints."""

from src.schemas.api_base import PaginationBase, ResponseBase
from src.schemas.interview import (
    CreateInterviewSchema,
    InterviewRelEntitySchema,
    UpdateInterviewSchema,
)


class PostCreateInterviewRequest(CreateInterviewSchema):
    """Request schema for interview creation."""


class PostCreateInterviewResponse(ResponseBase):
    """Response schema for interview creation."""

    msg: InterviewRelEntitySchema


class GetInterviewsRequest(PaginationBase):
    """Pagination query parameters for interview list endpoint."""


class GetInterviewResponse(ResponseBase):
    """Response schema for a single interview retrieval."""

    msg: InterviewRelEntitySchema


class GetInterviewsResponse(ResponseBase):
    """Response schema for paginated interview list retrieval."""

    msg: list[InterviewRelEntitySchema]


class GetCountInterviewResponse(ResponseBase):
    """Response schema for interview count."""

    msg: int


class PutUpdateInterviewRequest(UpdateInterviewSchema):
    """Request schema for partial interview update."""


class PutUpdateInterviewResponse(ResponseBase):
    """Response schema for interview update."""

    msg: InterviewRelEntitySchema


class DeleteInterviewResponse(ResponseBase):
    """Response schema for interview deletion."""

    msg: bool
