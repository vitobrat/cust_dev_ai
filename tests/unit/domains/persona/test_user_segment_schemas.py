from src.domains.persona.schemas.user_segment_search import (
    FindUserSegmentOutput,
    UserSegment,
)


def test_user_segment_from_find_output_preserves_fields() -> None:
    """Ensure the helper converts a discovery result into a history entry."""

    discovery = FindUserSegmentOutput(
        segment_name='Focused Early Adopters',
        segment_description='Developers needing automated compliance documentation.',
        comments_for_improvement='Highlight industry to avoid being too broad.',
        unifying_problem='Manual compliance slowing release cycles',
        where_to_find='Compliance Slack channels',
    )

    history_entry = UserSegment.from_find_output(discovery)

    assert history_entry.segment_name == discovery.segment_name
    assert history_entry.segment_description == discovery.segment_description
    assert history_entry.unifying_problem == discovery.unifying_problem
    assert history_entry.where_to_find == discovery.where_to_find
    assert history_entry.comments_for_improvement == discovery.comments_for_improvement


def test_segment_info_includes_optional_fields_when_present() -> None:
    """Verify segment_info emits every available data point."""

    segment = UserSegment(
        segment_name='Niche founders',
        segment_description='Bootstrapped founders who never touch marketing.',
        unifying_problem='No reliable channel to reach testers',
        where_to_find='Notion community',
        comments_for_improvement=None,
    )

    info = segment.segment_info

    assert 'Segment Name: Niche founders' in info
    assert 'Description: Bootstrapped founders who never touch marketing.' in info
    assert 'Unifying Problem: No reliable channel to reach testers' in info
    assert 'Where to Find: Notion community' in info
    assert 'Comments for Improvement: None' in info


def test_segment_info_handles_missing_optional_fields() -> None:
    """Ensure segment_info still renders when optional metadata is absent."""

    segment = UserSegment(
        segment_name='Beta engineers',
        segment_description='Engineers looking for automated safety checks.',
    )

    info = segment.segment_info

    assert 'Segment Name: Beta engineers' in info
    assert 'Description: Engineers looking for automated safety checks.' in info
    assert 'Unifying Problem' not in info
    assert 'Where to Find' not in info
    assert 'Comments for Improvement: None' in info
