from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class IncidentEmbeddingRow(Base):
    __tablename__ = "incident_embeddings"

    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), primary_key=True)
    service: Mapped[str]
    severity: Mapped[str]
    category: Mapped[str]
    tags: Mapped[list[str]] = mapped_column(JSON)
    root_cause_text: Mapped[str] = mapped_column(Text)
    remediation_summary: Mapped[str] = mapped_column(Text)
    embedding: Mapped[bytes] = mapped_column(LargeBinary)
    resolved_at: Mapped[str]
