from typing import Literal

from pydantic import BaseModel, Field


class LogFindings(BaseModel):
    error_pattern: str
    first_occurrence: str
    frequency: str
    affected_versions: list[str]
    last_healthy_version: str
    correlated_event: str | None
    sample_stack_trace: str | None


class AffectedService(BaseModel):
    service: str
    status: Literal["down", "degraded", "healthy"]
    impact: Literal["primary", "downstream", "none"]


class RemediationOption(BaseModel):
    id: str
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: str
    estimated_recovery_time: str
    steps: list[str]


class PostMortemImpact(BaseModel):
    users_affected: str
    estimated_revenue_loss: str | None
    services_degraded: list[str]


class PostMortemTimelineEntry(BaseModel):
    time: str
    event: str


class TriageResult(BaseModel):
    severity: str
    category: str
    tags: list[str]
    is_duplicate: bool
    summary: str


class InvestigationResult(BaseModel):
    log_findings: LogFindings
    affected_services: list[AffectedService]
    estimated_users_affected: str
    revenue_impact_per_minute: str | None


class RootCauseResult(BaseModel):
    probable_cause: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    contributing_factors: list[str]


class PRInfo(BaseModel):
    pr_number: int
    pr_url: str
    diff: str
    file_path: str
    branch: str


class RemediationResult(BaseModel):
    options: list[RemediationOption]
    pr: PRInfo | None = None


class HumanDecision(BaseModel):
    approved_option_id: str
    approved_by: str
    notes: str | None


class PostMortem(BaseModel):
    title: str
    duration: str
    severity: str
    impact: PostMortemImpact
    timeline: list[PostMortemTimelineEntry]
    root_cause: str
    remediation_taken: str
    prevention: list[str]
