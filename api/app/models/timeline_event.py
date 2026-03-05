from sqlalchemy import JSON, Column, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from app.models import Base


class TimelineEventRow(Base):
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    timestamp = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    type = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)

    incident = relationship("IncidentRow", back_populates="timeline_events")

    __table_args__ = (
        Index("ix_timeline_events_incident_id_timestamp", "incident_id", "timestamp"),
    )
