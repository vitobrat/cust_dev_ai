"""Unit tests for public interview schemas."""

import uuid

import pytest
from pydantic import ValidationError

from src.schemas.interview import CreateInterviewSchema, UpdateInterviewSchema


def test_create_interview_schema_rejects_non_json_final_report() -> None:
    """The final report payload must be JSON-safe before reaching PostgreSQL JSONB."""
    with pytest.raises(ValidationError):
        CreateInterviewSchema(
            user_id=uuid.uuid4(),
            final_report={"invalid": object()},
        )


def test_update_interview_schema_rejects_non_json_final_report() -> None:
    """Partial updates must also reject values that cannot be stored as JSONB."""
    with pytest.raises(ValidationError):
        UpdateInterviewSchema(final_report={"invalid": object()})
