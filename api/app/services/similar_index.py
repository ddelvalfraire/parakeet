"""Shared helper for indexing resolved incidents into the similarity store."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def index_resolved_incident(
    db: AsyncSession, incident_id: str
) -> None:
    """Index a resolved incident for similar-incident retrieval."""
    try:
        from app.services.embedding import get_embedding_service
        from app.services.similar_incidents import SimilarIncidentService

        svc = SimilarIncidentService(db, get_embedding_service())
        await svc.index_incident(incident_id)
    except Exception:
        logger.exception(
            "Failed to index incident %s for similarity search",
            incident_id,
        )
