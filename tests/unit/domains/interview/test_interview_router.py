"""Unit tests for Interview API route handlers."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi import Response, status

from src.domains.interview.app.requests.router import download_final_report
from src.domains.interview.exceptions import InterviewFinalReportNotFound
from src.domains.interview.schemas.report_storage import FinalReportFile
from src.schemas.api_base import ResponseBase, StatusType


async def test_download_final_report_route_returns_markdown_response() -> None:
    """The final report endpoint should return a downloadable markdown response."""
    interview_id = uuid.uuid4()
    response = Response()
    interview_service = MagicMock()
    interview_service.get_final_report_file = AsyncMock(
        return_value=FinalReportFile(
            report_content=b"# Report",
            filename=f"interview-{interview_id}-final-report.md",
            media_type="text/markdown; charset=utf-8",
        ),
    )

    route_response = await download_final_report(
        response=response,
        interview_id=interview_id,
        interview_service=interview_service,
    )

    assert isinstance(route_response, Response)
    assert route_response.body == b"# Report"
    assert route_response.media_type == "text/markdown; charset=utf-8"
    assert route_response.headers["content-disposition"] == (
        f'attachment; filename="interview-{interview_id}-final-report.md"'
    )


async def test_download_final_report_route_returns_not_found_when_report_is_missing() -> None:
    """Missing final report should produce the common error envelope."""
    response = Response()
    interview_service = MagicMock()
    interview_service.get_final_report_file = AsyncMock(
        side_effect=InterviewFinalReportNotFound("Final report is not available."),
    )

    route_response = await download_final_report(
        response=response,
        interview_id=uuid.uuid4(),
        interview_service=interview_service,
    )

    assert isinstance(route_response, ResponseBase)
    assert route_response.status == StatusType.ERROR
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert route_response.details == "Final report is not available."
