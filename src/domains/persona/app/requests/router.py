"""FastAPI router for Persona CRUD endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Response, status

from src.configs.log.logger import get_logger
from src.domains.persona.app.requests.schema import (  # noqa: WPS235
    DeletePersonaResponse,
    GetCountPersonaResponse,
    GetPersonaResponse,
    GetPersonasRequest,
    GetPersonasResponse,
    PostCreatePersonaRequest,
    PostCreatePersonaResponse,
    PutUpdatePersonaRequest,
    PutUpdatePersonaResponse,
)
from src.domains.persona.app.usecases.service import PersonaService
from src.domains.persona.exceptions import (
    PersonaCreationFailed,
    PersonaNotFound,
)
from src.infrastructure.containers.domain import PersonaContainer
from src.schemas.api_base import ResponseBase, StatusType

_logger = get_logger(__name__)

router = APIRouter(
    prefix="/persona",
    tags=["persona"],
)


@router.post("/", response_model=PostCreatePersonaResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_persona(
    response: Response,
    request_data: PostCreatePersonaRequest,
    persona_service: PersonaService = Depends(Provide[PersonaContainer.persona_service]),
) -> PostCreatePersonaResponse | ResponseBase:
    """Create a new persona.

    Args:
        response: FastAPI response object used to override the status code on errors.
        request_data: Validated persona creation payload.
        persona_service: Injected persona service.

    Returns:
        Created persona entity wrapped in a success response, or an error response.
    """
    try:
        new_persona = await persona_service.create_persona(request_data)
    except PersonaCreationFailed as exc:
        _logger.error("Persona creation failed: %s", exc)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Persona creation failed: {exc}", status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during persona creation")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PostCreatePersonaResponse(msg=new_persona, status=StatusType.SUCCESS)


@router.get("/count", response_model=GetCountPersonaResponse, status_code=status.HTTP_200_OK)
@inject
async def count_personas(
    response: Response,
    persona_service: PersonaService = Depends(Provide[PersonaContainer.persona_service]),
) -> GetCountPersonaResponse | ResponseBase:
    """Get total count of personas.

    Args:
        response: FastAPI response object used to override the status code on errors.
        persona_service: Injected persona service.

    Returns:
        Integer count wrapped in a success response, or an error response.
    """
    try:
        count = await persona_service.count_personas()
    except Exception as exc:
        _logger.exception("Unexpected error during persona count")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetCountPersonaResponse(msg=count, status=StatusType.SUCCESS)


@router.get("/", response_model=GetPersonasResponse, status_code=status.HTTP_200_OK)
@inject
async def get_personas(
    response: Response,
    pagination: Annotated[GetPersonasRequest, Query()],
    persona_service: PersonaService = Depends(Provide[PersonaContainer.persona_service]),
) -> GetPersonasResponse | ResponseBase:
    """Get a paginated list of personas.

    Args:
        response: FastAPI response object used to override the status code on errors.
        params: Pagination query parameters (limit, offset).
        persona_service: Injected persona service.

    Returns:
        List of persona entities wrapped in a success response, or an error response.
    """
    try:
        personas = await persona_service.get_personas(limit=pagination.limit, offset=pagination.offset)
    except Exception as exc:
        _logger.exception("Unexpected error during personas retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetPersonasResponse(msg=personas, status=StatusType.SUCCESS)


@router.get("/{persona_id}", response_model=GetPersonaResponse, status_code=status.HTTP_200_OK)
@inject
async def get_persona(
    response: Response,
    persona_id: uuid.UUID,
    persona_service: PersonaService = Depends(Provide[PersonaContainer.persona_service]),
) -> GetPersonaResponse | ResponseBase:
    """Get a single persona by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        persona_id: UUID of the persona to retrieve.
        persona_service: Injected persona service.

    Returns:
        Persona entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        persona = await persona_service.get_persona(persona_id)
    except PersonaNotFound as exc:
        _logger.warning("Persona not found: %s", persona_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during persona retrieval")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return GetPersonaResponse(msg=persona, status=StatusType.SUCCESS)


@router.put("/{persona_id}", response_model=PutUpdatePersonaResponse, status_code=status.HTTP_200_OK)
@inject
async def update_persona(
    response: Response,
    persona_id: uuid.UUID,
    request_data: PutUpdatePersonaRequest,
    persona_service: PersonaService = Depends(Provide[PersonaContainer.persona_service]),
) -> PutUpdatePersonaResponse | ResponseBase:
    """Update a persona by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        persona_id: UUID of the persona to update.
        request_data: Validated partial update payload.
        persona_service: Injected persona service.

    Returns:
        Updated persona entity wrapped in a success response, or a 404/500 error response.
    """
    try:
        updated_persona = await persona_service.update_persona(
            persona_id=persona_id,
            update_persona_data=request_data,
        )
    except PersonaNotFound as exc:
        _logger.warning("Persona not found for update: %s", persona_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during persona update")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return PutUpdatePersonaResponse(msg=updated_persona, status=StatusType.SUCCESS)


@router.delete("/{persona_id}", response_model=DeletePersonaResponse, status_code=status.HTTP_200_OK)
@inject
async def delete_persona(
    response: Response,
    persona_id: uuid.UUID,
    persona_service: PersonaService = Depends(Provide[PersonaContainer.persona_service]),
) -> DeletePersonaResponse | ResponseBase:
    """Delete a persona by ID.

    Args:
        response: FastAPI response object used to override the status code on errors.
        persona_id: UUID of the persona to delete.
        persona_service: Injected persona service.

    Returns:
        Boolean success flag wrapped in a success response, or a 404/500 error response.
    """
    try:
        await persona_service.delete_persona(persona_id)
    except PersonaNotFound as exc:
        _logger.warning("Persona not found for deletion: %s", persona_id)
        response.status_code = status.HTTP_404_NOT_FOUND
        return ResponseBase(details=str(exc), status=StatusType.ERROR)
    except Exception as exc:
        _logger.exception("Unexpected error during persona deletion")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseBase(details=f"Internal server error: {exc}", status=StatusType.ERROR)

    return DeletePersonaResponse(msg=True, status=StatusType.SUCCESS)
