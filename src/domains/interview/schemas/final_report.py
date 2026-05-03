"""Structured schemas for the final interview analytics report."""

from pydantic import BaseModel, Field


class CustomerProblemStat(BaseModel):
    """Quantified repeated customer problem found across interviews."""

    problem_name: str = Field(..., min_length=1)
    mention_count: int = Field(..., ge=1)
    affected_persona_count: int = Field(..., ge=1)
    intensity_score: float = Field(..., ge=0, le=1)
    supporting_quotes: list[str] = Field(default_factory=list)


class CustomerContradiction(BaseModel):
    """Contradiction or tension found in respondent evidence."""

    topic: str = Field(..., min_length=1)
    contradiction_summary: str = Field(..., min_length=1)
    evidence_quotes: list[str] = Field(..., min_length=1)
    implication: str = Field(..., min_length=1)


class FinalReportPlanningAnalysis(BaseModel):
    """Initial analysis and writing plan for the final report."""

    report_goal: str = Field(..., min_length=1)
    writing_plan: list[str] = Field(..., min_length=1)
    problem_statistics: list[CustomerProblemStat] = Field(default_factory=list)
    contradictions: list[CustomerContradiction] = Field(default_factory=list)
    evidence_quality_notes: list[str] = Field(default_factory=list)


class FinalReportSection(BaseModel):
    """One generated markdown section of the final report."""

    section_kind: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    markdown_content: str = Field(..., min_length=1)
    evidence_quotes: list[str] = Field(default_factory=list)
    data_points: list[str] = Field(default_factory=list)


class FinalReportCoreSections(BaseModel):
    """All core analytical sections generated in parallel."""

    user_persona_map: FinalReportSection
    pain_points: FinalReportSection
    key_insights: FinalReportSection
    failure_risk_analysis: FinalReportSection
    recommendations: FinalReportSection


class FinalReportOpening(BaseModel):
    """Short introduction for the final report."""

    title: str = Field(..., min_length=1)
    introduction: str = Field(..., min_length=1)
    report_scope: str = Field(..., min_length=1)


class FinalReportConclusion(BaseModel):
    """Closing section with the main takeaways."""

    key_takeaways: list[str] = Field(..., min_length=1)
    conclusion: str = Field(..., min_length=1)


class FinalInterviewReport(BaseModel):
    """Final analytics report produced from all simulated interviews."""

    opening: FinalReportOpening
    planning_analysis: FinalReportPlanningAnalysis
    core_sections: FinalReportCoreSections
    main_body: FinalReportSection
    conclusion: FinalReportConclusion
    markdown_content: str = Field(..., min_length=1)
    source_interview_count: int = Field(..., ge=1)
