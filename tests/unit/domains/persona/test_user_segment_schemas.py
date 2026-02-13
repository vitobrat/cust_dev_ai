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


def test_user_segment_info_includes_all_sections() -> None:
    """Validate that segment info concatenates every available section."""

    segment = UserSegment(
        segment_name="Automated QA Leads",
        segment_description="Teams automating quality assurance across microservices.",
        unifying_problem="Manual verification delaying deploys",
        where_to_find="QA automation community channels",
        comments_for_improvement="Provide targeted success metrics.",
    )

    expected_parts = [
        "Segment Name: Automated QA Leads",
        "Description: Teams automating quality assurance across microservices.",
        "Unifying Problem: Manual verification delaying deploys",
        "Where to Find: QA automation community channels",
        "Comments for Improvement: Provide targeted success metrics.",
    ]

    assert segment.segment_info == ";\n".join(expected_parts)


def test_user_segment_info_handles_missing_optional_fields() -> None:
    """Ensure segment info omits empty optional sections and defaults comments."""

    segment = UserSegment(
        segment_name="DataOps Leaders",
        segment_description="Leads wanting tighter feedback loops from analytics.",
        unifying_problem="",
        where_to_find="",
        comments_for_improvement=None,
    )

    expected_parts = [
        "Segment Name: DataOps Leaders",
        "Description: Leads wanting tighter feedback loops from analytics.",
        "Comments for Improvement: None",
    ]

    assert segment.segment_info == ";\n".join(expected_parts)
