"""Pipeline service — chains ADK agents to process an incident end-to-end.

Flow:
  alert → triage → investigation → root_cause → remediation (→ awaiting_approval)
  [human approves] → retro → resolved
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.investigation.agent import root_agent as investigation_agent
from app.agents.remediation.agent import (
    create_demo_remediation_agent,
    root_agent as remediation_agent,
)
from app.agents.retro.agent import root_agent as retro_agent
from app.agents.root_cause.agent import root_agent as root_cause_agent
from app.agents.triage.agent import root_agent as triage_agent
from app.models.incident import IncidentRow
from app.models.timeline_event import TimelineEventRow
from app.schemas.domain import IncidentStatus, TimelineEventType
from app.schemas.ws import WSEvent, WSEventType
from app.services.github_service import GitHubService
from app.services.ws_manager import ConnectionManager
from fixtures.demo_scenarios import SCENARIOS

logger = logging.getLogger(__name__)

APP_NAME = "parakeet"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _evt_id() -> str:
    return f"evt-{uuid4().hex[:6]}"


def _extract_tool_calls(events: list) -> list[dict[str, Any]]:
    """Extract tool call names and args from ADK events."""
    calls: list[dict[str, Any]] = []
    for event in events:
        if not event.content or not event.content.parts:
            continue
        for part in event.content.parts:
            fc = part.function_call
            if fc is not None:
                calls.append({"name": fc.name, "args": dict(fc.args)})
    return calls


async def _run_agent(agent: Agent, message: str, session_id: str) -> list[dict[str, Any]]:
    """Run an ADK agent and return its tool calls."""
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    events = []
    async for event in runner.run_async(
        user_id="pipeline",
        session_id=session_id,
        new_message=types.Content(
            parts=[types.Part(text=message)],
            role="user",
        ),
    ):
        events.append(event)
    return _extract_tool_calls(events)


async def _save_event(
    db: AsyncSession,
    incident_id: str,
    stage: str,
    title: str,
    payload: dict[str, Any],
) -> TimelineEventRow:
    row = TimelineEventRow(
        id=_evt_id(),
        incident_id=incident_id,
        timestamp=_now(),
        stage=stage,
        type=TimelineEventType.agent_output.value,
        title=title,
        payload=payload,
    )
    db.add(row)
    return row


async def _update_status(
    db: AsyncSession,
    incident: IncidentRow,
    status: IncidentStatus,
    **extra: str,
) -> None:
    incident.status = status.value
    incident.updated_at = _now()
    for k, v in extra.items():
        setattr(incident, k, v)


async def _broadcast(
    ws: ConnectionManager,
    incident_id: str,
    event_type: WSEventType,
    payload: dict[str, Any],
) -> None:
    try:
        await ws.broadcast(
            incident_id,
            WSEvent(
                type=event_type,
                incident_id=incident_id,
                timestamp=_now(),
                payload=payload,
            ),
        )
    except Exception:
        logger.exception("WS broadcast failed for %s", incident_id)


def _build_alert_message(alert: dict[str, Any]) -> str:
    return (
        f"Alert from {alert['source']}:\n"
        f"Service: {alert['service']}\n"
        f"Environment: {alert['environment']}\n"
        f"Metric: {alert['metric']}\n"
        f"Value: {alert['value']} (threshold: {alert['threshold']})\n"
        f"Message: {alert['message']}"
    )


async def run_triage_to_remediation(
    db: AsyncSession,
    ws: ConnectionManager,
    incident_id: str,
    github: GitHubService | None = None,
) -> None:
    """Run the full agent pipeline from triage through remediation.

    Called as a background task after incident creation.
    Pass *github* for demo incidents that need live GitHub interaction.
    """
    result = await db.execute(
        select(IncidentRow).where(IncidentRow.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        logger.error("Incident %s not found for pipeline", incident_id)
        return

    alert = incident.alert
    session_id = incident_id
    context_parts: list[str] = []

    # --- 1. Triage ---
    try:
        alert_msg = _build_alert_message(alert)
        triage_calls = await _run_agent(triage_agent, alert_msg, session_id)
        triage_data = next(
            (c["args"] for c in triage_calls if c["name"] == "classify_alert"), None
        )

        if triage_data:
            await _update_status(db, incident, IncidentStatus.investigating)
            incident.severity = triage_data.get("severity", incident.severity)
            incident.summary = triage_data.get("summary", incident.summary)
            await _save_event(
                db, incident_id, IncidentStatus.triaging.value,
                "Triage complete", triage_data,
            )
            await db.commit()
            await _broadcast(ws, incident_id, WSEventType.stage_change, {
                "stage": IncidentStatus.investigating.value,
                "triage": triage_data,
            })
            context_parts.append(f"Triage result: {json.dumps(triage_data)}")
        else:
            logger.warning("Triage agent returned no classify_alert call for %s", incident_id)
            context_parts.append(f"Alert: {alert_msg}")

    except Exception:
        logger.exception("Triage failed for %s", incident_id)
        db.add(TimelineEventRow(
            id=_evt_id(),
            incident_id=incident_id,
            timestamp=_now(),
            stage="failed",
            type=TimelineEventType.system_event.value,
            title="Triage agent failed",
            payload={"error": "agent_error"},
        ))
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.error, {"stage": "triage"})
        return

    # --- 2. Investigation ---
    try:
        inv_msg = f"{alert_msg}\n\n{"\n".join(context_parts)}"
        inv_calls = await _run_agent(investigation_agent, inv_msg, session_id)

        log_findings = next(
            (c["args"] for c in inv_calls if c["name"] == "report_log_findings"), None
        )
        affected = [c["args"] for c in inv_calls if c["name"] == "report_affected_service"]
        impact = next(
            (c["args"] for c in inv_calls if c["name"] == "report_impact_summary"), None
        )

        inv_data = {
            "log_findings": log_findings,
            "affected_services": affected,
            "estimated_users_affected": impact.get("estimated_users_affected") if impact else None,
            "revenue_impact_per_minute": impact.get("revenue_impact_per_minute") if impact else None,
        }
        await _update_status(db, incident, IncidentStatus.root_cause)
        await _save_event(
            db, incident_id, IncidentStatus.investigating.value,
            "Investigation complete", inv_data,
        )
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.stage_change, {
            "stage": IncidentStatus.root_cause.value,
            "investigation": inv_data,
        })
        context_parts.append(f"Investigation: {json.dumps(inv_data)}")

    except Exception:
        logger.exception("Investigation failed for %s", incident_id)
        db.add(TimelineEventRow(
            id=_evt_id(),
            incident_id=incident_id,
            timestamp=_now(),
            stage="failed",
            type=TimelineEventType.system_event.value,
            title="Investigation agent failed",
            payload={"error": "agent_error"},
        ))
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.error, {"stage": "investigation"})
        return

    # --- 3. Root cause ---
    try:
        rc_msg = "\n\n".join(context_parts)
        rc_calls = await _run_agent(root_cause_agent, rc_msg, session_id)
        rc_data = next(
            (c["args"] for c in rc_calls if c["name"] == "report_root_cause"), None
        )

        if rc_data:
            await _update_status(db, incident, IncidentStatus.awaiting_approval)
            await _save_event(
                db, incident_id, IncidentStatus.root_cause.value,
                "Root cause identified", rc_data,
            )
            await db.commit()
            await _broadcast(ws, incident_id, WSEventType.stage_change, {
                "stage": IncidentStatus.awaiting_approval.value,
                "root_cause": rc_data,
            })
            context_parts.append(f"Root cause: {json.dumps(rc_data)}")
        else:
            logger.warning("Root cause agent returned no result for %s", incident_id)
            await _broadcast(ws, incident_id, WSEventType.error, {"stage": "root_cause"})
            return

    except Exception:
        logger.exception("Root cause failed for %s", incident_id)
        db.add(TimelineEventRow(
            id=_evt_id(),
            incident_id=incident_id,
            timestamp=_now(),
            stage="failed",
            type=TimelineEventType.system_event.value,
            title="Root cause agent failed",
            payload={"error": "agent_error"},
        ))
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.error, {"stage": "root_cause"})
        return

    # --- 4. Remediation ---
    try:
        scenario = SCENARIOS.get(incident.demo_scenario_id or "")
        if scenario and github:
            # Demo path: agent reads repo, opens PR
            demo_agent = create_demo_remediation_agent(github, scenario, incident_id)
            rem_msg = "\n\n".join(context_parts) + "\n\nService logs:\n" + "\n".join(scenario.logs)
            rem_calls = await _run_agent(demo_agent, rem_msg, session_id)

            pr_data = next(
                (c["args"] for c in rem_calls if c["name"] == "open_fix_pr"), None
            )
            options = [c["args"] for c in rem_calls if c["name"] == "propose_remediation"]
            rem_data: dict[str, Any] = {"options": options}
            if pr_data:
                rem_data["pr"] = pr_data
        else:
            # Standard path: generic remediation options
            rem_msg = "\n\n".join(context_parts)
            rem_calls = await _run_agent(remediation_agent, rem_msg, session_id)
            options = [c["args"] for c in rem_calls if c["name"] == "propose_remediation"]
            rem_data = {"options": options}

        await _save_event(
            db, incident_id, IncidentStatus.awaiting_approval.value,
            "Remediation options proposed", rem_data,
        )
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.awaiting_approval, {
            "remediation": rem_data,
        })

    except Exception:
        logger.exception("Remediation failed for %s", incident_id)
        db.add(TimelineEventRow(
            id=_evt_id(),
            incident_id=incident_id,
            timestamp=_now(),
            stage="failed",
            type=TimelineEventType.system_event.value,
            title="Remediation agent failed",
            payload={"error": "agent_error"},
        ))
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.error, {"stage": "remediation"})


async def run_retro(
    db: AsyncSession,
    ws: ConnectionManager,
    incident_id: str,
) -> dict[str, Any] | None:
    """Run the retro agent on a resolved incident. Returns the post-mortem payload."""
    result = await db.execute(
        select(IncidentRow).where(IncidentRow.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        return None

    # Gather all timeline event payloads as context
    evt_result = await db.execute(
        select(TimelineEventRow)
        .where(TimelineEventRow.incident_id == incident_id)
        .order_by(TimelineEventRow.timestamp)
    )
    events = evt_result.scalars().all()
    context_lines = [
        f"Alert: {json.dumps(incident.alert)}",
        f"Severity: {incident.severity}",
        f"Service: {incident.service}",
    ]
    for evt in events:
        context_lines.append(f"[{evt.stage}] {evt.title}: {json.dumps(evt.payload)}")

    retro_msg = "\n".join(context_lines)
    retro_calls = await _run_agent(retro_agent, retro_msg, incident_id)
    retro_data = next(
        (c["args"] for c in retro_calls if c["name"] == "write_post_mortem"), None
    )

    if retro_data:
        await _update_status(
            db, incident, IncidentStatus.resolved, resolved_at=_now()
        )
        await _save_event(
            db, incident_id, IncidentStatus.resolved.value,
            "Post-mortem generated", retro_data,
        )
        await db.commit()
        await _broadcast(ws, incident_id, WSEventType.resolved, {
            "post_mortem": retro_data,
        })

    return retro_data
