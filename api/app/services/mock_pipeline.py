"""Mock pipeline — deterministic agent responses without LLM calls.

Drop-in replacement for pipeline.py. Produces realistic, context-aware
responses based on the alert data so the frontend gets full stage transitions,
WebSocket events, and DB persistence without spending tokens.

Enable via PARAKEET_MOCK_AGENTS=true.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import IncidentRow
from app.models.timeline_event import TimelineEventRow
from app.schemas.domain import IncidentStatus, TimelineEventType
from app.schemas.ws import WSEvent, WSEventType
from app.services.ws_manager import ConnectionManager

logger = logging.getLogger(__name__)

# Simulated delay per stage (seconds) — short enough for dev, long enough to see transitions
STAGE_DELAY = 1.5


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _evt_id() -> str:
    return f"evt-{uuid4().hex[:6]}"


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


# ---------------------------------------------------------------------------
# Mock response generators — produce context-aware data from the alert
# ---------------------------------------------------------------------------


def _mock_triage(alert: dict[str, Any]) -> dict[str, Any]:
    service = alert.get("service", "unknown-service")
    metric = alert.get("metric", "error_rate")
    value = alert.get("value", "N/A")
    env = alert.get("environment", "production")

    # Revenue-critical services in prod get P1
    revenue_services = {"checkout", "payment", "billing", "stripe"}
    is_revenue = any(s in service.lower() for s in revenue_services)

    if env != "production":
        severity = "P3"
    elif is_revenue:
        severity = "P1"
    elif "error" in metric.lower() or "5xx" in metric.lower():
        severity = "P2"
    else:
        severity = "P3"

    category_map = {
        "latency": "latency",
        "p99": "latency",
        "p95": "latency",
        "error": "error_rate",
        "5xx": "error_rate",
        "availability": "availability",
        "cpu": "resource",
        "memory": "resource",
        "disk": "resource",
    }
    category = "error_rate"
    for key, cat in category_map.items():
        if key in metric.lower():
            category = cat
            break

    return {
        "severity": severity,
        "category": category,
        "tags": [service, env, metric, "auto-triaged"],
        "is_duplicate": False,
        "summary": (
            f"{service} {category.replace('_', ' ')} alert in {env}. "
            f"{metric} at {value}. Requires investigation."
        ),
    }


def _mock_investigation(alert: dict[str, Any], triage: dict[str, Any]) -> dict[str, Any]:
    service = alert.get("service", "unknown-service")
    metric = alert.get("metric", "error_rate")
    value = alert.get("value", "N/A")
    ts = alert.get("timestamp", _now())

    log_findings = {
        "error_pattern": f"Exception in {service}.handleRequest()",
        "first_occurrence": ts,
        "frequency": "~120 errors/min",
        "affected_versions": [f"{service}@1.2.1"],
        "last_healthy_version": f"{service}@1.2.0",
        "correlated_event": f"deployment at {ts}",
        "sample_stack_trace": f"{service}/handler.py:87 -> unexpected None value",
    }

    affected_services = [
        {"service": service, "status": "down", "impact": "primary"},
        {"service": "api-gateway", "status": "degraded", "impact": "downstream"},
    ]

    return {
        "log_findings": log_findings,
        "affected_services": affected_services,
        "estimated_users_affected": "~1,500-3,000 active sessions",
        "revenue_impact_per_minute": "$800" if triage.get("severity") in ("P1", "P2") else None,
    }


def _mock_root_cause(alert: dict[str, Any], _investigation: dict[str, Any]) -> dict[str, Any]:
    service = alert.get("service", "unknown-service")
    return {
        "probable_cause": (
            f"Recent deployment of {service} introduced a configuration error. "
            f"A required environment variable is missing from the new deployment manifest, "
            f"causing null reference exceptions on the critical request path."
        ),
        "confidence_score": 0.88,
        "evidence": [
            f"Error pattern began shortly after latest deployment of {service}",
            f"Previous version of {service} had zero errors in preceding 24 hours",
            "Stack trace points to missing configuration value",
        ],
        "contributing_factors": [
            "No canary deployment — change went straight to 100% traffic",
            "Missing environment variable validation on startup",
            "No automated rollback trigger on error rate spike",
        ],
    }


def _mock_remediation(alert: dict[str, Any], _root_cause: dict[str, Any]) -> list[dict[str, Any]]:
    service = alert.get("service", "unknown-service")
    return [
        {
            "id": "opt-1",
            "title": f"Rollback {service} to previous version",
            "description": f"Revert {service} to last known good version to restore service immediately.",
            "confidence": 0.94,
            "risk_level": "low",
            "estimated_recovery_time": "3-5 minutes",
            "steps": [
                f"kubectl rollout undo deployment/{service}",
                "Verify pod health — wait for all replicas running",
                "Confirm error rate drops below 1%",
                "Notify on-call team of rollback completion",
            ],
        },
        {
            "id": "opt-2",
            "title": "Patch deployment configuration",
            "description": "Add the missing environment variable and trigger a rolling restart.",
            "confidence": 0.76,
            "risk_level": "medium",
            "estimated_recovery_time": "8-12 minutes",
            "steps": [
                f"kubectl set env deployment/{service} MISSING_VAR=<value>",
                "Trigger rolling restart",
                "Monitor error rate for 5 minutes post-restart",
            ],
        },
        {
            "id": "opt-3",
            "title": "Enable feature flag fallback",
            "description": "Toggle off the new code path and fall back to legacy behavior.",
            "confidence": 0.60,
            "risk_level": "medium",
            "estimated_recovery_time": "2 minutes",
            "steps": [
                "Set feature flag NEW_PATH=false in config service",
                "Confirm traffic routing to legacy handler",
                "Monitor legacy path error rate",
            ],
        },
    ]


def _mock_retro(
    incident: IncidentRow, events: list[TimelineEventRow],
) -> dict[str, Any]:
    service = incident.service or "unknown-service"
    severity = incident.severity or "P2"
    created = incident.created_at or _now()

    # Build a realistic timeline from existing events
    timeline = []
    for evt in events:
        timeline.append({"time": evt.timestamp, "event": evt.title})
    timeline.append({"time": _now(), "event": "Incident resolved"})

    # Ensure minimum 4 entries
    if len(timeline) < 4:
        timeline = [
            {"time": created, "event": f"Alert fired for {service}"},
            {"time": created, "event": "Triage complete"},
            {"time": created, "event": "Root cause identified"},
            {"time": _now(), "event": "Incident resolved"},
        ]

    # Gather affected services from investigation events
    services_degraded = []
    for evt in events:
        if evt.payload and "affected_services" in evt.payload:
            for svc in evt.payload["affected_services"]:
                if svc.get("impact") == "downstream":
                    services_degraded.append(svc["service"])
    if not services_degraded:
        services_degraded = ["api-gateway"]

    return {
        "title": f"{severity}: {service} incident — {created[:10]}",
        "duration": "~15-20 minutes",
        "severity": severity,
        "impact": {
            "users_affected": "~1,500-3,000",
            "estimated_revenue_loss": "$12,000" if severity in ("P1", "P2") else None,
            "services_degraded": services_degraded,
        },
        "timeline": timeline,
        "root_cause": (
            f"A configuration error in the latest deployment of {service} "
            f"caused request failures on the critical path."
        ),
        "remediation_taken": f"Rolled back {service} to the previous stable version.",
        "prevention": [
            "Add environment variable validation to deployment startup checks",
            "Enforce canary deployments for critical services",
            "Add pre-deploy config diff check to CI/CD pipeline",
            "Implement automated rollback on error rate threshold breach",
        ],
    }


# ---------------------------------------------------------------------------
# Public API — same signatures as pipeline.py
# ---------------------------------------------------------------------------


async def run_triage_to_remediation(
    db: AsyncSession,
    ws: ConnectionManager,
    incident_id: str,
) -> None:
    """Mock pipeline: triage -> investigation -> root_cause -> remediation."""
    result = await db.execute(
        select(IncidentRow).where(IncidentRow.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        logger.error("Incident %s not found for mock pipeline", incident_id)
        return

    alert = incident.alert

    # --- 1. Triage ---
    await asyncio.sleep(STAGE_DELAY)
    triage_data = _mock_triage(alert)
    await _update_status(db, incident, IncidentStatus.investigating)
    incident.severity = triage_data["severity"]
    incident.summary = triage_data["summary"]
    await _save_event(
        db, incident_id, IncidentStatus.triaging.value,
        "Triage complete", triage_data,
    )
    await db.commit()
    await _broadcast(ws, incident_id, WSEventType.stage_change, {
        "stage": IncidentStatus.investigating.value,
        "triage": triage_data,
    })

    # --- 2. Investigation ---
    await asyncio.sleep(STAGE_DELAY)
    inv_data = _mock_investigation(alert, triage_data)
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

    # --- 3. Root cause ---
    await asyncio.sleep(STAGE_DELAY)
    rc_data = _mock_root_cause(alert, inv_data)
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

    # --- 4. Remediation ---
    await asyncio.sleep(STAGE_DELAY)
    options = _mock_remediation(alert, rc_data)
    rem_data = {"options": options}
    await _save_event(
        db, incident_id, IncidentStatus.awaiting_approval.value,
        "Remediation options proposed", rem_data,
    )
    await db.commit()
    await _broadcast(ws, incident_id, WSEventType.awaiting_approval, {
        "remediation": rem_data,
    })


async def run_retro(
    db: AsyncSession,
    ws: ConnectionManager,
    incident_id: str,
) -> dict[str, Any] | None:
    """Mock retro: generate a deterministic post-mortem."""
    result = await db.execute(
        select(IncidentRow).where(IncidentRow.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        return None

    evt_result = await db.execute(
        select(TimelineEventRow)
        .where(TimelineEventRow.incident_id == incident_id)
        .order_by(TimelineEventRow.timestamp)
    )
    events = list(evt_result.scalars().all())

    await asyncio.sleep(STAGE_DELAY)
    retro_data = _mock_retro(incident, events)

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
