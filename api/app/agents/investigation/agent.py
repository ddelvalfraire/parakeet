"""Investigation agent — analyses logs, blast radius, and impact from a triage result."""

from typing import Literal

from langchain_core.tools import StructuredTool

from app.agents.policies import severity_policy_as_prompt
from app.agents.runner import AgentConfig
from app.agents.tools.similar_incidents import get_similar_past_incidents


def report_log_findings(
    error_pattern: str,
    first_occurrence: str,
    frequency: str,
    affected_versions: list[str],
    last_healthy_version: str,
    correlated_event: str | None,
    sample_stack_trace: str | None,
) -> dict:
    """Report log analysis findings for the incident.

    Args:
        error_pattern: The primary error pattern found in logs
            (e.g. "NullPointerException in PaymentProcessor.charge").
        first_occurrence: Timestamp of the first occurrence of this error.
        frequency: How often the error is occurring (e.g. "~200/min", "constant").
        affected_versions: List of service versions exhibiting the error.
        last_healthy_version: The last version where this error was not present.
        correlated_event: Any correlated event such as a deploy or config change, or null.
        sample_stack_trace: A representative stack trace snippet, or null.

    Returns:
        The log findings dict.
    """
    return {
        "error_pattern": error_pattern,
        "first_occurrence": first_occurrence,
        "frequency": frequency,
        "affected_versions": affected_versions,
        "last_healthy_version": last_healthy_version,
        "correlated_event": correlated_event,
        "sample_stack_trace": sample_stack_trace,
    }


def report_affected_service(
    service: str,
    status: Literal["down", "degraded", "healthy"],
    impact: Literal["primary", "downstream", "none"],
) -> dict:
    """Report the status of a single affected service.

    Call this once for each service impacted by the incident.

    Args:
        service: Service name (e.g. "payment-service", "api-gateway").
        status: Current status — one of "down", "degraded", "healthy".
        impact: Impact type — one of "primary" (directly affected),
            "downstream" (affected via dependency), "none".

    Returns:
        The affected service dict.
    """
    return {"service": service, "status": status, "impact": impact}


def report_impact_summary(
    estimated_users_affected: str,
) -> dict:
    """Report the overall user impact estimate.

    Args:
        estimated_users_affected: Human-readable estimate (e.g. "~12,000 users", "all EU users").

    Returns:
        The impact summary dict.
    """
    return {
        "estimated_users_affected": estimated_users_affected,
    }


INVESTIGATION_INSTRUCTION = f"""\
You are an expert incident investigation agent for a cloud-based platform.

You receive a triage summary of an incident and must investigate it in depth.
You have three tools — call ALL of them for every investigation:

1. **`report_log_findings`** — Infer what the logs would show for this incident.
   Base every inference on the concrete alert details: service name, metric,
   threshold, and error type.
   - Use correlated events (deploys, config changes) to infer timing and the
     versions involved.
   - When inferring values like frequency or timestamps, state your assumptions
     and use reasonable estimates grounded in the alert data.
   - Do NOT fabricate specific stack traces unless the error pattern strongly
     implies one (e.g. a NullPointerException in a named class).

2. **`report_affected_service`** — Call this ONCE for each service affected.
   Include the primary service and any downstream dependencies. Classify each
   as "down", "degraded", or "healthy" and whether the impact is "primary",
   "downstream", or "none".

3. **`report_impact_summary`** — Estimate user impact with anchored ranges,
   not false-precision single numbers.
   - Estimate user impact relative to the service's typical traffic and the
     scope of degradation (e.g. one AZ, one region, global).
   - Use ranges when uncertain ("5,000–10,000 users" not "7,342 users").
   - If the incident affects a subset (one AZ, one region, one customer tier),
     scale estimates down accordingly rather than assuming full-service impact.

{severity_policy_as_prompt()}

## Security incidents
For security-related incidents (credential leaks, unauthorized access, anomalous traffic):
- In log findings, focus on access patterns, source IPs, affected endpoints,
  and data exposure scope.
- In affected services, include any service whose data or credentials may have been compromised.
- In impact summary, estimate users whose data may have been exposed, not just active users.

## Multi-service cascading failures
When the primary service failure causes downstream degradation:
- Call `report_affected_service` for EACH affected service in the dependency chain.
- Mark the origin service as "primary" and all others as "downstream".
- Trace the cascade: A→B→C, not just A and C.

## Similar past incidents
Before concluding your investigation, call `get_similar_past_incidents` with the service
name and a summary of what you've found so far. If similar incidents exist, incorporate
their root cause and remediation into your findings — this helps the root cause agent
narrow down faster.

## Rules
- Always call all three tool types. Never respond with only text.
- Be specific and quantitative in your findings.
- When you don't have exact data, make reasonable inferences from the alert context
  and state your assumptions.
- Consider upstream and downstream dependencies when mapping affected services.
- For infrastructure failures (AZ outage, cloud provider issues), map all services
  hosted in the affected infrastructure as affected services.
"""

root_agent = AgentConfig(
    name="investigation",
    instruction=INVESTIGATION_INSTRUCTION,
    tools=[
        StructuredTool.from_function(report_log_findings),
        StructuredTool.from_function(report_affected_service),
        StructuredTool.from_function(report_impact_summary),
        get_similar_past_incidents,
    ],
)
