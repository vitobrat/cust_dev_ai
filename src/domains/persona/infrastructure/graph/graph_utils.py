"""Accessor helpers for extracting fields from LangGraph TypedDict states.

Each function encapsulates safe access to a specific state key, raising
``ValueError`` when a required field is missing or returning a sensible
default for optional ones.
"""

from typing import Optional, Union

from src.configs.log.logger import get_logger
from src.domains.persona.schemas.generate_persona.demographic_persona import (
    DemographicAttributePersona,
)
from src.domains.persona.schemas.generate_persona.state_schemas import (
    GeneratePersonaSchema,
    GeneratePersonasSchema,
)
from src.domains.persona.schemas.user_segment_search import (
    UserSegment,
    UserSegmentSearchSchema,
)

logger = get_logger(__name__)

_PersonaState = Union[GeneratePersonaSchema, GeneratePersonasSchema]


def get_last_segment(state: UserSegmentSearchSchema) -> UserSegment:
    """Return the most recent segment from history.

    Raises:
        ValueError: If ``segments_history`` is empty.
    """
    try:
        return state["segments_history"][-1]
    except (KeyError, IndexError):
        raise ValueError("Segments history is empty, cannot retrieve last segment.")


def get_segment_name(state: _PersonaState) -> str:
    """Extract ``segment_name`` from ``input_data``.

    Raises:
        ValueError: If the field is missing or empty.
    """
    try:
        segment_name = state["input_data"].segment_name
    except (KeyError, AttributeError) as exc:
        raise ValueError(f"Segment name is missing in input_data: {exc}") from exc
    if not segment_name:
        raise ValueError("Segment name is empty in input_data.")
    return segment_name


def get_segment_description(state: _PersonaState) -> str:
    """Extract ``segment_description`` from ``input_data``.

    Raises:
        ValueError: If the field is missing or empty.
    """
    try:
        segment_description = state["input_data"].segment_description
    except (KeyError, AttributeError) as exc:
        raise ValueError(f"Segment description is missing in input_data: {exc}") from exc
    if not segment_description:
        raise ValueError("Segment description is empty in input_data.")
    return segment_description


def get_demographic_attributes(state: GeneratePersonaSchema) -> DemographicAttributePersona:
    """Extract validated ``demographic_attributes`` from state.

    Raises:
        ValueError: If the field is missing or has an unexpected type.
    """
    try:
        demographic_attributes = state["demographic_attributes"]
    except KeyError as exc:
        raise ValueError(f"Demographic attributes are missing in state: {exc}") from exc
    if not isinstance(demographic_attributes, DemographicAttributePersona):
        raise ValueError("Demographic attributes have unexpected type or are None.")
    return demographic_attributes


def get_person_count(state: GeneratePersonasSchema) -> int:
    """Return ``person_count`` from ``input_data``, defaulting to ``1``."""
    try:
        return state["input_data"].person_count
    except (KeyError, AttributeError):
        logger.warning("Person count not found in input_data, defaulting to 1.")
        return 1


def get_verification_result_is_valid(state: UserSegmentSearchSchema) -> Optional[bool]:
    """Return ``is_valid`` flag from the verification result, or ``None``."""
    verification_result = state.get("verification_result")
    if verification_result is None:
        logger.warning("Verification result is missing, treating as not valid.")
        return None
    return verification_result.is_valid


def get_user_prompt(state: UserSegmentSearchSchema) -> str:
    """Extract ``user_prompt`` from ``input_data``.

    Raises:
        ValueError: If the field is missing.
    """
    try:
        return state["input_data"].user_prompt
    except (KeyError, AttributeError) as exc:
        raise ValueError(f"User prompt is missing in input_data: {exc}") from exc


def get_analysis_result(state: UserSegmentSearchSchema) -> Optional[str]:
    """Return ``analysis_result`` from state, or ``None`` if absent."""
    try:
        return state["analysis_result"]
    except KeyError:
        logger.warning("Analysis result is missing in state, defaulting to None.")
        return None


def get_previous_segments(state: UserSegmentSearchSchema) -> str:
    """Join all previous segment summaries into a single string.

    Returns an empty string when ``segments_history`` is absent or empty.
    """
    try:
        segments = state["segments_history"]
    except KeyError:
        logger.warning("Segments history is missing in state, defaulting to empty string.")
        return ""
    return ";\n".join(segment.segment_info for segment in segments)
