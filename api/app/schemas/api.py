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


# ---------------------------------------------------------------------------
# Demo endpoints
# ---------------------------------------------------------------------------


class DemoScenarioResponse(BaseModel):
    id: str
    title: str
    service: str
    severity: str
    language: str
    description: str


class ListScenariosResponse(BaseModel):
    scenarios: list[DemoScenarioResponse]


class StartDemoRequest(BaseModel):
    scenario_id: str


class StartDemoResponse(BaseModel):
    incident: IncidentSummary


class ResetDemoResponse(BaseModel):
    success: bool
    prs_closed: int
    branches_deleted: int


# ---------------------------------------------------------------------------
# Additional incident actions
# ---------------------------------------------------------------------------


class MergeFixRequest(BaseModel):
    approved_by: str = "On-Call Engineer"
    notes: str | None = None


class ResolveManuallyRequest(BaseModel):
    explanation: str
    approved_by: str = "On-Call Engineer"
