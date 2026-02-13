from typing import Optional

from pydantic import BaseModel, Field


class InputData(BaseModel):
    """Schema for the raw data required to discover user segments."""

    user_prompt: str = Field(..., description="The user prompt for finding user segments")


class FindUserSegmentOutput(BaseModel):
    """Structured response returned by the model when discovering a new segment."""

    segment_name: str = Field(..., description="Name of the user segment")
    segment_description: str = Field(..., description="Description of the user segment")
    comments_for_improvement: Optional[str] = Field(
        None,
        description="Optional feedback about ways to improve the segment",
    )
    unifying_problem: str = Field(..., description="The unifying problem that defines the user segment")
    where_to_find: str = Field(..., description="Where to find the user segment")


class UserSegment(FindUserSegmentOutput):
    """Representation of a previously discovered segment stored in history."""

    @property
    def segment_info(self) -> str:
        """Return a formatted string summarizing the segment for prompt reuse."""

        parts: list[str] = [
            f"Segment Name: {self.segment_name}",
            f"Description: {self.segment_description}",
        ]
        if self.unifying_problem:
            parts.append(f"Unifying Problem: {self.unifying_problem}")
        if self.where_to_find:
            parts.append(f"Where to Find: {self.where_to_find}")
        parts.append(
            f"Comments for Improvement: {self.comments_for_improvement or 'None'}",
        )
        return ";\n".join(parts)

    @classmethod
    def from_find_output(cls, found: FindUserSegmentOutput) -> "UserSegment":
        """Create a history entry from a freshly discovered segment."""

        return cls(**found.model_dump())


class VerificationSegmentOutput(BaseModel):
    """Structured verification result for a user segment."""

    reasoning: str = Field(..., description="The reasoning behind the verification result")
    is_valid: bool = Field(..., description="Whether the user segment is valid or not")
    comments_for_improvement: Optional[str] = Field(
        None,
        description="Comments for improving the user segment if it is not valid",
    )


class UserSegmentSearchSchema(BaseModel):
    """State schema describing the running user segment search execution."""

    segments_history: list[UserSegment] = Field(
        default_factory=list,
        description="Previously found user segments",
    )
    input_data: InputData
    analysis_result: Optional[str] = Field(
        None,
        description="The result of analysing the user prompt for finding user segments",
    )
    verification_result: Optional[VerificationSegmentOutput] = Field(
        None,
        description="Results produced by the verification step",
    )


class UserSegmentSearchOutputSchema(BaseModel):
    """Final output returned when the graph completes."""

    segment_name: str = Field(..., description="Name of the user segment found")
    segment_description: str = Field(..., description="Description of the user segment found")
