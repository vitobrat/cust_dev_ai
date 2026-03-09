"""Request and response schemas for the Persona API endpoints."""

from src.schemas.api_base import PaginationBase, ResponseBase
from src.schemas.persona import (
    CreatePersonaSchema,
    PersonaRelEntitySchema,
    UpdatePersonasSchema,
)


class PostCreatePersonaRequest(CreatePersonaSchema):
    """Request schema for persona creation."""


class PostCreatePersonaResponse(ResponseBase):
    """Response schema for persona creation."""

    msg: PersonaRelEntitySchema


class GetPersonasRequest(PaginationBase):
    """Pagination query parameters for persona list endpoint."""


class GetPersonaResponse(ResponseBase):
    """Response schema for a single persona retrieval."""

    msg: PersonaRelEntitySchema


class GetPersonasResponse(ResponseBase):
    """Response schema for paginated persona list retrieval."""

    msg: list[PersonaRelEntitySchema]


class GetCountPersonaResponse(ResponseBase):
    """Response schema for persona count."""

    msg: int


class PutUpdatePersonaRequest(UpdatePersonasSchema):
    """Request schema for partial persona update."""


class PutUpdatePersonaResponse(ResponseBase):
    """Response schema for persona update."""

    msg: PersonaRelEntitySchema


class DeletePersonaResponse(ResponseBase):
    """Response schema for persona deletion."""

    msg: bool
