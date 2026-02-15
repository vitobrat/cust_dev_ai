from src.configs.log.logger import get_logger
from src.domains.persona.schemas.generate_persona import (
    DemographicAttributePersona,
    GeneratePersonaSchema,
    GeneratePersonasSchema,
)
from src.domains.persona.schemas.user_segment_search import (
    UserSegment,
    UserSegmentSearchSchema,
)


def get_last_segment(state: UserSegmentSearchSchema) -> UserSegment:
    try:
        return state.segments_history[-1]
    except IndexError:
        raise ValueError("Segments history is empty, cannot verify user segment.")


def get_segment_name(state: GeneratePersonaSchema | GeneratePersonasSchema) -> str:
    try:
        segment_name = state["input_data"].segment_name
    except KeyError as key_error:
        raise ValueError(f"Segment name not found in persona. It is missing in input_data: {key_error}")
    if not segment_name:
        raise ValueError("Segment name not found in persona. It is empty in input_data.")
    return segment_name


def get_segment_description(state: GeneratePersonaSchema | GeneratePersonasSchema) -> str:
    try:
        segment_description = state["input_data"].segment_description
    except KeyError as key_error:
        raise ValueError(f"Segment description not found in persona. It is missing in input_data: {key_error}")
    if not segment_description:
        raise ValueError("Segment description not found in persona. It is empty.")
    return segment_description


def get_demographic_attributes(state: GeneratePersonaSchema) -> DemographicAttributePersona:
    try:
        demographic_attributes = state["demographic_attributes"]
    except KeyError as key_error:
        raise ValueError(f"Demographic attributes not found in persona. It is missing in input_data: {key_error}")
    if not isinstance(demographic_attributes, DemographicAttributePersona):
        raise ValueError("Demographic attributes not found in persona. It is empty.")
    return demographic_attributes


def get_person_count(state: GeneratePersonasSchema) -> int:
    logger = get_logger(f"{__name__}.{get_person_count.__name__}")

    try:
        count = state["input_data"].person_count
    except KeyError:
        count = 1  # Default to 1 if person_count is not provided
        logger.warning("Person count not found in input_data, defaulting to 1.")
    return count
