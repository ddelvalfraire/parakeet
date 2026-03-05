from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.api import (
    CreateIncidentRequest,
    CreateIncidentResponse,
    GenerateRetroResponse,
    GetIncidentResponse,
    ListIncidentsResponse,
    SubmitActionRequest,
    SubmitActionResponse,
)
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _service(db: AsyncSession) -> IncidentService:
    return IncidentService(db)


@router.get("", response_model=ListIncidentsResponse)
async def list_incidents(db: AsyncSession = Depends(get_db)):
    service = _service(db)
    summaries = await service.list_incidents()
    return ListIncidentsResponse(incidents=summaries, total=len(summaries))


@router.get("/{incident_id}", response_model=GetIncidentResponse)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    service = _service(db)
    incident = await service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return GetIncidentResponse(incident=incident)


@router.post("", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(body: CreateIncidentRequest, db: AsyncSession = Depends(get_db)):
    service = _service(db)
    summary = await service.create_incident(body.alert)
    return CreateIncidentResponse(incident=summary)


@router.post("/{incident_id}/action", response_model=SubmitActionResponse)
async def submit_action(
    incident_id: str,
    body: SubmitActionRequest,
    db: AsyncSession = Depends(get_db),
):
    service = _service(db)
    new_status = await service.submit_action(
        incident_id, body.approved_option_id, body.approved_by, body.notes
    )
    if new_status is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return SubmitActionResponse(success=True, incident_status=new_status)


@router.post("/{incident_id}/retro", response_model=GenerateRetroResponse)
async def generate_retro(incident_id: str, db: AsyncSession = Depends(get_db)):
    service = _service(db)
    retro = await service.get_retro(incident_id)
    if retro is None:
        raise HTTPException(status_code=404, detail="Incident or retro not found")
    return GenerateRetroResponse(post_mortem=retro)
