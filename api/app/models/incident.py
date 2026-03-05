from sqlalchemy import JSON, Column, String, Text
from sqlalchemy.orm import relationship

from app.models import Base


class IncidentRow(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    service = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    alert = Column(JSON, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    resolved_at = Column(String, nullable=True)

    timeline_events = relationship(
        "TimelineEventRow",
        back_populates="incident",
        order_by="TimelineEventRow.timestamp",
        lazy="select",
    )
