"""Raw observability data models.

These represent the signals that agents ingest from external systems
(CloudWatch, Datadog, Kubernetes, APM, health-check monitors).
"""

from pydantic import BaseModel


# ── Application Logs ───────────────────────────────────────────────────────
# CloudWatch Logs, Datadog, kubectl logs


class LogEntry(BaseModel):
    timestamp: str
    level: str  # INFO | WARN | ERROR | FATAL
    service: str
    version: str
    message: str
    trace_id: str | None = None
    metadata: dict = {}


# ── Deployment History ─────────────────────────────────────────────────────
# ArgoCD, GitHub Actions, CI/CD audit log


class DeploymentEvent(BaseModel):
    id: str
    timestamp: str
    service: str
    version_from: str
    version_to: str
    environment: str
    deployed_by: str
    commit_sha: str
    commit_message: str


# ── Kubernetes Events ──────────────────────────────────────────────────────
# kubectl get events, k8s observability layer


class KubernetesEvent(BaseModel):
    timestamp: str
    namespace: str
    kind: str  # Pod | Deployment | ReplicaSet | Node
    name: str
    reason: str  # OOMKilling | BackOff | Unhealthy | Pulled | Started
    message: str
    count: int


# ── APM Traces ─────────────────────────────────────────────────────────────
# Datadog APM, Honeycomb, Jaeger, AWS X-Ray


class SpanEvent(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    service: str
    operation: str  # e.g. POST /checkout, db.query, http.client
    start_time: str
    duration_ms: int
    status: str  # ok | error | timeout
    error_message: str | None = None
    metadata: dict = {}


# ── Health Checks ──────────────────────────────────────────────────────────
# /health, /ready endpoints polled by load balancer or uptime monitor


class HealthCheckResult(BaseModel):
    timestamp: str
    service: str
    endpoint: str  # /health | /ready | /metrics
    status_code: int
    response_time_ms: int
    healthy: bool
    body: dict | None = None
