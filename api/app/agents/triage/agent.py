"""Triage agent — classifies incoming alerts into severity, category, and tags."""

from langchain_core.tools import StructuredTool

from app.agents.callbacks import patch_empty_tool_descriptions
from app.agents.policies import severity_policy_as_prompt
from app.agents.runner import AgentConfig


def classify_alert(
    severity: str,
    category: str,
    tags: list[str],
    is_duplicate: bool,
    summary: str,
) -> dict:
    """Classify an incoming monitoring alert.

    Analyse the alert and call this tool with your triage classification.

    Args:
        severity: Severity level — one of "P1", "P2", "P3", "P4".
        category: Category label — one of "latency", "error_rate", "availability",
            "resource", "security", "data_integrity", "deployment".
        tags: 3-6 relevant keywords for filtering (service name, environment,
            metric type, suspected root cause).
        is_duplicate: True if this matches an already-active incident on the
            same service with the same failure mode.
        summary: A concise 1-2 sentence summary an on-call engineer can scan
            in seconds. Include impact scope and suspected cause.

    Returns:
        The triage classification dict.
    """
    return {
        "severity": severity,
        "category": category,
        "tags": tags,
        "is_duplicate": is_duplicate,
        "summary": summary,
    }


TRIAGE_INSTRUCTION = f"""\
You are an expert incident triage agent for a cloud-based platform.

When you receive an alert, analyse it carefully and call the `classify_alert` tool
with your assessment.

{severity_policy_as_prompt()}

## Categories
Choose the single most fitting label:
- **latency** — response time / timeout issues
- **error_rate** — elevated error percentages or HTTP 5xx spikes
- **availability** — service or endpoint completely unreachable
- **resource** — CPU, memory, disk, or connection pool exhaustion
- **security** — unauthorised access, credential leaks, anomalous traffic
- **data_integrity** — data corruption, replication lag, inconsistent state, data loss
- **deployment** — failures caused by a recent deploy or config change

When an alert overlaps multiple categories (e.g. a deploy that causes latency),
choose the category that best describes the **user-facing symptom**, not the cause.

## Tags
Include 3-6 relevant keywords: the service name, environment,
metric type, suspected root cause, and any patterns you recognise.

## Duplicate Detection
Flag `is_duplicate: true` when:
- The alert message describes the SAME failure mode on the SAME service
  as a known, already-active incident.
- The symptoms, service, and environment match a currently-open issue.
Do NOT flag as duplicate merely because the same service has alerted before
on a different metric or failure mode.

## Summary
Write a concise 1-2 sentence summary that an on-call engineer can scan in
seconds. Include the impact scope and suspected cause.

## Handling vague or minimal alerts
If the alert lacks detail (e.g. no clear metric value, ambiguous service name),
still classify to the best of your ability. State your assumptions in the summary.
When evidence is insufficient to distinguish between severities, round UP
(e.g. unclear P2 vs P3 → choose P2).

## Rules
- Always call the `classify_alert` tool. Never respond with only text.
- Base severity strictly on the definitions above. When in doubt, round up.
- If the environment is non-production, cap severity at P3 unless there is
  a security concern.
- An alert on a revenue-critical service (payment, checkout, billing) in
  production with ANY degradation should be at least P2.
"""

root_agent = AgentConfig(
    name="triage",
    instruction=TRIAGE_INSTRUCTION,
    tools=[StructuredTool.from_function(classify_alert)],
)
