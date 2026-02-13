from src.domains.persona.schemas.user_segment_search import (
    UserSegment,
    UserSegmentSearchSchema,
)


def get_last_segment(state: UserSegmentSearchSchema) -> UserSegment:
    try:
        return state.segments_history[-1]
    except IndexError:
        raise ValueError("Segments history is empty, cannot verify user segment.")
