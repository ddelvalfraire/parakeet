from enum import Enum
from typing import Any

from pydantic import BaseModel


class WSEventType(str, Enum):
    stage_change = "stage_change"
    timeline_append = "timeline_append"
    awaiting_approval = "awaiting_approval"
    resolved = "resolved"
    error = "error"


class WSEvent(BaseModel):
    type: WSEventType
    incident_id: str
    timestamp: str
    payload: dict[str, Any]
