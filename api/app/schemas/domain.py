from enum import Enum


class IncidentStatus(str, Enum):
    triaging = "triaging"
    investigating = "investigating"
    root_cause = "root_cause"
    awaiting_approval = "awaiting_approval"
    resolving = "resolving"
    resolved = "resolved"


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TimelineEventType(str, Enum):
    agent_output = "agent_output"
    human_action = "human_action"
    system_event = "system_event"
