from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base

if TYPE_CHECKING:
    from app.models.incident import IncidentRow


class TimelineEventRow(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"))
    timestamp: Mapped[str]
    stage: Mapped[str]
    type: Mapped[str]
    title: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)

    incident: Mapped[IncidentRow] = relationship(back_populates="timeline_events")

    __table_args__ = (
        Index("ix_timeline_events_incident_id_timestamp", "incident_id", "timestamp"),
    )
