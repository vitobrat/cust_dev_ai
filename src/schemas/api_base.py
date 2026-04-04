"""Common Pydantic schemas for API responses.

This module defines lightweight base models that are reused across the
application's public API. They provide a consistent structure for response
payloads and optional identifiers.
"""

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StatusType(Enum):
    SUCCESS = "success"
    ERROR = "error"


class VerboseBase(BaseModel):
    """Base model that includes an identifier.

    Attributes:
        id: uuid primary key.
    """

    id: uuid.UUID


class PaginationBase(BaseModel):
    """Pagination query parameters for list endpoints.

    Attributes:
        limit: Maximum number of items to return (0–100). Defaults to 10.
        offset: Number of items to skip before collecting results. Defaults to 0.
    """

    limit: int = Field(default=10, ge=0, le=100)
    offset: int = Field(default=0, ge=0)


class ResponseBase(BaseModel):
    """Standard schema for API responses.

    The model is deliberately generic – ``msg`` can hold any serialisable
    payload, while ``details`` offers a human‑readable description (in Russian
    as per project conventions). ``status`` is a required literal that
    indicates whether the request succeeded.

    Attributes:
        msg: Primary data of the response; type is unrestricted to allow
            flexible payloads.
        details: Optional additional information, typically a short message
            in Russian.
        status: Literal value ``"success"`` or ``"error"`` describing the
            outcome of the request.
    """

    msg: Any = None
    details: Optional[str] = None
    status: StatusType = Field(..., description="Response status: 'success' or 'error'")
