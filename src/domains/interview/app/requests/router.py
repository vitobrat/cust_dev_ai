"""FastAPI router for Interview CRUD endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from src.configs.log.logger import get_logger
from src.domains.interview.app.requests.schema import (  # noqa: WPS235
    DeleteInterviewResponse,
    GetCountInterviewResponse,
    GetInterviewResponse,
    GetInterviewsRequest,
    GetInterviewsResponse,
    PostCreateInterviewRequest,
    PostCreateInterviewResponse,
    PutUpdateInterviewRequest,
    PutUpdateInterviewResponse,
)
from src.domains.interview.app.usecases.service import InterviewService
from src.domains.interview.exceptions import InterviewError, InterviewNotFound
from src.infrastructure.containers.domain import DomainContainer
from src.schemas.api_base import ResponseBase, StatusType

_logger = get_logger(__name__)

router = APIRouter(
    prefix="/interviews",
    tags=["interviews"],
)


@router.post("/", response_model=PostCreateInterviewResponse | ResponseBase, status_code=status.HTTP_201_CREATED)
@inject
async def create_interview(
    response: Response,
    request_data: PostCreateInterviewRequest,
    interview_service: InterviewService = Depends(Provide[DomainContainer.interview.interview_service]),
) -> PostCreateInterviewResponse | ResponseBase:
    """Create a new interview.

    Args:
        response: FastAPI response object used to override the status code on errors.
        request_data: Validated interview creation payload.
        interview_service: Injected interview service.

    Returns:
        Created interview entity wrapped in a success response, or an error response.
    """
    try:
        new_interview = await interview_service.create_interview(request_data)
    except InterviewError as exc:
        _logger.error("Interview creation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Interview creation failed: {exc}", status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during interview creation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PostCreateInterviewResponse(msg=new_interview, status=StatusType.SUCCESS)


@router.get("/count", response_model=GetCountInterviewResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def count_interviews(
    response: Response,
    interview_service: InterviewService = Depends(Provide[DomainContainer.interview.interview_service]),
) -> GetCountInterviewResponse | ResponseBase:
    """Get total count of interviews.

    Args:
        response: FastAPI response object used to override the status code on errors.
        interview_service: Injected interview service.

    Returns:
        Integer count wrapped in a success response, or an error response.
    """
    try:
        count = await interview_service.count_interviews()
    except Exception as exc:
        _logger.exception("Unexpected error during interview count")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetCountInterviewResponse(msg=count, status=StatusType.SUCCESS)


@router.get("/", response_model=GetInterviewsResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_interviews(
    response: Response,
    pagination: Annotated[GetInterviewsRequest, Query()],
    interview_service: InterviewService = Depends(Provide[DomainContainer.interview.interview_service]),
) -> GetInterviewsResponse | ResponseBase:
    """Get a paginated list of interviews.

    Args:
        response: FastAPI response object used to override the status code on errors.
        params: Pagination query parameters (limit, offset).
        interview_service: Injected interview service.

    Returns:
        List of interview entities wrapped in a success response, or an error response.
    """
    try:
        interviews = await interview_service.get_interviews(limit=pagination.limit, offset=pagination.offset)
    except Exception as exc:
        _logger.exception("Unexpected error during interviews retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetInterviewsResponse(msg=interviews, status=StatusType.SUCCESS)


@router.get("/{interview_id}", response_model=GetInterviewResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def get_interview(
    response: Response,
    interview_id: uuid.UUID,
    interview_service: InterviewService = Depends(Provide[DomainContainer.interview.interview_service]),
) -> GetInterviewResponse | ResponseBase:
    """Get a single interview by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        interview_id: UUID of the interview to retrieve.
        interview_service: Injected interview service.

    Returns:
        Interview entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        interview = await interview_service.get_interview(interview_id)
    except InterviewNotFound as exc:
        _logger.warning("Interview not found: %s", interview_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during interview retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetInterviewResponse(msg=interview, status=StatusType.SUCCESS)


@router.put("/{interview_id}", response_model=PutUpdateInterviewResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def update_interview(
    response: Response,
    interview_id: uuid.UUID,
    request_data: PutUpdateInterviewRequest,
    interview_service: InterviewService = Depends(Provide[DomainContainer.interview.interview_service]),
) -> PutUpdateInterviewResponse | ResponseBase:
    """Update an interview by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        interview_id: UUID of the interview to update.
        request_data: Validated partial update payload.
        interview_service: Injected interview service.

    Returns:
        Updated interview entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        updated_interview = await interview_service.update_interview(
            interview_id=interview_id,
            update_interview_data=request_data,
        )
    except InterviewNotFound as exc:
        _logger.warning("Interview not found for update: %s", interview_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during interview update")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PutUpdateInterviewResponse(msg=updated_interview, status=StatusType.SUCCESS)


@router.delete("/{interview_id}", response_model=DeleteInterviewResponse | ResponseBase, status_code=status.HTTP_200_OK)
@inject
async def delete_interview(
    response: Response,
    interview_id: uuid.UUID,
    interview_service: InterviewService = Depends(Provide[DomainContainer.interview.interview_service]),
) -> DeleteInterviewResponse | ResponseBase:
    """Delete an interview by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        interview_id: UUID of the interview to delete.
        interview_service: Injected interview service.

    Returns:
        Boolean success flag wrapped in a success response, or a 404/500 error response.
    """
    try:
        await interview_service.delete_interview(interview_id)
    except InterviewNotFound as exc:
        _logger.warning("Interview not found for deletion: %s", interview_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during interview deletion")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return DeleteInterviewResponse(msg=True, status=StatusType.SUCCESS)
