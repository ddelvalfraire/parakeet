from enum import StrEnum


class IncidentStatus(StrEnum):
    triaging = "triaging"
    investigating = "investigating"
    root_cause = "root_cause"
    remediating = "remediating"
    awaiting_approval = "awaiting_approval"
    resolving = "resolving"
    resolved = "resolved"
    error = "error"
    needs_input = "needs_input"


class Severity(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class TimelineEventType(StrEnum):
    agent_output = "agent_output"
    human_action = "human_action"
    system_event = "system_event"
