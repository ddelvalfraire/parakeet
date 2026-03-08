"""Shared agent tool for retrieving similar past incidents."""

from __future__ import annotations


def get_similar_past_incidents(
    service: str,
    summary: str,
    severity: str,
) -> list[dict]:
    """Search for resolved incidents similar to the current one.

    Call this to check if the platform has seen similar issues before.
    Returns past incidents with their root cause and what remediation
    worked, ordered by relevance. Empty list if no matches found.

    Args:
        service: The service experiencing the incident (e.g. "payment-service").
        summary: A brief description of the current issue being investigated.
        severity: Current severity level — one of "P1", "P2", "P3", "P4".

    Returns:
        List of similar past incidents. Each entry contains:
        incident_id, service, severity, summary, root_cause,
        remediation_taken, resolved_at, and similarity_score (0-1).
    """
    import asyncio

    from app.database import async_session_factory
    from app.services.embedding import get_embedding_service
    from app.services.similar_incidents import SimilarIncidentService

    async def _query():
        async with async_session_factory() as db:
            svc = SimilarIncidentService(db, get_embedding_service())
            results = await svc.find_similar_by_text(
                service=service, summary=summary, severity=severity,
            )
            return [r.model_dump() for r in results]

    # LangChain tool calls run in a thread, so we can use asyncio.run directly.
    return asyncio.run(_query())
