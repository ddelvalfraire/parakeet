from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.incident import IncidentRow
from app.models.timeline_event import TimelineEventRow
from app.schemas.agents import PostMortem
from app.schemas.alert import Alert
from app.schemas.domain import IncidentStatus, Severity, TimelineEventType
from app.schemas.incident import Incident, IncidentSummary, TimelineEvent


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_summary(row: IncidentRow) -> IncidentSummary:
    return IncidentSummary(
        id=row.id,
        status=row.status,
        severity=row.severity,
        service=row.service,
        environment=row.environment,
        summary=row.summary,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _event_row_to_schema(row: TimelineEventRow) -> TimelineEvent:
    return TimelineEvent(
        id=row.id,
        incident_id=row.incident_id,
        timestamp=row.timestamp,
        stage=row.stage,
        type=row.type,
        title=row.title,
        payload=row.payload,
    )


def _row_to_incident(row: IncidentRow) -> Incident:
    return Incident(
        id=row.id,
        status=row.status,
        severity=row.severity,
        service=row.service,
        environment=row.environment,
        summary=row.summary,
        alert=row.alert,
        timeline=[_event_row_to_schema(e) for e in row.timeline_events],
        created_at=row.created_at,
        updated_at=row.updated_at,
        resolved_at=row.resolved_at,
    )


class IncidentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_incidents(self) -> list[IncidentSummary]:
        result = await self._db.execute(
            select(IncidentRow).order_by(IncidentRow.created_at.desc())
        )
        return [_row_to_summary(r) for r in result.scalars().all()]

    async def get_incident(self, incident_id: str) -> Incident | None:
        result = await self._db.execute(
            select(IncidentRow)
            .options(joinedload(IncidentRow.timeline_events))
            .where(IncidentRow.id == incident_id)
        )
        row = result.unique().scalar_one_or_none()
        if row is None:
            return None
        return _row_to_incident(row)

    async def create_incident(
        self, alert: Alert, *, demo_scenario_id: str | None = None,
    ) -> IncidentSummary:
        now = _now()
        incident_id = f"inc-{uuid4().hex[:6]}"

        row = IncidentRow(
            id=incident_id,
            status=IncidentStatus.triaging.value,
            severity=Severity.P3.value,
            service=alert.service,
            environment=alert.environment,
            summary=alert.message,
            alert=alert.model_dump(),
            created_at=now,
            updated_at=now,
            resolved_at=None,
            demo_scenario_id=demo_scenario_id,
        )
        self._db.add(row)

        # Create initial triage timeline event
        event = TimelineEventRow(
            id=f"evt-{uuid4().hex[:6]}",
            incident_id=incident_id,
            timestamp=now,
            stage=IncidentStatus.triaging.value,
            type=TimelineEventType.system_event.value,
            title=f"Incident created from {alert.source} alert",
            payload={
                "severity": Severity.P3.value,
                "category": "uncategorized",
                "tags": [],
                "is_duplicate": False,
                "summary": alert.message,
            },
        )
        self._db.add(event)
        await self._db.commit()

        return _row_to_summary(row)

    async def submit_action(
        self, incident_id: str, approved_option_id: str, approved_by: str, notes: str | None
    ) -> IncidentStatus | None:
        result = await self._db.execute(
            select(IncidentRow).where(IncidentRow.id == incident_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        now = _now()
        row.status = IncidentStatus.resolving.value
        row.updated_at = now

        event = TimelineEventRow(
            id=f"evt-{uuid4().hex[:6]}",
            incident_id=incident_id,
            timestamp=now,
            stage=IncidentStatus.resolving.value,
            type=TimelineEventType.human_action.value,
            title=f"Remediation approved by {approved_by}",
            payload={
                "approved_option_id": approved_option_id,
                "approved_by": approved_by,
                "notes": notes,
            },
        )
        self._db.add(event)
        await self._db.commit()

        return IncidentStatus.resolving

    async def merge_fix(
        self, incident_id: str, approved_by: str, notes: str | None,
    ) -> IncidentStatus | None:
        """Approve the code fix PR — transitions incident to resolving."""
        result = await self._db.execute(
            select(IncidentRow).where(IncidentRow.id == incident_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if row.status != IncidentStatus.awaiting_approval.value:
            return IncidentStatus(row.status)

        now = _now()
        row.status = IncidentStatus.resolving.value
        row.updated_at = now

        event = TimelineEventRow(
            id=f"evt-{uuid4().hex[:6]}",
            incident_id=incident_id,
            timestamp=now,
            stage=IncidentStatus.resolving.value,
            type=TimelineEventType.human_action.value,
            title=f"Fix PR merged by {approved_by}",
            payload={
                "approved_option_id": "pr-fix",
                "approved_by": approved_by,
                "notes": notes,
                "action": "merge_pr",
            },
        )
        self._db.add(event)
        await self._db.commit()
        return IncidentStatus.resolving

    async def resolve_manually(
        self, incident_id: str, explanation: str, approved_by: str,
    ) -> IncidentStatus | None:
        """Resolve an incident manually with an explanation."""
        result = await self._db.execute(
            select(IncidentRow).where(IncidentRow.id == incident_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if row.status != IncidentStatus.awaiting_approval.value:
            return IncidentStatus(row.status)

        now = _now()
        row.status = IncidentStatus.resolving.value
        row.updated_at = now

        event = TimelineEventRow(
            id=f"evt-{uuid4().hex[:6]}",
            incident_id=incident_id,
            timestamp=now,
            stage=IncidentStatus.resolving.value,
            type=TimelineEventType.human_action.value,
            title=f"Manually resolved by {approved_by}",
            payload={
                "approved_by": approved_by,
                "explanation": explanation,
                "action": "manual_resolve",
            },
        )
        self._db.add(event)
        await self._db.commit()
        return IncidentStatus.resolving

    async def get_retro(self, incident_id: str) -> PostMortem | None:
        result = await self._db.execute(
            select(IncidentRow)
            .options(joinedload(IncidentRow.timeline_events))
            .where(IncidentRow.id == incident_id)
        )
        row = result.unique().scalar_one_or_none()
        if row is None:
            return None

        # Look for an existing PostMortem in the timeline
        for event in row.timeline_events:
            payload = event.payload
            if isinstance(payload, dict) and "remediation_taken" in payload:
                return PostMortem.model_validate(payload)

        return None
