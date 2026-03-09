"""FastAPI router for SubInterview CRUD endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from src.configs.log.logger import get_logger
from src.domains.sub_interview.app.requests.schema import (  # noqa: WPS235
    DeleteSubInterviewResponse,
    GetCountSubInterviewResponse,
    GetSubInterviewResponse,
    GetSubInterviewsRequest,
    GetSubInterviewsResponse,
    PostCreateSubInterviewRequest,
    PostCreateSubInterviewResponse,
    PutUpdateSubInterviewRequest,
    PutUpdateSubInterviewResponse,
)
from src.domains.sub_interview.app.usecases.service import SubInterviewService
from src.domains.sub_interview.exceptions import (
    SubInterviewError,
    SubInterviewNotFound,
)
from src.infrastructure.containers.domain import DomainContainer
from src.schemas.api_base import ResponseBase, StatusType

_logger = get_logger(__name__)

router = APIRouter(
    prefix="/sub_interviews",
    tags=["sub_interviews"],
)


@router.post("/", response_model=PostCreateSubInterviewResponse | ResponseBase, status_code=status.HTTP_201_CREATED)
@inject
async def create_sub_interview(
    response: Response,
    request_data: PostCreateSubInterviewRequest,
    sub_interview_service: SubInterviewService = Depends(Provide[DomainContainer.sub_interview.sub_interview_service]),
) -> PostCreateSubInterviewResponse | ResponseBase:
    """Create a new sub-interview.

    Args:
        response: FastAPI response object used to override the status code on errors.
        request_data: Validated sub-interview creation payload.
        sub_interview_service: Injected sub-interview service.

    Returns:
        Created sub-interview entity wrapped in a success response, or an error response.
    """
    try:
        new_sub_interview = await sub_interview_service.create_sub_interview(request_data)
    except SubInterviewError as exc:
        _logger.error("SubInterview creation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"SubInterview creation failed: {exc}", status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during sub-interview creation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PostCreateSubInterviewResponse(msg=new_sub_interview, status=StatusType.SUCCESS)


@router.get("/count", response_model=GetCountSubInterviewResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def count_sub_interviews(
    response: Response,
    sub_interview_service: SubInterviewService = Depends(Provide[DomainContainer.sub_interview.sub_interview_service]),
) -> GetCountSubInterviewResponse | ResponseBase:
    """Get total count of sub-interviews.

    Args:
        response: FastAPI response object used to override the status code on errors.
        sub_interview_service: Injected sub-interview service.

    Returns:
        Integer count wrapped in a success response, or an error response.
    """
    try:
        count = await sub_interview_service.count_sub_interviews()
    except Exception as exc:
        _logger.exception("Unexpected error during sub-interview count")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetCountSubInterviewResponse(msg=count, status=StatusType.SUCCESS)


@router.get("/", response_model=GetSubInterviewsResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_sub_interviews(
    response: Response,
    pagination: Annotated[GetSubInterviewsRequest, Query()],
    sub_interview_service: SubInterviewService = Depends(Provide[DomainContainer.sub_interview.sub_interview_service]),
) -> GetSubInterviewsResponse | ResponseBase:
    """Get a paginated list of sub-interviews.

    Args:
        response: FastAPI response object used to override the status code on errors.
        params: Pagination query parameters (limit, offset).
        sub_interview_service: Injected sub-interview service.

    Returns:
        List of sub-interview entities wrapped in a success response, or an error response.
    """
    try:
        sub_interviews = await sub_interview_service.get_sub_interviews(
            limit=pagination.limit,
            offset=pagination.offset,
        )
    except Exception as exc:
        _logger.exception("Unexpected error during sub-interviews retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetSubInterviewsResponse(msg=sub_interviews, status=StatusType.SUCCESS)


@router.get(
    "/{sub_interview_id}",
    response_model=GetSubInterviewResponse | ResponseBase,
    status_code=status.HTTP_200_OK,
)
@inject
async def get_sub_interview(
    response: Response,
    sub_interview_id: uuid.UUID,
    sub_interview_service: SubInterviewService = Depends(Provide[DomainContainer.sub_interview.sub_interview_service]),
) -> GetSubInterviewResponse | ResponseBase:
    """Get a single sub-interview by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        sub_interview_id: UUID of the sub-interview to retrieve.
        sub_interview_service: Injected sub-interview service.

    Returns:
        Sub-interview entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        sub_interview = await sub_interview_service.get_sub_interview(sub_interview_id)
    except SubInterviewNotFound as exc:
        _logger.warning("SubInterview not found: %s", sub_interview_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during sub-interview retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetSubInterviewResponse(msg=sub_interview, status=StatusType.SUCCESS)


@router.put(
    "/{sub_interview_id}",
    response_model=PutUpdateSubInterviewResponse | ResponseBase,
    status_code=status.HTTP_200_OK,
)
@inject
async def update_sub_interview(
    response: Response,
    sub_interview_id: uuid.UUID,
    request_data: PutUpdateSubInterviewRequest,
    sub_interview_service: SubInterviewService = Depends(Provide[DomainContainer.sub_interview.sub_interview_service]),
) -> PutUpdateSubInterviewResponse | ResponseBase:
    """Update a sub-interview by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        sub_interview_id: UUID of the sub-interview to update.
        request_data: Validated partial update payload.
        sub_interview_service: Injected sub-interview service.

    Returns:
        Updated sub-interview entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        updated_sub_interview = await sub_interview_service.update_sub_interview(
            sub_interview_id=sub_interview_id,
            update_sub_interview_data=request_data,
        )
    except SubInterviewNotFound as exc:
        _logger.warning("SubInterview not found for update: %s", sub_interview_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during sub-interview update")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PutUpdateSubInterviewResponse(msg=updated_sub_interview, status=StatusType.SUCCESS)


@router.delete(
    "/{sub_interview_id}",
    response_model=DeleteSubInterviewResponse | ResponseBase,
    status_code=status.HTTP_200_OK,
)
@inject
async def delete_sub_interview(
    response: Response,
    sub_interview_id: uuid.UUID,
    sub_interview_service: SubInterviewService = Depends(Provide[DomainContainer.sub_interview.sub_interview_service]),
) -> DeleteSubInterviewResponse | ResponseBase:
    """Delete a sub-interview by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        sub_interview_id: UUID of the sub-interview to delete.
        sub_interview_service: Injected sub-interview service.

    Returns:
        Boolean success flag wrapped in a success response, or a 404/500 error response.
    """
    try:
        await sub_interview_service.delete_sub_interview(sub_interview_id)
    except SubInterviewNotFound as exc:
        _logger.warning("SubInterview not found for deletion: %s", sub_interview_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during sub-interview deletion")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return DeleteSubInterviewResponse(msg=True, status=StatusType.SUCCESS)
