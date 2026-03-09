"""Request and response schemas for the SubInterview API endpoints."""

from src.schemas.api_base import PaginationBase, ResponseBase
from src.schemas.sub_interview import (
    CreateSubInterviewSchema,
    SubInterviewRelEntitySchema,
    UpdateSubInterviewSchema,
)


class PostCreateSubInterviewRequest(CreateSubInterviewSchema):
    """Request schema for sub-interview creation."""


class PostCreateSubInterviewResponse(ResponseBase):
    """Response schema for sub-interview creation."""

    msg: SubInterviewRelEntitySchema


class GetSubInterviewsRequest(PaginationBase):
    """Pagination query parameters for sub-interview list endpoint."""


class GetSubInterviewResponse(ResponseBase):
    """Response schema for a single sub-interview retrieval."""

    msg: SubInterviewRelEntitySchema


class GetSubInterviewsResponse(ResponseBase):
    """Response schema for paginated sub-interview list retrieval."""

    msg: list[SubInterviewRelEntitySchema]


class GetCountSubInterviewResponse(ResponseBase):
    """Response schema for sub-interview count."""

    msg: int


class PutUpdateSubInterviewRequest(UpdateSubInterviewSchema):
    """Request schema for partial sub-interview update."""


class PutUpdateSubInterviewResponse(ResponseBase):
    """Response schema for sub-interview update."""

    msg: SubInterviewRelEntitySchema


class DeleteSubInterviewResponse(ResponseBase):
    """Response schema for sub-interview deletion."""

    msg: bool
