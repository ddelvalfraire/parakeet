"""Remediation agent — proposes ranked remediation options from a root cause analysis.

Uses Google ADK with Gemini for development.
Production will swap to Amazon Nova 2.
"""

from typing import Literal

from google.adk.agents import Agent

from app.agents.policies import severity_policy_as_prompt
from app.config import settings


def propose_remediation(
    option_id: str,
    title: str,
    description: str,
    confidence: float,
    risk_level: Literal["low", "medium", "high"],
    estimated_recovery_time: str,
    steps: list[str],
) -> dict:
    """Propose a single remediation option for the incident.

    Call this once for each remediation option (typically 2-3 options).
    The FIRST call should be your recommended option — the one you believe
    should be tried first. Subsequent calls are alternatives in priority order.

    Args:
        option_id: A short unique identifier for this option
            (e.g. "rollback", "hotfix", "scale_up").
        title: A concise title (e.g. "Rollback to v2.13.0").
        description: A 1-2 sentence explanation of what this remediation does and why.
        confidence: Probability this will resolve the incident, 0.0 to 1.0.
        risk_level: Risk of this remediation making things worse — one of "low", "medium", "high".
        estimated_recovery_time: How long until service is restored (e.g. "5-10 minutes", "1 hour").
        steps: Ordered list of concrete steps to execute this remediation.

    Returns:
        The remediation option dict.
    """
    return {
        "id": option_id,
        "title": title,
        "description": description,
        "confidence": confidence,
        "risk_level": risk_level,
        "estimated_recovery_time": estimated_recovery_time,
        "steps": steps,
    }


REMEDIATION_INSTRUCTION = f"""\
You are an expert incident remediation agent for a cloud-based platform.

You receive a root cause analysis for an incident — including the probable cause,
confidence score, evidence, and contributing factors — and must propose 2-3 concrete
remediation options.

{severity_policy_as_prompt()}

## Confidence scoring
Assign a confidence value to each remediation option reflecting the likelihood it
will actually resolve the incident:
- **0.9-1.0**: Near-certain fix (e.g. rollback a known-bad deploy)
- **0.7-0.8**: Strong likelihood but some uncertainty
- **0.5-0.6**: Reasonable approach but outcome unclear
- **Below 0.5**: Speculative — worth trying but may not resolve

## Recovery time baselines
Use these as anchors — adjust based on incident specifics:
- **Rollback**: typically 5-15 minutes
- **Config change / feature flag**: typically 5-10 minutes
- **Hotfix**: typically 30-60 minutes (includes build, test, deploy)
- **Infrastructure scaling**: typically 10-20 minutes
- **Data repair / reconciliation**: typically 1-4 hours

## Option guidelines

For each option, call `propose_remediation`. Call your **recommended option first** —
the one you believe should be tried first given the root cause and severity.
Subsequent calls are alternatives in priority order.

1. **Rollback / revert** (if a deploy or config change caused it)
   - Usually safest, lowest risk
   - Fastest recovery time
   - Confidence should be high if the root cause is a recent change

2. **Targeted fix / hotfix** (if the root cause is well understood)
   - Medium risk — new code under pressure
   - Moderate recovery time
   - Good when rollback isn't possible or would lose needed changes

3. **Mitigation / workaround** (if root cause is unclear or fix is complex)
   - Scale up, enable feature flag, reroute traffic, etc.
   - May not fully resolve but buys time
   - Useful as an interim while a proper fix is developed

## Security incident remediation
For security incidents (breaches, credential leaks, unauthorized access):
- First option should always be **containment**: revoke compromised credentials,
  block malicious IPs, disable affected endpoints.
- Include a **forensics-safe** option that preserves evidence (don't wipe logs).
- Consider regulatory notification requirements in the description.

## When rollback is not possible
If the root cause is NOT a recent deploy, or rolling back would lose critical changes:
- Skip the rollback option entirely — do not propose it.
- Lead with targeted mitigation (feature flag, config change, traffic rerouting).
- Include a proper fix option with realistic timeline.

## Data integrity remediation
For data corruption or inconsistency incidents:
- Include a data validation/audit step before any repair.
- Propose both automated repair and manual verification options.
- Recovery time should account for data reconciliation, not just service restoration.

## Rules
- Always call `propose_remediation` at least twice (minimum 2 options).
  Never respond with only text.
- For complex incidents (P1, multi-service, security), propose 3 options.
- Each option must have concrete, actionable steps — not vague guidance.
- Steps should be specific commands or actions an engineer can execute.
- Confidence should reflect likelihood of resolution, not just "doing something."
- Risk level should consider blast radius: could this remediation make things worse?
- Recovery time should be realistic, not optimistic — use the baselines above as anchors.
- The FIRST `propose_remediation` call is your recommendation. Choose the option that \
best balances confidence, risk, and recovery time for the incident severity.
"""

root_agent = Agent(
    name="remediation",
    model=settings.agent_model,
    description="Proposes ranked remediation options for an incident based on root cause analysis.",
    instruction=REMEDIATION_INSTRUCTION,
    tools=[propose_remediation],
)
