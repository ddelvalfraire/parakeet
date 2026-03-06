from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.incident import IncidentRow  # noqa: E402, F401
from app.models.incident_embedding import IncidentEmbeddingRow  # noqa: E402, F401
from app.models.timeline_event import TimelineEventRow  # noqa: E402, F401
