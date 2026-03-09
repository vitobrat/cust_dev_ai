"""FastAPI router for User CRUD endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from src.configs.log.logger import get_logger
from src.domains.user.app.requests.schema import (  # noqa: WPS235
    DeleteUserResponse,
    GetCountUserResponse,
    GetUserResponse,
    GetUsersRequest,
    GetUsersResponse,
    PostCreateUserRequest,
    PostCreateUserResponse,
    PutUpdateUserRequest,
    PutUpdateUserResponse,
)
from src.domains.user.app.usecases.service import UserService
from src.domains.user.exceptions import UserError, UserNotFound
from src.infrastructure.containers.domain import DomainContainer
from src.schemas.api_base import ResponseBase, StatusType

_logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/", response_model=PostCreateUserResponse | ResponseBase, status_code=status.HTTP_201_CREATED)
@inject
async def create_user(
    response: Response,
    request_data: PostCreateUserRequest,
    user_service: UserService = Depends(Provide[DomainContainer.user.user_service]),
) -> PostCreateUserResponse | ResponseBase:
    """Create a new user.

    Args:
        response: FastAPI response object used to override the status code on errors.
        request_data: Validated user creation payload.
        user_service: Injected user service.

    Returns:
        Created user entity wrapped in a success response, or an error response.
    """
    try:
        new_user = await user_service.create_user(request_data)
    except UserError as exc:
        _logger.error("User creation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"User creation failed: {exc}", status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during user creation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PostCreateUserResponse(msg=new_user, status=StatusType.SUCCESS)


@router.get("/count", response_model=GetCountUserResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def count_users(
    response: Response,
    user_service: UserService = Depends(Provide[DomainContainer.user.user_service]),
) -> GetCountUserResponse | ResponseBase:
    """Get total count of users.

    Args:
        response: FastAPI response object used to override the status code on errors.
        user_service: Injected user service.

    Returns:
        Integer count wrapped in a success response, or an error response.
    """
    try:
        count = await user_service.count_users()
    except Exception as exc:
        _logger.exception("Unexpected error during user count")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetCountUserResponse(msg=count, status=StatusType.SUCCESS)


@router.get("/", response_model=GetUsersResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_users(
    response: Response,
    pagination: Annotated[GetUsersRequest, Query()],
    user_service: UserService = Depends(Provide[DomainContainer.user.user_service]),
) -> GetUsersResponse | ResponseBase:
    """Get a paginated list of users.

    Args:
        response: FastAPI response object used to override the status code on errors.
        params: Pagination query parameters (limit, offset).
        user_service: Injected user service.

    Returns:
        List of user entities wrapped in a success response, or an error response.
    """
    try:
        users = await user_service.get_users(limit=pagination.limit, offset=pagination.offset)
    except Exception as exc:
        _logger.exception("Unexpected error during users retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetUsersResponse(msg=users, status=StatusType.SUCCESS)


@router.get("/{user_id}", response_model=GetUserResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_user(
    response: Response,
    user_id: uuid.UUID,
    user_service: UserService = Depends(Provide[DomainContainer.user.user_service]),
) -> GetUserResponse | ResponseBase:
    """Get a single user by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        user_id: UUID of the user to retrieve.
        user_service: Injected user service.

    Returns:
        User entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        user = await user_service.get_user(user_id)
    except UserNotFound as exc:
        _logger.warning("User not found: %s", user_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during user retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetUserResponse(msg=user, status=StatusType.SUCCESS)


@router.put("/{user_id}", response_model=PutUpdateUserResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def update_user(
    response: Response,
    user_id: uuid.UUID,
    request_data: PutUpdateUserRequest,
    user_service: UserService = Depends(Provide[DomainContainer.user.user_service]),
) -> PutUpdateUserResponse | ResponseBase:
    """Update a user by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        user_id: UUID of the user to update.
        request_data: Validated partial update payload.
        user_service: Injected user service.

    Returns:
        Updated user entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        updated_user = await user_service.update_user(
            user_id=user_id,
            update_user_data=request_data,
        )
    except UserNotFound as exc:
        _logger.warning("User not found for update: %s", user_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during user update")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PutUpdateUserResponse(msg=updated_user, status=StatusType.SUCCESS)


@router.delete("/{user_id}", response_model=DeleteUserResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def delete_user(
    response: Response,
    user_id: uuid.UUID,
    user_service: UserService = Depends(Provide[DomainContainer.user.user_service]),
) -> DeleteUserResponse | ResponseBase:
    """Delete a user by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        user_id: UUID of the user to delete.
        user_service: Injected user service.

    Returns:
        Boolean success flag wrapped in a success response, or a 404/500 error response.
    """
    try:
        await user_service.delete_user(user_id)
    except UserNotFound as exc:
        _logger.warning("User not found for deletion: %s", user_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during user deletion")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return DeleteUserResponse(msg=True, status=StatusType.SUCCESS)
