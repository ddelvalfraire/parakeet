"""Mock observability data for the inc-001 checkout-service outage.

All timestamps align with the seed.py timeline:
  14:19:45  checkout-service@2.4.1 deployed
  14:21:03  First 5xx errors
  14:23:11  CloudWatch alert (94% error rate)
  14:36:22  Rollback completes
  14:38:00  Incident resolved
"""

from app.fixtures.raw_data import (
    DeploymentEvent,
    HealthCheckResult,
    KubernetesEvent,
    LogEntry,
    SpanEvent,
)

# ── Application Logs ───────────────────────────────────────────────────────

LOGS: list[LogEntry] = [
    # Normal traffic before deploy
    LogEntry(
        timestamp="2026-03-04T14:18:00Z",
        level="INFO",
        service="checkout-service",
        version="2.4.0",
        message="POST /checkout completed — orderId=ord-88410",
        trace_id="tr-a001",
        metadata={"order_id": "ord-88410", "latency_ms": 142},
    ),
    LogEntry(
        timestamp="2026-03-04T14:18:45Z",
        level="INFO",
        service="checkout-service",
        version="2.4.0",
        message="POST /checkout completed — orderId=ord-88411",
        trace_id="tr-a002",
        metadata={"order_id": "ord-88411", "latency_ms": 138},
    ),
    # Deploy happens at 14:19:45 — new pods roll out
    LogEntry(
        timestamp="2026-03-04T14:20:10Z",
        level="INFO",
        service="checkout-service",
        version="2.4.1",
        message="Application started on port 8080",
        trace_id=None,
        metadata={"pod": "checkout-6f8b9c-xk2rp"},
    ),
    LogEntry(
        timestamp="2026-03-04T14:20:12Z",
        level="WARN",
        service="checkout-service",
        version="2.4.1",
        message="Environment variable STRIPE_API_KEY is not set",
        trace_id=None,
        metadata={"pod": "checkout-6f8b9c-xk2rp"},
    ),
    # Errors start at 14:21:03
    LogEntry(
        timestamp="2026-03-04T14:21:03Z",
        level="ERROR",
        service="checkout-service",
        version="2.4.1",
        message=(
            "NullPointerException in PaymentGatewayClient.processPayment()"
            " — stripeApiKey is null"
        ),
        trace_id="tr-b001",
        metadata={
            "exception": "java.lang.NullPointerException",
            "stack_trace": "PaymentGatewayClient.java:142",
            "pod": "checkout-6f8b9c-xk2rp",
        },
    ),
    LogEntry(
        timestamp="2026-03-04T14:21:05Z",
        level="ERROR",
        service="checkout-service",
        version="2.4.1",
        message=(
            "NullPointerException in PaymentGatewayClient.processPayment()"
            " — stripeApiKey is null"
        ),
        trace_id="tr-b002",
        metadata={
            "exception": "java.lang.NullPointerException",
            "stack_trace": "PaymentGatewayClient.java:142",
            "pod": "checkout-6f8b9c-m7wnl",
        },
    ),
    LogEntry(
        timestamp="2026-03-04T14:21:18Z",
        level="ERROR",
        service="order-service",
        version="3.1.0",
        message="Upstream checkout-service returned 500 — failing order creation",
        trace_id="tr-b003",
        metadata={"upstream_status": 500, "order_id": "ord-88412"},
    ),
    LogEntry(
        timestamp="2026-03-04T14:22:00Z",
        level="ERROR",
        service="checkout-service",
        version="2.4.1",
        message=(
            "NullPointerException in PaymentGatewayClient.processPayment()"
            " — stripeApiKey is null"
        ),
        trace_id="tr-b010",
        metadata={
            "exception": "java.lang.NullPointerException",
            "stack_trace": "PaymentGatewayClient.java:142",
            "pod": "checkout-6f8b9c-xk2rp",
        },
    ),
    LogEntry(
        timestamp="2026-03-04T14:22:45Z",
        level="FATAL",
        service="checkout-service",
        version="2.4.1",
        message="Health check /ready failing — circuit breaker open",
        trace_id=None,
        metadata={"pod": "checkout-6f8b9c-m7wnl"},
    ),
    # Post-rollback recovery
    LogEntry(
        timestamp="2026-03-04T14:36:30Z",
        level="INFO",
        service="checkout-service",
        version="2.4.0",
        message="Application started on port 8080",
        trace_id=None,
        metadata={"pod": "checkout-5a7e1d-q9ztl"},
    ),
    LogEntry(
        timestamp="2026-03-04T14:37:00Z",
        level="INFO",
        service="checkout-service",
        version="2.4.0",
        message="POST /checkout completed — orderId=ord-88450",
        trace_id="tr-c001",
        metadata={"order_id": "ord-88450", "latency_ms": 155},
    ),
]

# ── Deployment History ─────────────────────────────────────────────────────

DEPLOYMENTS: list[DeploymentEvent] = [
    DeploymentEvent(
        id="deploy-078",
        timestamp="2026-03-04T10:05:00Z",
        service="order-service",
        version_from="3.0.9",
        version_to="3.1.0",
        environment="production",
        deployed_by="ci-bot",
        commit_sha="c3d4e5f",
        commit_message="chore: bump order validation timeout to 30s",
    ),
    DeploymentEvent(
        id="deploy-079",
        timestamp="2026-03-04T14:19:45Z",
        service="checkout-service",
        version_from="2.4.0",
        version_to="2.4.1",
        environment="production",
        deployed_by="ci-bot",
        commit_sha="a1b2c3d",
        commit_message="feat: migrate payment gateway to Stripe v3 SDK",
    ),
    # Rollback deploy
    DeploymentEvent(
        id="deploy-080",
        timestamp="2026-03-04T14:34:15Z",
        service="checkout-service",
        version_from="2.4.1",
        version_to="2.4.0",
        environment="production",
        deployed_by="oncall-engineer",
        commit_sha="f9e8d7c",
        commit_message="revert: rollback checkout-service to 2.4.0",
    ),
]

# ── Kubernetes Events ──────────────────────────────────────────────────────

K8S_EVENTS: list[KubernetesEvent] = [
    KubernetesEvent(
        timestamp="2026-03-04T14:19:46Z",
        namespace="production",
        kind="Deployment",
        name="checkout-service",
        reason="ScalingReplicaSet",
        message="Scaled up replica set checkout-6f8b9c to 3",
        count=1,
    ),
    KubernetesEvent(
        timestamp="2026-03-04T14:20:05Z",
        namespace="production",
        kind="Pod",
        name="checkout-6f8b9c-xk2rp",
        reason="Pulled",
        message="Container image checkout-service:2.4.1 already present on machine",
        count=1,
    ),
    KubernetesEvent(
        timestamp="2026-03-04T14:20:07Z",
        namespace="production",
        kind="Pod",
        name="checkout-6f8b9c-xk2rp",
        reason="Started",
        message="Started container checkout",
        count=1,
    ),
    KubernetesEvent(
        timestamp="2026-03-04T14:21:30Z",
        namespace="production",
        kind="Pod",
        name="checkout-6f8b9c-xk2rp",
        reason="Unhealthy",
        message="Readiness probe failed: HTTP probe failed with status code 503",
        count=3,
    ),
    KubernetesEvent(
        timestamp="2026-03-04T14:22:00Z",
        namespace="production",
        kind="Pod",
        name="checkout-6f8b9c-m7wnl",
        reason="Unhealthy",
        message="Readiness probe failed: HTTP probe failed with status code 503",
        count=5,
    ),
    KubernetesEvent(
        timestamp="2026-03-04T14:23:00Z",
        namespace="production",
        kind="Pod",
        name="checkout-6f8b9c-xk2rp",
        reason="BackOff",
        message="Back-off restarting failed container",
        count=2,
    ),
    # Rollback events
    KubernetesEvent(
        timestamp="2026-03-04T14:34:16Z",
        namespace="production",
        kind="Deployment",
        name="checkout-service",
        reason="ScalingReplicaSet",
        message="Scaled up replica set checkout-5a7e1d to 3",
        count=1,
    ),
    KubernetesEvent(
        timestamp="2026-03-04T14:35:00Z",
        namespace="production",
        kind="Pod",
        name="checkout-5a7e1d-q9ztl",
        reason="Started",
        message="Started container checkout",
        count=1,
    ),
]

# ── APM Traces ─────────────────────────────────────────────────────────────

TRACES: list[SpanEvent] = [
    # Healthy request (pre-deploy)
    SpanEvent(
        trace_id="tr-a001",
        span_id="sp-a001-1",
        parent_span_id=None,
        service="api-gateway",
        operation="POST /checkout",
        start_time="2026-03-04T14:18:00Z",
        duration_ms=145,
        status="ok",
    ),
    SpanEvent(
        trace_id="tr-a001",
        span_id="sp-a001-2",
        parent_span_id="sp-a001-1",
        service="checkout-service",
        operation="processPayment",
        start_time="2026-03-04T14:18:00.020Z",
        duration_ms=98,
        status="ok",
    ),
    SpanEvent(
        trace_id="tr-a001",
        span_id="sp-a001-3",
        parent_span_id="sp-a001-2",
        service="checkout-service",
        operation="http.client stripe.com/v1/charges",
        start_time="2026-03-04T14:18:00.025Z",
        duration_ms=82,
        status="ok",
    ),
    # Failed request (post-deploy)
    SpanEvent(
        trace_id="tr-b001",
        span_id="sp-b001-1",
        parent_span_id=None,
        service="api-gateway",
        operation="POST /checkout",
        start_time="2026-03-04T14:21:03Z",
        duration_ms=12,
        status="error",
        error_message="upstream returned 500",
    ),
    SpanEvent(
        trace_id="tr-b001",
        span_id="sp-b001-2",
        parent_span_id="sp-b001-1",
        service="checkout-service",
        operation="processPayment",
        start_time="2026-03-04T14:21:03.003Z",
        duration_ms=4,
        status="error",
        error_message="NullPointerException: stripeApiKey is null",
    ),
    # Downstream cascade
    SpanEvent(
        trace_id="tr-b003",
        span_id="sp-b003-1",
        parent_span_id=None,
        service="order-service",
        operation="POST /orders",
        start_time="2026-03-04T14:21:18Z",
        duration_ms=38,
        status="error",
        error_message="checkout-service returned 500",
    ),
    SpanEvent(
        trace_id="tr-b003",
        span_id="sp-b003-2",
        parent_span_id="sp-b003-1",
        service="order-service",
        operation="http.client checkout-service/checkout",
        start_time="2026-03-04T14:21:18.005Z",
        duration_ms=22,
        status="error",
        error_message="HTTP 500 Internal Server Error",
    ),
    # Recovered request (post-rollback)
    SpanEvent(
        trace_id="tr-c001",
        span_id="sp-c001-1",
        parent_span_id=None,
        service="api-gateway",
        operation="POST /checkout",
        start_time="2026-03-04T14:37:00Z",
        duration_ms=158,
        status="ok",
    ),
    SpanEvent(
        trace_id="tr-c001",
        span_id="sp-c001-2",
        parent_span_id="sp-c001-1",
        service="checkout-service",
        operation="processPayment",
        start_time="2026-03-04T14:37:00.015Z",
        duration_ms=105,
        status="ok",
    ),
]

# ── Health Checks ──────────────────────────────────────────────────────────

HEALTH_CHECKS: list[HealthCheckResult] = [
    # Healthy (pre-deploy)
    HealthCheckResult(
        timestamp="2026-03-04T14:18:00Z",
        service="checkout-service",
        endpoint="/health",
        status_code=200,
        response_time_ms=8,
        healthy=True,
        body={"status": "ok", "version": "2.4.0"},
    ),
    HealthCheckResult(
        timestamp="2026-03-04T14:18:00Z",
        service="checkout-service",
        endpoint="/ready",
        status_code=200,
        response_time_ms=12,
        healthy=True,
        body={"status": "ready", "checks": {"db": "ok", "stripe": "ok"}},
    ),
    # Unhealthy (post-deploy)
    HealthCheckResult(
        timestamp="2026-03-04T14:21:30Z",
        service="checkout-service",
        endpoint="/health",
        status_code=503,
        response_time_ms=3,
        healthy=False,
        body={"status": "error", "version": "2.4.1"},
    ),
    HealthCheckResult(
        timestamp="2026-03-04T14:21:30Z",
        service="checkout-service",
        endpoint="/ready",
        status_code=503,
        response_time_ms=4,
        healthy=False,
        body={
            "status": "not_ready",
            "checks": {"db": "ok", "stripe": "error — api key missing"},
        },
    ),
    HealthCheckResult(
        timestamp="2026-03-04T14:23:00Z",
        service="checkout-service",
        endpoint="/health",
        status_code=503,
        response_time_ms=2,
        healthy=False,
        body={"status": "error", "version": "2.4.1"},
    ),
    # Healthy neighbors (unaffected)
    HealthCheckResult(
        timestamp="2026-03-04T14:22:00Z",
        service="notification-service",
        endpoint="/health",
        status_code=200,
        response_time_ms=6,
        healthy=True,
        body={"status": "ok", "version": "1.8.2"},
    ),
    # Recovered (post-rollback)
    HealthCheckResult(
        timestamp="2026-03-04T14:36:30Z",
        service="checkout-service",
        endpoint="/health",
        status_code=200,
        response_time_ms=9,
        healthy=True,
        body={"status": "ok", "version": "2.4.0"},
    ),
    HealthCheckResult(
        timestamp="2026-03-04T14:36:30Z",
        service="checkout-service",
        endpoint="/ready",
        status_code=200,
        response_time_ms=14,
        healthy=True,
        body={"status": "ready", "checks": {"db": "ok", "stripe": "ok"}},
    ),
]
