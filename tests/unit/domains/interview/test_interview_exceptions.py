"""Unit tests for interview-domain exception exports."""

from src.domains.interview.exceptions import (
    InterviewError,
    InterviewFinalReportNotFound,
    InterviewNotFound,
    InterviewOrchestratorDraftNodeError,
    InterviewSimulationDraftNodeError,
    PostInterviewUpdateDraftNodeError,
    PreInterviewPreparationDraftNodeError,
)


def test_graph_draft_errors_belong_to_interview_exception_hierarchy() -> None:
    """Graph draft errors should be importable from the domain exceptions module."""
    graph_errors = (
        PreInterviewPreparationDraftNodeError,
        InterviewSimulationDraftNodeError,
        PostInterviewUpdateDraftNodeError,
        InterviewOrchestratorDraftNodeError,
    )

    assert all(issubclass(error_class, InterviewError) for error_class in graph_errors)


def test_final_report_not_found_belongs_to_interview_not_found_hierarchy() -> None:
    """Final report download errors should map cleanly to 404-style errors."""
    assert issubclass(InterviewFinalReportNotFound, InterviewNotFound)
