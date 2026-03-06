"""Shared helpers for asyncio background tasks."""

import asyncio
import logging

logger = logging.getLogger(__name__)


def log_task_exception(task: asyncio.Task[None]) -> None:
    """Done-callback that logs unhandled exceptions from background tasks."""
    if not task.cancelled() and task.exception():
        logger.exception("Background task failed", exc_info=task.exception())
