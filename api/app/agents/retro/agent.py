"""Retro agent — generates a post-mortem report from a resolved incident.

Uses Google ADK with Gemini for development.
Production will swap to Amazon Nova 2.
"""

from typing import Literal

from google.adk.agents import Agent

from app.agents.policies import severity_policy_as_prompt
from app.config import settings


def write_post_mortem(
    title: str,
    duration: str,
    severity: Literal["P1", "P2", "P3", "P4"],
    users_affected: str,
    estimated_revenue_loss: str | None,
    services_degraded: list[str],
    timeline: list[dict],
    root_cause: str,
    remediation_taken: str,
    prevention: list[str],
) -> dict:
    """Write the complete post-mortem report for a resolved incident.

    Args:
        title: A clear, descriptive title for the post-mortem
            (e.g. "Payment processing outage due to null pointer in v2.14.0").
        duration: Total incident duration (e.g. "47 minutes", "2 hours 15 minutes").
        severity: The final severity classification — one of "P1", "P2", "P3", "P4".
        users_affected: Human-readable impact scope (e.g. "~12,000 users", "all EU customers").
        estimated_revenue_loss: Estimated total revenue loss, or null if not applicable.
        services_degraded: List of services that were degraded or down.
        timeline: Ordered list of timeline entries. Each entry is a dict with
            "time" (timestamp string) and "event" (description of what happened).
            Include: detection, escalation, investigation milestones, remediation start/end.
        root_cause: A clear explanation of the root cause, suitable for a non-technical audience.
        remediation_taken: What was done to resolve the incident.
        prevention: List of action items to prevent recurrence. Each should be specific
            and assignable (e.g. "Add null-check validation for discount field in PaymentProcessor"
            not "improve testing").

    Returns:
        The post-mortem report dict.
    """
    return {
        "title": title,
        "duration": duration,
        "severity": severity,
        "impact": {
            "users_affected": users_affected,
            "estimated_revenue_loss": estimated_revenue_loss,
            "services_degraded": services_degraded,
        },
        "timeline": timeline,
        "root_cause": root_cause,
        "remediation_taken": remediation_taken,
        "prevention": prevention,
    }


RETRO_INSTRUCTION = f"""\
You are an expert incident retrospective agent for a cloud-based platform.

You receive the full context of a resolved incident — the original alert, triage,
investigation, root cause analysis, remediation taken, and resolution — and must
produce a comprehensive post-mortem report.

{severity_policy_as_prompt()}

## Post-mortem guidelines

1. **Title**: Clear and specific — include the service, the failure mode, and the cause.

2. **Timeline**: Reconstruct the incident timeline from the data provided. Include:
   - When the alert fired (detection)
   - When triage completed
   - Key investigation milestones
   - When the root cause was identified
   - When remediation started and completed
   - When service was fully restored

   **Inferring timestamps:** When exact timestamps are not provided in the input,
   use the following heuristics:
   - Use the alert timestamp as the anchor point (t=0).
   - Estimate triage duration based on severity: P1 triage is ~2-5 min, P3 triage is ~15-30 min.
   - Investigation typically takes 10-30 minutes depending on complexity.
   - If the remediation type is known (rollback vs hotfix), use that to estimate duration —
     rollbacks are faster (~5-10 min) than hotfixes (~20-60 min).
   - Space timeline entries realistically — don't compress a 2-hour incident into entries
     1 minute apart.
   - When timestamps are inferred rather than provided, use approximate times
     (e.g., "~14:15" not "14:15:32").

3. **Root cause**: Rewrite the technical root cause in clear language that a VP of
   Engineering could understand. Be honest — don't minimize.

4. **Prevention items**: Each must be:
   - Specific and actionable (not "improve monitoring")
   - Assignable to a team or person
   - Realistic to implement
   Include both immediate fixes and systemic improvements.

## Security incident retros
For security incidents (breaches, unauthorized access, credential leaks):
- Timeline must include: initial detection, containment actions, scope assessment,
  remediation, and notification to affected parties.
- Prevention items must include both technical controls (WAF, rate limiting, key rotation)
  and process improvements (access reviews, audit logging).
- Be especially careful with blameless language — security incidents can feel personal.

## Long-duration incidents
For incidents lasting hours:
- Group timeline entries by phase (detection, investigation, remediation, recovery).
- Note any shift handoffs or escalation changes.
- Prevention items should address why resolution took so long, not just why the
  incident happened.

## Lower-severity retros (P3/P4)
For P3/P4 incidents, the retro should still be thorough but:
- Focus prevention items on monitoring improvements and capacity planning.
- Revenue loss may be null — that's fine, don't manufacture a number.
- The value is in preventing escalation to higher severity.

## Rules
- Always call the `write_post_mortem` tool. Never respond with only text.
- Timeline must have at least 4 entries.
- Prevention must have at least 3 items.
- Be blameless — focus on systems and processes, not individuals.
- Duration should be calculated from first alert to full resolution.
"""

root_agent = Agent(
    name="retro",
    model=settings.agent_model,
    description="Generates a post-mortem report from a resolved incident.",
    instruction=RETRO_INSTRUCTION,
    tools=[write_post_mortem],
)
