from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.timeline_event import TimelineEventRow


class IncidentRow(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[str]
    severity: Mapped[str]
    service: Mapped[str]
    environment: Mapped[str]
    summary: Mapped[str] = mapped_column(Text)
    alert: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[str]
    updated_at: Mapped[str]
    resolved_at: Mapped[str | None]

    timeline_events: Mapped[list[TimelineEventRow]] = relationship(
        back_populates="incident",
        order_by="TimelineEventRow.timestamp",
        lazy="select",
    )
