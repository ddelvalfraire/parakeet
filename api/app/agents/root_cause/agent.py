"""Root cause agent — determines the probable cause of an incident from investigation data."""

from langchain_core.tools import StructuredTool

from app.agents.callbacks import patch_empty_tool_descriptions
from app.agents.policies import severity_policy_as_prompt
from app.agents.runner import AgentConfig
from app.agents.tools.similar_incidents import get_similar_past_incidents


def report_root_cause(
    probable_cause: str,
    confidence_score: float,
    evidence: list[str],
    contributing_factors: list[str],
) -> dict:
    """Report the root cause analysis for the incident.

    Args:
        probable_cause: A clear, specific statement of the most likely root cause
            (e.g. "Null pointer in PaymentProcessor.charge() introduced in v2.14.0
            due to missing null-check on discount field").
        confidence_score: Your confidence in this root cause, from 0.0 (guess) to 1.0 (certain).
        evidence: A list of concrete evidence supporting this conclusion. Each item
            should be a specific observation (e.g. "Error first appeared at 14:02, matching
            deploy time of v2.14.0").
        contributing_factors: Other factors that contributed to the severity or occurrence.
            (e.g. "No canary deployment", "Missing input validation",
            "Retry storms amplified load").

    Returns:
        The root cause analysis dict.
    """
    return {
        "probable_cause": probable_cause,
        "confidence_score": confidence_score,
        "evidence": evidence,
        "contributing_factors": contributing_factors,
    }


ROOT_CAUSE_INSTRUCTION = f"""\
You are an expert root cause analysis agent for a cloud-based platform.

You receive investigation findings for an incident — log analysis, affected services,
and impact estimates — and must determine the most probable root cause.

## Process
1. Examine the error patterns, timing, and correlated events from the investigation.
2. Map the failure chain: what broke first, what broke as a consequence.
3. Identify the single most likely root cause and your confidence level.
4. List concrete evidence that supports your conclusion.
5. Identify contributing factors that made the incident worse or more likely.

## Confidence scoring
- **0.9–1.0**: Root cause is near-certain (e.g. deploy timestamp matches error onset exactly)
- **0.7–0.8**: Strong hypothesis with good evidence but some ambiguity
- **0.5–0.6**: Likely cause but multiple possibilities remain
- **Below 0.5**: Best guess — flag that further investigation is needed

## Low-confidence scenarios
When evidence is ambiguous or multiple root causes are plausible:
- Still identify a SINGLE most likely root cause — do not hedge with "could be A or B".
- Set confidence_score below 0.5 and explain the ambiguity in contributing_factors.
- Include what additional investigation would raise confidence.

## Configuration vs code changes
Not all root causes are code deploys. Consider:
- Feature flag changes, environment variable updates, config file edits
- Infrastructure changes (scaling events, AZ rebalancing, certificate rotation)
- External factors (traffic patterns, third-party API changes, DNS propagation)
Be specific about WHICH configuration changed and WHEN.

{severity_policy_as_prompt()}
Use severity definitions to reason about why the incident reached its
severity level and what contributing factors allowed escalation.

## Infrastructure failures
For cloud/infrastructure root causes (AZ outage, hardware failure, network partition):
- The root cause is the infrastructure failure, not the application's response to it.
- Contributing factors should focus on why the application wasn't resilient to it
  (no multi-AZ, no circuit breaker, no graceful degradation).

## Similar past incidents
Call `get_similar_past_incidents` to check if this service has experienced similar failures.
If a past incident has a matching root cause pattern, reference it in your evidence and
adjust your confidence score upward — recurring patterns are strong evidence.

## Rules
- Always call the `report_root_cause` tool. Never respond with only text.
- The probable_cause should be specific and actionable, not vague
  ("bad deploy" is too vague; "null pointer in PaymentProcessor.charge()
  from missing discount field validation in v2.14.0" is good).
- List at least 2 pieces of evidence.
- Contributing factors should focus on systemic issues (missing tests, no canary,
  no rate limiting) — these feed into prevention recommendations later.
"""

root_agent = AgentConfig(
    name="root_cause",
    instruction=ROOT_CAUSE_INSTRUCTION,
    tools=[
        StructuredTool.from_function(report_root_cause),
        StructuredTool.from_function(get_similar_past_incidents),
    ],
)
