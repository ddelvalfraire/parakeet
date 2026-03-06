from typing import Any

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    id: str
    incident_id: str
    timestamp: str
    stage: str
    type: str
    title: str
    payload: dict[str, Any]


class IncidentSummary(BaseModel):
    id: str
    status: str
    severity: str
    service: str
    environment: str
    summary: str
    created_at: str
    updated_at: str


class Incident(IncidentSummary):
    alert: dict[str, Any]
    timeline: list[TimelineEvent]
    resolved_at: str | None
