from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import IncidentRow
from app.models.incident_embedding import IncidentEmbeddingRow
from app.models.timeline_event import TimelineEventRow
from app.schemas.similar import SimilarIncident
from app.services.embedding import EmbeddingService


class SimilarIncidentService:
    def __init__(self, db: AsyncSession, embeddings: EmbeddingService) -> None:
        self._db = db
        self._embeddings = embeddings

    async def index_incident(self, incident_id: str) -> None:
        result = await self._db.execute(
            select(IncidentRow).where(IncidentRow.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident is None:
            return

        result = await self._db.execute(
            select(TimelineEventRow)
            .where(TimelineEventRow.incident_id == incident_id)
            .order_by(TimelineEventRow.timestamp)
        )
        events = result.scalars().all()

        category = "uncategorized"
        tags: list[str] = []
        root_cause_text = ""
        remediation_summary = ""

        for event in events:
            payload = event.payload
            if not isinstance(payload, dict):
                continue
            if "category" in payload and category == "uncategorized":
                category = payload["category"]
                tags = payload.get("tags", [])
            if "probable_cause" in payload and not root_cause_text:
                root_cause_text = payload["probable_cause"]
            if "remediation_taken" in payload and not remediation_summary:
                remediation_summary = payload["remediation_taken"]

        embedding_text = f"{incident.summary} {root_cause_text} {remediation_summary}"
        embedding = self._embeddings.encode(embedding_text)

        row = IncidentEmbeddingRow(
            incident_id=incident_id,
            service=incident.service,
            severity=incident.severity,
            category=category,
            tags=tags,
            root_cause_text=root_cause_text,
            remediation_summary=remediation_summary,
            embedding=embedding,
            resolved_at=incident.resolved_at or "",
        )
        await self._db.merge(row)
        await self._db.commit()

    async def find_similar(
        self,
        incident_id: str,
        *,
        max_results: int = 5,
        min_score: float = 0.3,
    ) -> list[SimilarIncident]:
        result = await self._db.execute(
            select(IncidentRow).where(IncidentRow.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident is None:
            return []

        # Build composite text matching what index_incident() stores
        root_cause = ""
        remediation = ""
        evt_result = await self._db.execute(
            select(TimelineEventRow)
            .where(TimelineEventRow.incident_id == incident_id)
            .order_by(TimelineEventRow.timestamp)
        )
        for evt in evt_result.scalars():
            p = evt.payload
            if not isinstance(p, dict):
                continue
            if "probable_cause" in p and not root_cause:
                root_cause = p["probable_cause"]
            if "remediation_taken" in p and not remediation:
                remediation = p["remediation_taken"]

        query_text = (
            f"{incident.summary} {root_cause} {remediation}"
        )
        query_embedding = self._embeddings.encode(query_text)

        result = await self._db.execute(
            select(IncidentEmbeddingRow).where(
                IncidentEmbeddingRow.incident_id != incident_id
            )
        )
        candidates = result.scalars().all()

        scored = self._score_candidates(
            query_embedding, candidates, min_score,
        )
        top = scored[:max_results]
        return await self._build_results(top)

    async def find_similar_by_text(
        self,
        service: str,
        summary: str,
        severity: str,
        *,
        max_results: int = 5,
        min_score: float = 0.3,
    ) -> list[SimilarIncident]:
        query_embedding = self._embeddings.encode(summary)

        result = await self._db.execute(
            select(IncidentEmbeddingRow)
        )
        candidates = result.scalars().all()

        # Boost same-service candidates
        scored = self._score_candidates(
            query_embedding, candidates, min_score,
            boost_service=service,
        )
        top = scored[:max_results]
        return await self._build_results(top)

    def _score_candidates(
        self,
        query_embedding: bytes,
        candidates: list[IncidentEmbeddingRow],
        min_score: float,
        *,
        boost_service: str | None = None,
    ) -> list[tuple[float, IncidentEmbeddingRow]]:
        now = datetime.now(UTC)
        scored: list[tuple[float, IncidentEmbeddingRow]] = []

        for c in candidates:
            sim = self._embeddings.cosine_similarity(
                query_embedding, c.embedding,
            )
            days_since = 365.0
            if c.resolved_at:
                try:
                    resolved_dt = datetime.fromisoformat(
                        c.resolved_at.replace("Z", "+00:00")
                    )
                    days_since = max(
                        0.0,
                        (now - resolved_dt).total_seconds() / 86400,
                    )
                except (ValueError, TypeError):
                    pass
            recency_factor = max(0.0, 1.0 - days_since / 365.0)
            service_boost = (
                0.15 if boost_service and c.service == boost_service
                else 0.0
            )
            score = sim * (1.0 + 0.1 * recency_factor + service_boost)
            if score >= min_score:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    async def _build_results(
        self, scored: list[tuple[float, IncidentEmbeddingRow]]
    ) -> list[SimilarIncident]:
        if not scored:
            return []

        incident_ids = [c.incident_id for _, c in scored]
        result = await self._db.execute(
            select(IncidentRow).where(IncidentRow.id.in_(incident_ids))
        )
        summaries = {row.id: row.summary for row in result.scalars().all()}

        return [
            SimilarIncident(
                incident_id=c.incident_id,
                service=c.service,
                severity=c.severity,
                summary=summaries.get(c.incident_id, c.root_cause_text),
                root_cause=c.root_cause_text,
                remediation_taken=c.remediation_summary,
                resolved_at=c.resolved_at,
                similarity_score=round(score, 4),
            )
            for score, c in scored
        ]
