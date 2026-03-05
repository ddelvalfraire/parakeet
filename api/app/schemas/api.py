from pydantic import BaseModel

from app.schemas.agents import PostMortem
from app.schemas.alert import Alert
from app.schemas.domain import IncidentStatus
from app.schemas.incident import Incident, IncidentSummary


class CreateIncidentRequest(BaseModel):
    alert: Alert


class CreateIncidentResponse(BaseModel):
    incident: IncidentSummary


class ListIncidentsResponse(BaseModel):
    incidents: list[IncidentSummary]
    total: int


class GetIncidentResponse(BaseModel):
    incident: Incident


class SubmitActionRequest(BaseModel):
    approved_option_id: str
    approved_by: str = "On-Call Engineer"
    notes: str | None = None


class SubmitActionResponse(BaseModel):
    success: bool
    incident_status: IncidentStatus


class GenerateRetroResponse(BaseModel):
    post_mortem: PostMortem
