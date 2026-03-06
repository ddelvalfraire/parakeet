"""Demo management routes — start scenarios, reset demo state."""

import asyncio
import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.dependencies import get_db, ws_manager
from app.schemas.api import (
    DemoScenarioResponse,
    ListScenariosResponse,
    ResetDemoResponse,
    StartDemoRequest,
    StartDemoResponse,
)
from app.services.incident_service import IncidentService
from app.services.github_service import GitHubService
from fixtures.demo_scenarios import SCENARIOS

if settings.mock_agents:
    from app.services.mock_pipeline import run_triage_to_remediation
else:
    from app.services.pipeline import run_triage_to_remediation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


def _log_task_exception(task: asyncio.Task[None]) -> None:
    if not task.cancelled() and task.exception():
        logger.exception("Demo pipeline failed", exc_info=task.exception())


def _get_github(request: Request) -> GitHubService | None:
    return getattr(request.app.state, "github", None)


@router.get("/scenarios", response_model=ListScenariosResponse)
async def list_scenarios() -> ListScenariosResponse:
    scenarios = [
        DemoScenarioResponse(
            id=s.id,
            title=s.title,
            service=s.service,
            severity=s.severity,
            language=s.language,
            description=s.description,
        )
        for s in SCENARIOS.values()
    ]
    return ListScenariosResponse(scenarios=scenarios)


@router.post("/start", response_model=StartDemoResponse, status_code=201)
async def start_demo(
    body: StartDemoRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StartDemoResponse:
    scenario = SCENARIOS.get(body.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {body.scenario_id}")

    from app.schemas.alert import Alert

    alert = Alert(
        **scenario.alert,
        id=f"demo-{uuid4().hex[:8]}",
        timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    service = IncidentService(db)
    summary = await service.create_incident(alert, demo_scenario_id=scenario.id)

    github = _get_github(request)

    async def _run_pipeline(incident_id: str) -> None:
        async with async_session_factory() as pipeline_db:
            await run_triage_to_remediation(pipeline_db, ws_manager, incident_id, github=github)

    asyncio.create_task(_run_pipeline(summary.id)).add_done_callback(_log_task_exception)
    return StartDemoResponse(incident=summary)


@router.post("/reset", response_model=ResetDemoResponse)
async def reset_demo(request: Request) -> ResetDemoResponse:
    github = _get_github(request)

    prs_closed = 0
    branches_deleted = 0

    if github:
        try:
            open_prs = await github.list_open_prs("parakeet-fix/")
            for pr in open_prs:
                try:
                    await github.close_pr(pr["number"])
                    prs_closed += 1
                except Exception:
                    logger.warning("Failed to close PR #%s", pr["number"])
                try:
                    await github.delete_branch(pr["head"])
                    branches_deleted += 1
                except Exception:
                    logger.warning("Failed to delete branch %s", pr["head"])

            if settings.demo_base_sha:
                await github.force_update_branch("main", settings.demo_base_sha)
        except Exception:
            logger.exception("Demo reset encountered errors")

    return ResetDemoResponse(
        success=True,
        prs_closed=prs_closed,
        branches_deleted=branches_deleted,
    )
