"""Request and response schemas for the User API endpoints."""

from src.schemas.api_base import PaginationBase, ResponseBase
from src.schemas.user import (
    CreateUserSchema,
    UpdateUserSchema,
    UserRelEntitySchema,
)


class PostCreateUserRequest(CreateUserSchema):
    """Request schema for user creation."""


class PostCreateUserResponse(ResponseBase):
    """Response schema for user creation."""

    msg: UserRelEntitySchema


class GetUsersRequest(PaginationBase):
    """Pagination query parameters for user list endpoint."""


class GetUserResponse(ResponseBase):
    """Response schema for a single user retrieval."""

    msg: UserRelEntitySchema


class GetUsersResponse(ResponseBase):
    """Response schema for paginated user list retrieval."""

    msg: list[UserRelEntitySchema]


class GetCountUserResponse(ResponseBase):
    """Response schema for user count."""

    msg: int


class PutUpdateUserRequest(UpdateUserSchema):
    """Request schema for partial user update."""


class PutUpdateUserResponse(ResponseBase):
    """Response schema for user update."""

    msg: UserRelEntitySchema


class DeleteUserResponse(ResponseBase):
    """Response schema for user deletion."""

    msg: bool
