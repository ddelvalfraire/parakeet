from pydantic import BaseModel

from app.schemas.agents import (
    HumanDecision,
    InvestigationResult,
    PostMortem,
    RemediationResult,
    RootCauseResult,
    TriageResult,
)
from app.schemas.alert import Alert
from app.schemas.domain import IncidentStatus, Severity, TimelineEventType

TimelinePayload = (
    TriageResult
    | InvestigationResult
    | RootCauseResult
    | RemediationResult
    | HumanDecision
    | PostMortem
)


class TimelineEvent(BaseModel):
    id: str
    incident_id: str
    timestamp: str
    stage: IncidentStatus
    type: TimelineEventType
    title: str
    payload: TimelinePayload


class IncidentSummary(BaseModel):
    id: str
    status: IncidentStatus
    severity: Severity
    service: str
    environment: str
    summary: str
    created_at: str
    updated_at: str


class Incident(IncidentSummary):
    alert: Alert
    timeline: list[TimelineEvent]
    resolved_at: str | None
