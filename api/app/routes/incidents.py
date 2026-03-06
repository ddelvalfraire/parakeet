import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.dependencies import get_db, ws_manager
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
from app.services.pipeline import run_retro, run_triage_to_remediation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _log_task_exception(task: asyncio.Task[None]) -> None:
    if not task.cancelled() and task.exception():
        logger.exception("Pipeline failed", exc_info=task.exception())


def _service(db: AsyncSession) -> IncidentService:
    return IncidentService(db)


@router.get("", response_model=ListIncidentsResponse)
async def list_incidents(db: AsyncSession = Depends(get_db)) -> ListIncidentsResponse:
    service = _service(db)
    summaries = await service.list_incidents()
    return ListIncidentsResponse(incidents=summaries, total=len(summaries))


@router.get("/{incident_id}", response_model=GetIncidentResponse)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)) -> GetIncidentResponse:
    service = _service(db)
    incident = await service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return GetIncidentResponse(incident=incident)


@router.post("", response_model=CreateIncidentResponse, status_code=201)
async def create_incident(
    body: CreateIncidentRequest, db: AsyncSession = Depends(get_db)
) -> CreateIncidentResponse:
    service = _service(db)
    summary = await service.create_incident(body.alert)

    async def _run_pipeline(incident_id: str) -> None:
        async with async_session_factory() as pipeline_db:
            await run_triage_to_remediation(pipeline_db, ws_manager, incident_id)

    asyncio.create_task(_run_pipeline(summary.id)).add_done_callback(_log_task_exception)
    return CreateIncidentResponse(incident=summary)


@router.post("/{incident_id}/action", response_model=SubmitActionResponse)
async def submit_action(
    incident_id: str,
    body: SubmitActionRequest,
    db: AsyncSession = Depends(get_db),
) -> SubmitActionResponse:
    service = _service(db)
    new_status = await service.submit_action(
        incident_id, body.approved_option_id, body.approved_by, body.notes
    )
    if new_status is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return SubmitActionResponse(success=True, incident_status=new_status)


@router.post("/{incident_id}/retro", response_model=GenerateRetroResponse)
async def generate_retro(
    incident_id: str, db: AsyncSession = Depends(get_db)
) -> GenerateRetroResponse:
    service = _service(db)

    # Return existing retro if already generated
    existing = await service.get_retro(incident_id)
    if existing is not None:
        return GenerateRetroResponse(post_mortem=existing)

    # Generate via the retro agent with a fresh session
    async with async_session_factory() as retro_db:
        retro_data = await run_retro(retro_db, ws_manager, incident_id)
    if retro_data is None:
        raise HTTPException(status_code=404, detail="Incident not found or retro generation failed")

    # Re-read from the request session to return the saved result
    retro = await service.get_retro(incident_id)
    if retro is None:
        raise HTTPException(status_code=500, detail="Retro generated but could not be read back")
    return GenerateRetroResponse(post_mortem=retro)
