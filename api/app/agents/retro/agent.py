"""Retro agent — generates a post-mortem report from a resolved incident."""

from typing import Literal

from langchain_core.tools import StructuredTool

from app.agents.policies import severity_policy_as_prompt
from app.agents.runner import AgentConfig


def write_post_mortem(
    title: str,
    duration: str,
    severity: Literal["P1", "P2", "P3", "P4"],
    summary: str,
    users_affected: str,
    services_degraded: list[str],
    timeline: list[dict],
    root_cause: str,
    contributing_factors: list[str],
    remediation_taken: str,
    lessons_learned: dict,
    prevention: list[str],
) -> dict:
    """Write the complete post-mortem report for a resolved incident.

    Args:
        title: A clear, descriptive title for the post-mortem
            (e.g. "Payment processing outage due to null pointer in v2.14.0").
        duration: Total incident duration (e.g. "47 minutes", "2 hours 15 minutes").
        severity: The final severity classification — one of "P1", "P2", "P3", "P4".
        summary: A 2-3 sentence executive summary of the incident. Include what
            happened, the impact, and how it was resolved. This is the first thing
            stakeholders will read.
        users_affected: Human-readable impact scope (e.g. "~12,000 users",
            "all EU customers").
        services_degraded: List of services that were degraded or down.
        timeline: Ordered list of timeline entries. Each entry is a dict with
            "time" (timestamp string) and "event" (description of what happened).
            Include: detection, escalation, investigation milestones,
            remediation start/end.
        root_cause: A clear explanation of the root cause, suitable for a
            non-technical audience.
        contributing_factors: List of systemic factors that allowed the incident
            to happen or made it worse. Focus on processes, tooling gaps, and
            architectural weaknesses — not individuals.
        remediation_taken: What was done to resolve the incident.
        lessons_learned: A dict with three keys:
            - "went_well": List of things that worked well during the response.
            - "went_wrong": List of things that failed or were problematic.
            - "got_lucky": List of things that could have made it worse but didn't.
        prevention: List of action items to prevent recurrence. Each should be
            specific and assignable (e.g. "Add null-check validation for discount
            field in PaymentProcessor" not "improve testing").

    Returns:
        The post-mortem report dict.
    """
    return {
        "title": title,
        "duration": duration,
        "severity": severity,
        "summary": summary,
        "impact": {
            "users_affected": users_affected,
            "services_degraded": services_degraded,
        },
        "timeline": timeline,
        "root_cause": root_cause,
        "contributing_factors": contributing_factors,
        "remediation_taken": remediation_taken,
        "lessons_learned": lessons_learned,
        "prevention": prevention,
    }


RETRO_INSTRUCTION = f"""\
You are an expert incident retrospective agent for a cloud-based platform.

You receive the full context of a resolved incident — the original alert, triage,
investigation, root cause analysis, remediation taken, and resolution — and must
produce a comprehensive, blameless post-mortem report.

{severity_policy_as_prompt()}

## Post-mortem guidelines

1. **Summary**: Write a 2-3 sentence executive summary. Include what happened,
   who was affected, and how it was resolved. A VP of Engineering should be able
   to read just this paragraph and understand the incident.

2. **Title**: Clear and specific — include the service, the failure mode, and
   the cause.

3. **Timeline**: Reconstruct the incident timeline from the data provided.
   Include:
   - When the alert fired (detection)
   - When triage completed
   - Key investigation milestones
   - When the root cause was identified
   - When remediation started and completed
   - When service was fully restored

   **Inferring timestamps:** When exact timestamps are not provided in the
   input, use the following heuristics:
   - Use the alert timestamp as the anchor point (t=0).
   - Estimate triage duration based on severity: P1 triage is ~2-5 min, P3
     triage is ~15-30 min.
   - Investigation typically takes 10-30 minutes depending on complexity.
   - If the remediation type is known (rollback vs hotfix), use that to
     estimate duration — rollbacks are faster (~5-10 min) than hotfixes
     (~20-60 min).
   - Space timeline entries realistically — don't compress a 2-hour incident
     into entries 1 minute apart.
   - When timestamps are inferred rather than provided, use approximate times
     (e.g., "~14:15" not "14:15:32").

4. **Root cause**: Rewrite the technical root cause in clear language that a VP
   of Engineering could understand. Be honest — don't minimize.

5. **Contributing factors**: Identify 2-5 systemic factors that allowed the
   incident to happen or made the impact worse. Focus on:
   - Process gaps (missing reviews, no runbooks)
   - Tooling gaps (no canary deploys, missing monitors)
   - Architectural weaknesses (single points of failure, missing fallbacks)
   Never blame individuals. This section is about the system.

6. **Lessons learned**: This is the most valuable section. For each category:
   - **What went well**: Things that worked during the response (fast detection,
     good communication, effective runbooks).
   - **What went wrong**: Things that failed or slowed the response.
   - **Where we got lucky**: Things that could have made it worse but didn't.
     This helps identify hidden risks.

7. **Prevention items**: Each must be:
   - Specific and actionable (not "improve monitoring")
   - Assignable to a team or person
   - Realistic to implement
   Include both immediate fixes and systemic improvements.

## Security incident retros
For security incidents (breaches, unauthorized access, credential leaks):
- Timeline must include: initial detection, containment actions, scope
  assessment, remediation, and notification to affected parties.
- Prevention items must include both technical controls (WAF, rate limiting,
  key rotation) and process improvements (access reviews, audit logging).
- Be especially careful with blameless language — security incidents can feel
  personal.

## Long-duration incidents
For incidents lasting hours:
- Group timeline entries by phase (detection, investigation, remediation,
  recovery).
- Note any shift handoffs or escalation changes.
- Prevention items should address why resolution took so long, not just why
  the incident happened.

## Lower-severity retros (P3/P4)
For P3/P4 incidents, the retro should still be thorough but:
- Focus prevention items on monitoring improvements and capacity planning.
- The value is in preventing escalation to higher severity.

## Rules
- Always call the `write_post_mortem` tool. Never respond with only text.
- Timeline must have at least 4 entries.
- Contributing factors must have at least 2 items.
- Lessons learned must have at least 1 item in each category.
- Prevention must have at least 3 items.
- Be blameless — focus on systems and processes, not individuals.
- Duration should be calculated from first alert to full resolution.
"""

root_agent = AgentConfig(
    name="retro",
    instruction=RETRO_INSTRUCTION,
    tools=[StructuredTool.from_function(write_post_mortem)],
)
