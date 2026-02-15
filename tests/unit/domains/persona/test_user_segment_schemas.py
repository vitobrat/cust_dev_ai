from src.domains.persona.schemas.user_segment_search import (
    FindUserSegmentOutput,
    UserSegment,
)


def test_user_segment_from_find_output_preserves_fields() -> None:
    """Ensure the helper converts a discovery result into a history entry."""

    discovery = FindUserSegmentOutput(
        segment_name="Focused Early Adopters",
        segment_description="Developers needing automated compliance documentation.",
        comments_for_improvement="Highlight industry to avoid being too broad.",
        unifying_problem="Manual compliance slowing release cycles",
        where_to_find="Compliance Slack channels",
    )

    history_entry = UserSegment.from_find_output(discovery)

    assert history_entry.segment_name == discovery.segment_name
    assert history_entry.segment_description == discovery.segment_description
    assert history_entry.unifying_problem == discovery.unifying_problem
    assert history_entry.where_to_find == discovery.where_to_find
    assert history_entry.comments_for_improvement == discovery.comments_for_improvement


def test_user_segment_info_includes_all_sections(user_segment_state: UserSegment) -> None:
    """Validate that segment info concatenates every available section."""

    expected_parts = [
        "Segment Name: Automation Architects",
        "Description: Focus on resilient pipelines",
        "Unifying Problem: Manual toil",
        "Where to Find: Infra communities",
        "Comments for Improvement: Share success metrics.",
    ]

    assert user_segment_state.segment_info == ";\n".join(expected_parts)


def test_user_segment_info_handles_missing_optional_fields(user_segment_state: UserSegment) -> None:
    """Ensure segment info omits empty optional sections and defaults comments."""
    user_segment_state.unifying_problem = ""
    user_segment_state.where_to_find = ""

    expected_parts = [
        "Segment Name: Automation Architects",
        "Description: Focus on resilient pipelines",
        "Comments for Improvement: Share success metrics.",
    ]

    assert user_segment_state.segment_info == ";\n".join(expected_parts)
