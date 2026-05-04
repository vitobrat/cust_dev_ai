"""Schemas for delivering generated interview reports."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FinalReportFile:
    """Downloadable final report file."""

    report_content: bytes
    filename: str
    media_type: str
