import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.dependencies import get_db, ws_manager
from app.schemas.api import (
    CreateIncidentRequest,
    CreateIncidentResponse,
    GenerateRetroResponse,
    GetIncidentResponse,
    ListIncidentsResponse,
    MergeFixRequest,
    ResolveManuallyRequest,
    SubmitActionRequest,
    SubmitActionResponse,
)
from app.config import settings
from app.services.incident_service import IncidentService
from app.services.github_service import GitHubService

if settings.mock_agents:
    from app.services.mock_pipeline import run_retro, run_triage_to_remediation
else:
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


@router.post("/{incident_id}/merge-fix", response_model=SubmitActionResponse)
async def merge_fix(
    incident_id: str,
    body: MergeFixRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SubmitActionResponse:
    """Merge the fix PR and transition the incident to resolving."""
    service = _service(db)

    # Find PR number from the remediation timeline event
    incident = await service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    pr_number = None
    for evt in incident.timeline:
        if isinstance(evt.payload, dict) and "pr" in evt.payload:
            pr_info = evt.payload["pr"]
            if isinstance(pr_info, dict):
                pr_number = pr_info.get("pr_number")
                break

    # Merge the PR via GitHub API if available
    github: GitHubService | None = getattr(request.app.state, "github", None)
    if github and pr_number:
        try:
            await github.merge_pr(pr_number)
        except Exception:
            logger.warning("Failed to merge PR #%s — continuing with resolution", pr_number)

    new_status = await service.merge_fix(incident_id, body.approved_by, body.notes)
    if new_status is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Kick off retro in background
    async def _run_retro(iid: str) -> None:
        async with async_session_factory() as retro_db:
            await run_retro(retro_db, ws_manager, iid)

    asyncio.create_task(_run_retro(incident_id)).add_done_callback(_log_task_exception)
    return SubmitActionResponse(success=True, incident_status=new_status)


@router.post("/{incident_id}/resolve-manual", response_model=SubmitActionResponse)
async def resolve_manually(
    incident_id: str,
    body: ResolveManuallyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SubmitActionResponse:
    """Resolve an incident manually with an explanation. Closes any open PR."""
    service = _service(db)

    # Close the PR if one exists
    incident = await service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    github: GitHubService | None = getattr(request.app.state, "github", None)
    if github:
        for evt in incident.timeline:
            if isinstance(evt.payload, dict) and "pr" in evt.payload:
                pr_info = evt.payload["pr"]
                if isinstance(pr_info, dict) and pr_info.get("pr_number"):
                    try:
                        await github.close_pr(pr_info["pr_number"])
                    except Exception:
                        logger.warning("Failed to close PR #%s", pr_info["pr_number"])
                break

    new_status = await service.resolve_manually(
        incident_id, body.explanation, body.approved_by,
    )
    if new_status is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Kick off retro in background
    async def _run_retro(iid: str) -> None:
        async with async_session_factory() as retro_db:
            await run_retro(retro_db, ws_manager, iid)

    asyncio.create_task(_run_retro(incident_id)).add_done_callback(_log_task_exception)
    return SubmitActionResponse(success=True, incident_status=new_status)
