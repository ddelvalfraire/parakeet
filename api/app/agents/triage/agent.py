"""Triage agent — classifies incoming alerts into severity, category, and tags."""

from google.adk.agents import Agent

from app.agents.policies import severity_policy_as_prompt
from app.config import settings


def classify_alert(
    source: str,
    service: str,
    environment: str,
    metric: str,
    value: str,
    threshold: str,
    message: str,
) -> dict:
    """Classify an incoming monitoring alert.

    Analyse the alert details and return a triage classification with:
    - severity: one of P1, P2, P3, P4
    - category: a short label like "latency", "error_rate", "availability", "resource"
    - tags: a list of relevant tags for filtering
    - is_duplicate: whether this looks like a duplicate of a recent incident
    - summary: a concise enriched summary of the incident

    Args:
        source: The monitoring system that fired the alert (e.g. CloudWatch, Datadog).
        service: Name of the affected service.
        environment: Deployment environment (e.g. production, staging).
        metric: The metric that breached its threshold.
        value: The current metric value.
        threshold: The threshold that was breached.
        message: Human-readable alert message.

    Returns:
        A dict with keys: severity, category, tags, is_duplicate, summary.
    """
    # The LLM will call this tool and populate the return value.
    # This function acts as the structured output schema for the agent.
    return {
        "severity": "P3",
        "category": "uncategorized",
        "tags": [],
        "is_duplicate": False,
        "summary": message,
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

root_agent = Agent(
    name="triage",
    model=settings.agent_model,
    description="Classifies incoming monitoring alerts by severity, category, and tags.",
    instruction=TRIAGE_INSTRUCTION,
    tools=[classify_alert],
)
