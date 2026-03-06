from __future__ import annotations

from pydantic import BaseModel, Field


class SimilarIncident(BaseModel):
    """A past resolved incident that matches the current one."""
    incident_id: str
    service: str
    severity: str
    summary: str
    root_cause: str
    remediation_taken: str
    resolved_at: str
    similarity_score: float = Field(ge=0.0, le=1.0)


class SimilarIncidentsResponse(BaseModel):
    """API response for the similar incidents endpoint."""
    similar: list[SimilarIncident]
    query_incident_id: str
