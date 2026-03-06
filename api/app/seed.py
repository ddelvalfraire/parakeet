"""Seed data — realistic incidents at various pipeline stages.

inc-001: P1 checkout-service  — awaiting_approval (full timeline through remediation)
inc-002: P2 auth-service      — investigating (triage + investigation)
inc-003: P2 recommendations   — resolved (full timeline + post-mortem)
inc-004: P3 email-notification — triaging (just created)
inc-005: P1 payments-service  — resolved (full timeline + post-mortem)
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import IncidentRow
from app.models.timeline_event import TimelineEventRow

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

ALERTS = {
    "inc-001": {
        "id": "alert-001",
        "source": "CloudWatch",
        "service": "checkout-service",
        "environment": "production",
        "metric": "5xx_error_rate",
        "value": "94%",
        "threshold": "5%",
        "message": "checkout-service error rate exceeded threshold",
        "timestamp": "2026-03-04T14:23:11Z",
    },
    "inc-002": {
        "id": "alert-002",
        "source": "Datadog",
        "service": "auth-service",
        "environment": "production",
        "metric": "login_failure_rate",
        "value": "23%",
        "threshold": "5%",
        "message": "auth-service login failure rate spiked to 23%",
        "timestamp": "2026-03-04T13:10:00Z",
    },
    "inc-003": {
        "id": "alert-003",
        "source": "CloudWatch",
        "service": "recommendations-service",
        "environment": "production",
        "metric": "p99_latency_ms",
        "value": "8200",
        "threshold": "2000",
        "message": "recommendations-service p99 latency exceeded 8s",
        "timestamp": "2026-03-04T11:45:00Z",
    },
    "inc-004": {
        "id": "alert-004",
        "source": "PagerDuty",
        "service": "email-notification-service",
        "environment": "production",
        "metric": "queue_depth",
        "value": "45000",
        "threshold": "10000",
        "message": "Email delivery queue backlog growing — 45k pending",
        "timestamp": "2026-03-04T14:30:00Z",
    },
    "inc-005": {
        "id": "alert-005",
        "source": "CloudWatch",
        "service": "payments-service",
        "environment": "production",
        "metric": "webhook_error_rate",
        "value": "78%",
        "threshold": "1%",
        "message": "Stripe webhook handler returning 503s at 78% rate",
        "timestamp": "2026-03-03T22:15:00Z",
    },
    # --- Historical incidents matching demo scenarios ---
    "inc-006": {
        "id": "alert-006",
        "source": "Prometheus",
        "service": "shippingservice",
        "environment": "production",
        "metric": "shipping_cost_variance",
        "value": "0%",
        "threshold": ">5%",
        "message": "Shipping cost anomaly — all orders charged flat rate regardless of weight",
        "timestamp": "2026-02-18T09:30:00Z",
    },
    "inc-007": {
        "id": "alert-007",
        "source": "Datadog",
        "service": "currencyservice",
        "environment": "production",
        "metric": "error_rate_5xx",
        "value": "28%",
        "threshold": "<1%",
        "message": (
            "Currency conversion errors spiking"
            " — unsupported locale codes crashing convert()"
        ),
        "timestamp": "2026-02-25T16:45:00Z",
    },
    "inc-008": {
        "id": "alert-008",
        "source": "Prometheus",
        "service": "recommendationservice",
        "environment": "production",
        "metric": "error_rate_5xx",
        "value": "8%",
        "threshold": "<1%",
        "message": "Recommendation service crashing on empty product catalog edge case",
        "timestamp": "2026-02-10T11:20:00Z",
    },
}

# ---------------------------------------------------------------------------
# Incident summaries
# ---------------------------------------------------------------------------

INCIDENTS = [
    {
        "id": "inc-001",
        "status": "awaiting_approval",
        "severity": "P1",
        "service": "checkout-service",
        "environment": "production",
        "summary": (
            "Checkout service experiencing near-total failure."
            " 94% error rate. Revenue impact immediate."
        ),
        "created_at": "2026-03-04T14:23:11Z",
        "updated_at": "2026-03-04T14:27:30Z",
        "resolved_at": None,
    },
    {
        "id": "inc-002",
        "status": "investigating",
        "severity": "P2",
        "service": "auth-service",
        "environment": "production",
        "summary": "Elevated login failure rate detected. 23% of authentication requests failing.",
        "created_at": "2026-03-04T13:10:00Z",
        "updated_at": "2026-03-04T13:18:30Z",
        "resolved_at": None,
    },
    {
        "id": "inc-003",
        "status": "resolved",
        "severity": "P2",
        "service": "recommendations-service",
        "environment": "production",
        "summary": "Recommendations service latency spike. p99 latency exceeded 8s threshold.",
        "created_at": "2026-03-04T11:45:00Z",
        "updated_at": "2026-03-04T12:32:00Z",
        "resolved_at": "2026-03-04T12:32:00Z",
    },
    {
        "id": "inc-004",
        "status": "triaging",
        "severity": "P3",
        "service": "email-notification-service",
        "environment": "production",
        "summary": "Email delivery queue backlog growing. Processing delay exceeding 15 minutes.",
        "created_at": "2026-03-04T14:30:00Z",
        "updated_at": "2026-03-04T14:30:45Z",
        "resolved_at": None,
    },
    {
        "id": "inc-005",
        "status": "resolved",
        "severity": "P1",
        "service": "payments-service",
        "environment": "production",
        "summary": "Payment processing failures. Stripe webhook handler throwing 503s.",
        "created_at": "2026-03-03T22:15:00Z",
        "updated_at": "2026-03-03T22:47:00Z",
        "resolved_at": "2026-03-03T22:47:00Z",
    },
    # --- Historical incidents matching demo scenarios ---
    {
        "id": "inc-006",
        "status": "resolved",
        "severity": "P2",
        "service": "shippingservice",
        "environment": "production",
        "summary": (
            "Shipping cost calculation returning flat $8.99"
            " for all orders regardless of weight or item count."
        ),
        "created_at": "2026-02-18T09:30:00Z",
        "updated_at": "2026-02-18T10:15:00Z",
        "resolved_at": "2026-02-18T10:15:00Z",
    },
    {
        "id": "inc-007",
        "status": "resolved",
        "severity": "P1",
        "service": "currencyservice",
        "environment": "production",
        "summary": (
            "Currency conversion failures. 28% of requests"
            " crashing with TypeError on unsupported currency codes."
        ),
        "created_at": "2026-02-25T16:45:00Z",
        "updated_at": "2026-02-25T17:22:00Z",
        "resolved_at": "2026-02-25T17:22:00Z",
    },
    {
        "id": "inc-008",
        "status": "resolved",
        "severity": "P2",
        "service": "recommendationservice",
        "environment": "production",
        "summary": (
            "Recommendation service crashing with ValueError"
            " when filtered product list is empty."
        ),
        "created_at": "2026-02-10T11:20:00Z",
        "updated_at": "2026-02-10T11:55:00Z",
        "resolved_at": "2026-02-10T11:55:00Z",
    },
]

# ---------------------------------------------------------------------------
# Timeline events per incident
# ---------------------------------------------------------------------------

TIMELINES: dict[str, list[dict]] = {
    # ── inc-001: awaiting_approval (triage → investigation → root_cause → remediation) ──
    "inc-001": [
        {
            "id": "evt-101", "timestamp": "2026-03-04T14:23:11Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from CloudWatch alert",
            "payload": {
                "severity": "P1", "category": "service_degradation",
                "tags": ["revenue-impacting", "customer-facing", "checkout", "high-error-rate"],
                "is_duplicate": False,
                "summary": "Checkout service experiencing near-total failure. 94% error rate.",
            },
        },
        {
            "id": "evt-102", "timestamp": "2026-03-04T14:24:02Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P1 declared",
            "payload": {
                "severity": "P1", "category": "service_degradation",
                "tags": ["revenue-impacting", "customer-facing", "checkout", "high-error-rate"],
                "is_duplicate": False,
                "summary": "Checkout service near-total failure in production. 94% error rate.",
            },
        },
        {
            "id": "evt-103", "timestamp": "2026-03-04T14:24:45Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — logs and blast radius mapped",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "NullPointerException in"
                        " PaymentGatewayClient.processPayment()"
                    ),
                    "first_occurrence": "2026-03-04T14:21:03Z",
                    "frequency": "~340 errors/min",
                    "affected_versions": ["checkout-service@2.4.1"],
                    "last_healthy_version": "checkout-service@2.4.0",
                    "correlated_event": "deployment at 2026-03-04T14:19:45Z",
                    "sample_stack_trace": (
                        "PaymentGatewayClient.java:142"
                        " → null reference on stripeApiKey"
                    ),
                },
                "affected_services": [
                    {"service": "checkout-service", "status": "down", "impact": "primary"},
                    {"service": "order-service", "status": "degraded", "impact": "downstream"},
                    {"service": "inventory-service", "status": "degraded", "impact": "downstream"},
                    {"service": "notification-service", "status": "healthy", "impact": "none"},
                ],
                "estimated_users_affected": "~4,200 active sessions",
                "revenue_impact_per_minute": "$2,800",
            },
        },
        {
            "id": "evt-104", "timestamp": "2026-03-04T14:26:45Z",
            "stage": "root_cause", "type": "agent_output",
            "title": "Root cause identified — 91% confidence",
            "payload": {
                "probable_cause": (
                    "Deployment of checkout-service@2.4.1 introduced"
                    " a null reference on stripeApiKey. The Stripe"
                    " API key environment variable is absent from"
                    " the new deployment config."
                ),
                "confidence_score": 0.91,
                "evidence": [
                    "Error pattern began 78 seconds after deploy at 14:19:45",
                    "NullPointerException at PaymentGatewayClient.java:142",
                    "checkout-service@2.4.0 had no errors in preceding 48 hours",
                    "stripeApiKey referenced in 2.4.1 changelog under config changes",
                ],
                "contributing_factors": [
                    "No canary deployment — change went straight to 100% traffic",
                    "Missing environment variable validation on startup",
                ],
            },
        },
        {
            "id": "evt-105", "timestamp": "2026-03-04T14:27:30Z",
            "stage": "awaiting_approval", "type": "agent_output",
            "title": "Remediation options ready — awaiting approval",
            "payload": {
                "options": [
                    {
                        "id": "opt-1", "title": "Rollback to v2.4.0",
                        "description": "Revert checkout-service to last known good version.",
                        "confidence": 0.95, "risk_level": "low",
                        "estimated_recovery_time": "3-5 minutes",
                        "steps": [
                            "kubectl rollout undo deployment/checkout-service",
                            "Verify pod health — wait for 3/3 running",
                            "Confirm error rate drops below 1% in CloudWatch",
                            "Notify on-call team of rollback completion",
                        ],
                    },
                    {
                        "id": "opt-2", "title": "Inject missing environment variable",
                        "description": (
                            "Patch deployment config with missing"
                            " stripeApiKey and re-deploy."
                        ),
                        "confidence": 0.78, "risk_level": "medium",
                        "estimated_recovery_time": "8-12 minutes",
                        "steps": [
                            "kubectl set env deployment/checkout-service"
                            " STRIPE_API_KEY=<value>",
                            "Trigger rolling restart",
                            "Monitor error rate for 5 minutes post-restart",
                        ],
                    },
                    {
                        "id": "opt-3", "title": "Feature flag — disable new payment flow",
                        "description": (
                            "Toggle off the v2.4.1 payment path,"
                            " fall back to legacy flow."
                        ),
                        "confidence": 0.61, "risk_level": "medium",
                        "estimated_recovery_time": "2 minutes",
                        "steps": [
                            "Set feature flag CHECKOUT_V2=false in LaunchDarkly",
                            "Confirm traffic routing to legacy payment handler",
                            "Monitor legacy flow error rate",
                        ],
                    },
                ],
            },
        },
    ],

    # ── inc-002: investigating (triage + investigation in progress) ──
    "inc-002": [
        {
            "id": "evt-201", "timestamp": "2026-03-04T13:10:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from Datadog alert",
            "payload": {
                "severity": "P2", "category": "authentication_failure",
                "tags": ["auth", "login", "user-facing"],
                "is_duplicate": False,
                "summary": "Elevated login failure rate. 23% of authentication requests failing.",
            },
        },
        {
            "id": "evt-202", "timestamp": "2026-03-04T13:12:30Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P2 declared",
            "payload": {
                "severity": "P2", "category": "authentication_failure",
                "tags": ["auth", "login", "user-facing", "redis-timeout"],
                "is_duplicate": False,
                "summary": "Auth service login failures at 23%. Redis session store suspected.",
            },
        },
        {
            "id": "evt-203", "timestamp": "2026-03-04T13:18:30Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — Redis connection pool saturated",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "RedisTimeoutException in"
                        " SessionManager.validateToken()"
                    ),
                    "first_occurrence": "2026-03-04T13:08:22Z",
                    "frequency": "~85 errors/min",
                    "affected_versions": ["auth-service@4.2.0"],
                    "last_healthy_version": "auth-service@4.2.0",
                    "correlated_event": (
                        "Redis cluster node rebalance at 13:05:00Z"
                    ),
                    "sample_stack_trace": (
                        "SessionManager.java:89"
                        " → connection pool exhausted"
                    ),
                },
                "affected_services": [
                    {"service": "auth-service", "status": "degraded", "impact": "primary"},
                    {
                        "service": "user-profile-service",
                        "status": "degraded",
                        "impact": "downstream",
                    },
                    {"service": "checkout-service", "status": "healthy", "impact": "none"},
                ],
                "estimated_users_affected": "~1,800 active sessions",
                "revenue_impact_per_minute": "$420",
            },
        },
    ],

    # ── inc-003: resolved (full pipeline + post-mortem) ──
    "inc-003": [
        {
            "id": "evt-301", "timestamp": "2026-03-04T11:45:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from CloudWatch alert",
            "payload": {
                "severity": "P2", "category": "performance_degradation",
                "tags": ["latency", "recommendations", "ml-pipeline"],
                "is_duplicate": False,
                "summary": "Recommendations service p99 latency spike to 8.2s.",
            },
        },
        {
            "id": "evt-302", "timestamp": "2026-03-04T11:48:00Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P2 declared",
            "payload": {
                "severity": "P2", "category": "performance_degradation",
                "tags": ["latency", "recommendations", "ml-pipeline", "cache-miss"],
                "is_duplicate": False,
                "summary": "Recommendations service latency spike. Cache layer suspected.",
            },
        },
        {
            "id": "evt-303", "timestamp": "2026-03-04T11:55:00Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — cache invalidation storm",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "CacheMissException"
                        " — model cache expired for all segments"
                    ),
                    "first_occurrence": "2026-03-04T11:42:15Z",
                    "frequency": "~200 cache misses/min",
                    "affected_versions": ["recommendations-service@3.1.2"],
                    "last_healthy_version": "recommendations-service@3.1.2",
                    "correlated_event": (
                        "ML model retrain job completed at 11:40:00Z"
                    ),
                    "sample_stack_trace": (
                        "ModelCache.java:67"
                        " → cache key expired, fetching from S3"
                    ),
                },
                "affected_services": [
                    {
                        "service": "recommendations-service",
                        "status": "degraded",
                        "impact": "primary",
                    },
                    {
                        "service": "product-page-service",
                        "status": "degraded",
                        "impact": "downstream",
                    },
                ],
                "estimated_users_affected": "~6,000 browsing sessions",
                "revenue_impact_per_minute": "$180",
            },
        },
        {
            "id": "evt-304", "timestamp": "2026-03-04T12:02:00Z",
            "stage": "root_cause", "type": "agent_output",
            "title": "Root cause identified — 88% confidence",
            "payload": {
                "probable_cause": (
                    "ML model retrain job invalidated the entire"
                    " model cache simultaneously. All recommendation"
                    " requests fell through to cold S3 fetches, causing"
                    " p99 latency to spike from 200ms to 8.2s."
                ),
                "confidence_score": 0.88,
                "evidence": [
                    "Cache miss rate: 2% to 98% at 11:42:15Z",
                    "ML retrain job completed at 11:40:00Z with new version",
                    "S3 GetObject latency averaged 4.2s during the spike",
                    "No code deployment — same version running before and after",
                ],
                "contributing_factors": [
                    "Model cache uses a single TTL for all segments"
                    " — no staggered expiry",
                    "No cache warming step after model retrain",
                ],
            },
        },
        {
            "id": "evt-305", "timestamp": "2026-03-04T12:05:00Z",
            "stage": "awaiting_approval", "type": "agent_output",
            "title": "Remediation options ready — awaiting approval",
            "payload": {
                "options": [
                    {
                        "id": "opt-1", "title": "Trigger cache warm-up job",
                        "description": (
                            "Pre-populate model cache from S3"
                            " for all segments."
                        ),
                        "confidence": 0.92, "risk_level": "low",
                        "estimated_recovery_time": "5-8 minutes",
                        "steps": [
                            "Run cache-warm CLI: ./warm-cache --all-segments",
                            "Monitor cache hit rate in CloudWatch",
                            "Confirm p99 latency drops below 500ms",
                        ],
                    },
                    {
                        "id": "opt-2", "title": "Revert to previous model version",
                        "description": "Roll back ML model to pre-retrain version.",
                        "confidence": 0.75, "risk_level": "medium",
                        "estimated_recovery_time": "10-15 minutes",
                        "steps": [
                            "Update model config to point to previous S3 artifact",
                            "Invalidate cache and let it repopulate",
                            "Verify recommendation quality with smoke tests",
                        ],
                    },
                ],
            },
        },
        {
            "id": "evt-306", "timestamp": "2026-03-04T12:08:00Z",
            "stage": "resolving", "type": "human_action",
            "title": "Remediation approved by on-call engineer",
            "payload": {
                "approved_option_id": "opt-1",
                "approved_by": "On-Call Engineer",
                "notes": "Cache warm-up is safest. Let's go.",
            },
        },
        {
            "id": "evt-307", "timestamp": "2026-03-04T12:32:00Z",
            "stage": "resolved", "type": "agent_output",
            "title": "Post-mortem generated",
            "payload": {
                "title": "P2: Recommendations Latency Spike — Cache Invalidation Storm",
                "duration": "11:42 - 12:20 UTC (38 minutes)",
                "severity": "P2",
                "impact": {
                    "users_affected": "~6,000",
                    "estimated_revenue_loss": "$6,840",
                    "services_degraded": ["product-page-service"],
                },
                "timeline": [
                    {"time": "11:40:00", "event": "ML model retrain job completed"},
                    {"time": "11:42:15", "event": "Cache miss rate spiked to 98%"},
                    {"time": "11:45:00", "event": "CloudWatch alert fired — p99 > 8s"},
                    {"time": "11:48:00", "event": "Triage complete — P2"},
                    {
                        "time": "12:02:00",
                        "event": "Root cause — cache invalidation storm",
                    },
                    {"time": "12:08:00", "event": "Cache warm-up approved"},
                    {"time": "12:18:00", "event": "Cache populated, latency normalizing"},
                    {"time": "12:20:00", "event": "p99 latency below 300ms — resolved"},
                ],
                "root_cause": (
                    "ML model retrain job invalidated the entire cache simultaneously,"
                    " causing all requests to hit cold S3 storage."
                ),
                "remediation_taken": "Ran cache warm-up job to pre-populate all segments from S3.",
                "prevention": [
                    "Implement staggered cache TTLs so segments expire gradually",
                    "Add automatic cache warming as post-retrain step",
                    (
                        "Set up latency circuit breaker to serve stale"
                        " recommendations during cache rebuilds"
                    ),
                ],
            },
        },
    ],

    # ── inc-004: triaging (just created) ──
    "inc-004": [
        {
            "id": "evt-401", "timestamp": "2026-03-04T14:30:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from PagerDuty alert",
            "payload": {
                "severity": "P3", "category": "queue_backlog",
                "tags": ["email", "queue", "notification", "delayed"],
                "is_duplicate": False,
                "summary": "Email delivery queue backlog growing. 45k pending, delay > 15 min.",
            },
        },
    ],

    # ── inc-005: resolved (full pipeline + post-mortem) ──
    "inc-005": [
        {
            "id": "evt-501", "timestamp": "2026-03-03T22:15:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from CloudWatch alert",
            "payload": {
                "severity": "P1", "category": "payment_failure",
                "tags": ["payments", "stripe", "webhook", "revenue-impacting"],
                "is_duplicate": False,
                "summary": "Stripe webhook handler returning 503s at 78% rate.",
            },
        },
        {
            "id": "evt-502", "timestamp": "2026-03-03T22:17:00Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P1 declared",
            "payload": {
                "severity": "P1", "category": "payment_failure",
                "tags": ["payments", "stripe", "webhook", "revenue-impacting", "database-lock"],
                "is_duplicate": False,
                "summary": "Payment webhook failures at 78%. Stripe retries accumulating.",
            },
        },
        {
            "id": "evt-503", "timestamp": "2026-03-03T22:22:00Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — database connection pool exhausted",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "ConnectionPoolExhaustedException"
                        " in WebhookProcessor.handleEvent()"
                    ),
                    "first_occurrence": "2026-03-03T22:12:44Z",
                    "frequency": "~120 errors/min",
                    "affected_versions": ["payments-service@5.0.3"],
                    "last_healthy_version": "payments-service@5.0.2",
                    "correlated_event": "deployment at 2026-03-03T22:10:00Z",
                    "sample_stack_trace": (
                        "WebhookProcessor.java:203"
                        " → HikariPool-1 connection not available"
                    ),
                },
                "affected_services": [
                    {"service": "payments-service", "status": "down", "impact": "primary"},
                    {"service": "order-service", "status": "degraded", "impact": "downstream"},
                    {
                        "service": "fulfillment-service",
                        "status": "degraded",
                        "impact": "downstream",
                    },
                ],
                "estimated_users_affected": "~2,100 transactions pending",
                "revenue_impact_per_minute": "$3,400",
            },
        },
        {
            "id": "evt-504", "timestamp": "2026-03-03T22:28:00Z",
            "stage": "root_cause", "type": "agent_output",
            "title": "Root cause identified — 93% confidence",
            "payload": {
                "probable_cause": (
                    "payments-service@5.0.3 introduced a long-running"
                    " transaction in the webhook handler that holds"
                    " a DB connection for the duration of Stripe API"
                    " calls. Under load, this exhausts the HikariCP"
                    " connection pool (max 10), causing all"
                    " subsequent webhooks to fail."
                ),
                "confidence_score": 0.93,
                "evidence": [
                    "Connection pool hit 100% within 2 min of deploy",
                    "Active DB connections holding for 8-12s (Stripe RT)",
                    "v5.0.2 processed webhooks in <200ms with no pool contention",
                    "v5.0.3 changelog: 'refactor webhook handler to use transactional processing'",
                ],
                "contributing_factors": [
                    "HikariCP max pool size of 10 is too low"
                    " for transactional webhook processing",
                    "No connection acquisition timeout"
                    " — threads block indefinitely",
                ],
            },
        },
        {
            "id": "evt-505", "timestamp": "2026-03-03T22:30:00Z",
            "stage": "awaiting_approval", "type": "agent_output",
            "title": "Remediation options ready — awaiting approval",
            "payload": {
                "options": [
                    {
                        "id": "opt-1", "title": "Rollback to v5.0.2",
                        "description": "Revert payments-service to pre-deploy version.",
                        "confidence": 0.96, "risk_level": "low",
                        "estimated_recovery_time": "3-5 minutes",
                        "steps": [
                            "kubectl rollout undo deployment/payments-service",
                            "Verify pod health and DB connection pool metrics",
                            "Confirm webhook success rate recovers above 99%",
                            "Trigger Stripe webhook retry for failed events",
                        ],
                    },
                    {
                        "id": "opt-2", "title": "Increase connection pool size",
                        "description": "Bump HikariCP max pool to 50 via config patch.",
                        "confidence": 0.70, "risk_level": "high",
                        "estimated_recovery_time": "5-8 minutes",
                        "steps": [
                            "Patch HIKARI_MAX_POOL_SIZE=50 via kubectl set env",
                            "Rolling restart of payments-service pods",
                            "Monitor DB load — ensure Postgres can handle 50 connections per pod",
                        ],
                    },
                ],
            },
        },
        {
            "id": "evt-506", "timestamp": "2026-03-03T22:32:00Z",
            "stage": "resolving", "type": "human_action",
            "title": "Remediation approved by on-call engineer",
            "payload": {
                "approved_option_id": "opt-1",
                "approved_by": "On-Call Engineer",
                "notes": "Rollback. We'll fix the transaction scope in a hotfix tomorrow.",
            },
        },
        {
            "id": "evt-507", "timestamp": "2026-03-03T22:47:00Z",
            "stage": "resolved", "type": "agent_output",
            "title": "Post-mortem generated",
            "payload": {
                "title": "P1: Payment Webhook Outage — DB Connection Pool Exhaustion",
                "duration": "22:12 - 22:40 UTC (28 minutes)",
                "severity": "P1",
                "impact": {
                    "users_affected": "~2,100",
                    "estimated_revenue_loss": "$95,200",
                    "services_degraded": ["order-service", "fulfillment-service"],
                },
                "timeline": [
                    {"time": "22:10:00", "event": "payments-service@5.0.3 deployed"},
                    {"time": "22:12:44", "event": "First connection pool exhaustion errors"},
                    {"time": "22:15:00", "event": "CloudWatch alert — webhook 503s at 78%"},
                    {"time": "22:17:00", "event": "Triage complete — P1"},
                    {
                        "time": "22:28:00",
                        "event": "Root cause: webhook handler exhausting pool",
                    },
                    {"time": "22:32:00", "event": "Rollback approved"},
                    {
                        "time": "22:37:00",
                        "event": "v5.0.2 running, webhooks recovering",
                    },
                    {"time": "22:40:00", "event": "Webhook success rate > 99% — resolved"},
                ],
                "root_cause": (
                    "v5.0.3 refactored webhook handler to wrap"
                    " Stripe API calls inside a DB transaction,"
                    " holding connections for 8-12s. HikariCP pool"
                    " (max 10) exhausted under load."
                ),
                "remediation_taken": (
                    "Rolled back to v5.0.2."
                    " Stripe webhook retry cleared backlog."
                ),
                "prevention": [
                    "Refactor webhook handler to separate DB writes"
                    " from external API calls",
                    "Increase HikariCP pool size to 30"
                    " with a 5s acquisition timeout",
                    "Add connection pool alert at 80% threshold",
                    "Require load testing for payment-critical paths",
                ],
            },
        },
    ],
    # ── inc-006: resolved — shippingservice flat-rate bug (matches shipping-bug demo) ──
    "inc-006": [
        {
            "id": "evt-601", "timestamp": "2026-02-18T09:30:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from Prometheus alert",
            "payload": {
                "severity": "P2", "category": "data_integrity",
                "tags": ["shipping", "pricing", "calculation-error"],
                "is_duplicate": False,
                "summary": "Shipping cost returning flat $8.99 for all orders.",
            },
        },
        {
            "id": "evt-602", "timestamp": "2026-02-18T09:33:00Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P2 declared",
            "payload": {
                "severity": "P2", "category": "data_integrity",
                "tags": ["shipping", "pricing", "calculation-error", "hardcoded-value"],
                "is_duplicate": False,
                "summary": "Shipping quotes always $8.99. GetQuote handler ignoring item count.",
            },
        },
        {
            "id": "evt-603", "timestamp": "2026-02-18T09:42:00Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — hardcoded argument in GetQuote",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "GetQuote returning identical cost"
                        " for all cart sizes"
                    ),
                    "first_occurrence": "2026-02-18T08:00:00Z",
                    "frequency": "100% of quotes affected",
                    "affected_versions": ["shippingservice@1.3.0"],
                    "last_healthy_version": "shippingservice@1.2.9",
                    "correlated_event": "deployment at 2026-02-18T07:45:00Z",
                    "sample_stack_trace": (
                        "main.go:124"
                        " → CreateQuoteFromCount(0) hardcoded"
                    ),
                },
                "affected_services": [
                    {"service": "shippingservice", "status": "degraded", "impact": "primary"},
                    {
                        "service": "checkout-service",
                        "status": "healthy",
                        "impact": "downstream",
                    },
                ],
                "estimated_users_affected": "~3,200 orders",
                "revenue_impact_per_minute": "$45",
            },
        },
        {
            "id": "evt-604", "timestamp": "2026-02-18T09:50:00Z",
            "stage": "root_cause", "type": "agent_output",
            "title": "Root cause identified — 95% confidence",
            "payload": {
                "probable_cause": (
                    "GetQuote handler in main.go passes hardcoded 0"
                    " to CreateQuoteFromCount() instead of"
                    " len(in.Items). Every quote falls through"
                    " to the flat $8.99 base rate."
                ),
                "confidence_score": 0.95,
                "evidence": [
                    "All 1,247 quotes returned exactly $8.99",
                    "main.go:124 calls CreateQuoteFromCount(0)"
                    " — ignores actual item count",
                    "v1.2.9 correctly passed len(in.Items)",
                    "Regression introduced in refactor commit a7c3d2f",
                ],
                "contributing_factors": [
                    "No unit tests for shipping cost calculation",
                    "Code review missed the hardcoded argument during refactor",
                ],
            },
        },
        {
            "id": "evt-605", "timestamp": "2026-02-18T09:55:00Z",
            "stage": "awaiting_approval", "type": "agent_output",
            "title": "Remediation options ready",
            "payload": {
                "options": [
                    {
                        "id": "opt-1", "title": "Hotfix: pass actual item count",
                        "description": (
                            "Change CreateQuoteFromCount(0) to"
                            " CreateQuoteFromCount(len(in.Items))."
                        ),
                        "confidence": 0.97, "risk_level": "low",
                        "estimated_recovery_time": "10-15 minutes",
                        "steps": [
                            "Fix main.go:124 — pass len(in.Items)"
                            " to CreateQuoteFromCount",
                            "Run shipping cost unit tests",
                            "Deploy hotfix via CI/CD",
                            "Verify quote variance returns to normal",
                        ],
                    },
                ],
            },
        },
        {
            "id": "evt-606", "timestamp": "2026-02-18T09:58:00Z",
            "stage": "resolving", "type": "human_action",
            "title": "Remediation approved",
            "payload": {
                "approved_option_id": "opt-1",
                "approved_by": "On-Call Engineer",
                "notes": "Straightforward fix. Deploy the hotfix.",
            },
        },
        {
            "id": "evt-607", "timestamp": "2026-02-18T10:15:00Z",
            "stage": "resolved", "type": "agent_output",
            "title": "Post-mortem generated",
            "payload": {
                "title": "P2: Shipping Flat-Rate Bug — Hardcoded Argument in GetQuote",
                "duration": "08:00 - 10:12 UTC (2 hours 12 minutes)",
                "severity": "P2",
                "impact": {
                    "users_affected": "~3,200",
                    "estimated_revenue_loss": "$5,400",
                    "services_degraded": [],
                },
                "timeline": [
                    {"time": "07:45:00", "event": "shippingservice@1.3.0 deployed"},
                    {"time": "08:00:00", "event": "First flat-rate quotes observed"},
                    {"time": "09:30:00", "event": "Prometheus alert — 0% shipping cost variance"},
                    {
                        "time": "09:50:00",
                        "event": "Root cause: hardcoded 0 in CreateQuoteFromCount()",
                    },
                    {"time": "09:58:00", "event": "Hotfix approved"},
                    {
                        "time": "10:12:00",
                        "event": "Hotfix deployed, quotes correct",
                    },
                ],
                "root_cause": (
                    "GetQuote handler passed hardcoded 0 to"
                    " CreateQuoteFromCount() instead of the actual"
                    " item count, making all quotes return the"
                    " $8.99 base rate."
                ),
                "remediation_taken": (
                    "Hotfix: changed CreateQuoteFromCount(0)"
                    " to CreateQuoteFromCount(len(in.Items))."
                ),
                "prevention": [
                    "Add unit tests for shipping cost with varying carts",
                    "Add integration test: quote varies by item count",
                    "Require test coverage for pricing-related code changes",
                ],
            },
        },
    ],

    # ── inc-007: resolved — currencyservice conversion failures (matches currency-bug demo) ──
    "inc-007": [
        {
            "id": "evt-701", "timestamp": "2026-02-25T16:45:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from Datadog alert",
            "payload": {
                "severity": "P1", "category": "service_degradation",
                "tags": ["currency", "conversion", "TypeError", "validation"],
                "is_duplicate": False,
                "summary": "Currency conversion failing at 28% — TypeError in convert handler.",
            },
        },
        {
            "id": "evt-702", "timestamp": "2026-02-25T16:48:00Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P1 declared",
            "payload": {
                "severity": "P1", "category": "service_degradation",
                "tags": ["currency", "conversion", "TypeError", "validation", "missing-guard"],
                "is_duplicate": False,
                "summary": (
                    "28% of currency conversions crashing."
                    " Unsupported codes hitting unguarded lookup."
                ),
            },
        },
        {
            "id": "evt-703", "timestamp": "2026-02-25T16:55:00Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — missing input validation in convert()",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "TypeError: Cannot read properties"
                        " of undefined (reading 'units')"
                    ),
                    "first_occurrence": "2026-02-25T16:40:12Z",
                    "frequency": "~95 errors/min",
                    "affected_versions": ["currencyservice@2.1.0"],
                    "last_healthy_version": "currencyservice@2.0.5",
                    "correlated_event": "deployment at 2026-02-25T16:35:00Z",
                    "sample_stack_trace": (
                        "server.js:146"
                        " → data[from.currency_code] is undefined"
                    ),
                },
                "affected_services": [
                    {"service": "currencyservice", "status": "degraded", "impact": "primary"},
                    {
                        "service": "checkout-service",
                        "status": "degraded",
                        "impact": "downstream",
                    },
                    {
                        "service": "product-page-service",
                        "status": "degraded",
                        "impact": "downstream",
                    },
                ],
                "estimated_users_affected": "~5,500 browsing sessions",
                "revenue_impact_per_minute": "$1,200",
            },
        },
        {
            "id": "evt-704", "timestamp": "2026-02-25T17:02:00Z",
            "stage": "root_cause", "type": "agent_output",
            "title": "Root cause identified — 92% confidence",
            "payload": {
                "probable_cause": (
                    "convert() in server.js accesses"
                    " data[from.currency_code] without validating"
                    " that the code exists in the data map."
                    " Unsupported or malformed codes return"
                    " undefined, causing TypeError when"
                    " accessing .units on the result."
                ),
                "confidence_score": 0.92,
                "evidence": [
                    "All errors are TypeError at server.js:146",
                    "Failing requests have codes not in"
                    " currency_conversion.json",
                    "v2.0.5 had try/catch removed in v2.1.0 refactor",
                    "getSupportedCurrencies() returns valid codes"
                    " but convert() doesn't check against it",
                ],
                "contributing_factors": [
                    "No input validation before data map lookup",
                    "Removed error handling during cleanup refactor",
                ],
            },
        },
        {
            "id": "evt-705", "timestamp": "2026-02-25T17:05:00Z",
            "stage": "awaiting_approval", "type": "agent_output",
            "title": "Remediation options ready",
            "payload": {
                "options": [
                    {
                        "id": "opt-1", "title": "Hotfix: add currency code validation",
                        "description": (
                            "Validate currency codes against"
                            " supported list before lookup."
                        ),
                        "confidence": 0.94, "risk_level": "low",
                        "estimated_recovery_time": "10-15 minutes",
                        "steps": [
                            "Add validation in convert() before lookup",
                            "Return INVALID_ARGUMENT gRPC error"
                            " for unsupported codes",
                            "Deploy via CI/CD",
                            "Verify error rate drops to <1%",
                        ],
                    },
                    {
                        "id": "opt-2", "title": "Rollback to v2.0.5",
                        "description": "Revert to previous version with try/catch intact.",
                        "confidence": 0.90, "risk_level": "low",
                        "estimated_recovery_time": "3-5 minutes",
                        "steps": [
                            "kubectl rollout undo deployment/currencyservice",
                            "Verify conversion success rate",
                        ],
                    },
                ],
            },
        },
        {
            "id": "evt-706", "timestamp": "2026-02-25T17:08:00Z",
            "stage": "resolving", "type": "human_action",
            "title": "Remediation approved",
            "payload": {
                "approved_option_id": "opt-2",
                "approved_by": "On-Call Engineer",
                "notes": "Rollback first, then ship the proper fix tomorrow.",
            },
        },
        {
            "id": "evt-707", "timestamp": "2026-02-25T17:22:00Z",
            "stage": "resolved", "type": "agent_output",
            "title": "Post-mortem generated",
            "payload": {
                "title": "P1: Currency Conversion Failures — Missing Input Validation",
                "duration": "16:40 - 17:15 UTC (35 minutes)",
                "severity": "P1",
                "impact": {
                    "users_affected": "~5,500",
                    "estimated_revenue_loss": "$42,000",
                    "services_degraded": ["checkout-service", "product-page-service"],
                },
                "timeline": [
                    {"time": "16:35:00", "event": "currencyservice@2.1.0 deployed"},
                    {"time": "16:40:12", "event": "First TypeError in convert()"},
                    {"time": "16:45:00", "event": "Datadog alert — 28% error rate"},
                    {
                        "time": "17:02:00",
                        "event": "Root cause: missing currency code validation",
                    },
                    {"time": "17:08:00", "event": "Rollback to v2.0.5 approved"},
                    {"time": "17:13:00", "event": "v2.0.5 running, errors stopped"},
                    {"time": "17:15:00", "event": "Error rate <1% — resolved"},
                ],
                "root_cause": (
                    "convert() accessed data[from.currency_code]"
                    " without checking the code exists."
                    " Unsupported codes returned undefined,"
                    " crashing on .units access."
                ),
                "remediation_taken": (
                    "Rolled back to v2.0.5 which had"
                    " try/catch error handling."
                ),
                "prevention": [
                    "Add input validation for currency codes",
                    "Add tests for unsupported currency code handling",
                    "Enforce review approval for error handling removal",
                ],
            },
        },
    ],

    # ── inc-008: resolved — recommendationservice crash (matches recommendation-bug demo) ──
    "inc-008": [
        {
            "id": "evt-801", "timestamp": "2026-02-10T11:20:00Z",
            "stage": "triaging", "type": "system_event",
            "title": "Incident created from Prometheus alert",
            "payload": {
                "severity": "P2", "category": "application_crash",
                "tags": ["recommendations", "ValueError", "edge-case", "empty-list"],
                "is_duplicate": False,
                "summary": "Recommendation service crashing on empty product list edge case.",
            },
        },
        {
            "id": "evt-802", "timestamp": "2026-02-10T11:23:00Z",
            "stage": "triaging", "type": "agent_output",
            "title": "Triage complete — P2 declared",
            "payload": {
                "severity": "P2", "category": "application_crash",
                "tags": [
                    "recommendations", "ValueError",
                    "edge-case", "empty-list", "random-sample",
                ],
                "is_duplicate": False,
                "summary": (
                    "8% of recommendation requests crashing."
                    " Empty filtered list hitting random.sample()."
                ),
            },
        },
        {
            "id": "evt-803", "timestamp": "2026-02-10T11:32:00Z",
            "stage": "investigating", "type": "agent_output",
            "title": "Investigation complete — random.sample() on empty range",
            "payload": {
                "log_findings": {
                    "error_pattern": (
                        "ValueError: Sample larger than"
                        " population or is negative"
                    ),
                    "first_occurrence": "2026-02-10T11:15:33Z",
                    "frequency": "~30 errors/min",
                    "affected_versions": ["recommendationservice@2.4.0"],
                    "last_healthy_version": "recommendationservice@2.3.8",
                    "correlated_event": "deployment at 2026-02-10T11:10:00Z",
                    "sample_stack_trace": (
                        "recommendation_server.py:79"
                        " → random.sample(range(0), 5)"
                    ),
                },
                "affected_services": [
                    {
                        "service": "recommendationservice",
                        "status": "degraded",
                        "impact": "primary",
                    },
                    {
                        "service": "product-page-service",
                        "status": "healthy",
                        "impact": "downstream",
                    },
                ],
                "estimated_users_affected": "~800 browsing sessions",
                "revenue_impact_per_minute": "$60",
            },
        },
        {
            "id": "evt-804", "timestamp": "2026-02-10T11:38:00Z",
            "stage": "root_cause", "type": "agent_output",
            "title": "Root cause identified — 94% confidence",
            "payload": {
                "probable_cause": (
                    "ListRecommendations filters out products already in the user's cart."
                    " When all products are in the cart, the filtered list is empty."
                    " random.sample(range(0), 5) raises ValueError because you can't"
                    " sample 5 items from an empty range."
                ),
                "confidence_score": 0.94,
                "evidence": [
                    "All crashes when product_ids contains all products",
                    "recommendation_server.py:79 calls random.sample"
                    " without checking list length",
                    "v2.3.8 had a guard: if not filtered_products: return []",
                    "Guard was accidentally removed in v2.4.0 refactor",
                ],
                "contributing_factors": [
                    "No edge case test for full-cart scenario",
                    "Product catalog is small (7 items) so full-cart is common",
                ],
            },
        },
        {
            "id": "evt-805", "timestamp": "2026-02-10T11:42:00Z",
            "stage": "awaiting_approval", "type": "agent_output",
            "title": "Remediation options ready",
            "payload": {
                "options": [
                    {
                        "id": "opt-1", "title": "Hotfix: add empty list guard",
                        "description": (
                            "Add check before random.sample —"
                            " return empty list if no products."
                        ),
                        "confidence": 0.96, "risk_level": "low",
                        "estimated_recovery_time": "10-15 minutes",
                        "steps": [
                            "Add guard: if not filtered_products: return empty response",
                            "Deploy via CI/CD",
                            "Verify error rate drops to 0%",
                        ],
                    },
                ],
            },
        },
        {
            "id": "evt-806", "timestamp": "2026-02-10T11:44:00Z",
            "stage": "resolving", "type": "human_action",
            "title": "Remediation approved",
            "payload": {
                "approved_option_id": "opt-1",
                "approved_by": "On-Call Engineer",
                "notes": "Simple guard fix.",
            },
        },
        {
            "id": "evt-807", "timestamp": "2026-02-10T11:55:00Z",
            "stage": "resolved", "type": "agent_output",
            "title": "Post-mortem generated",
            "payload": {
                "title": "P2: Recommendation Crash — Empty Product List Edge Case",
                "duration": "11:15 - 11:52 UTC (37 minutes)",
                "severity": "P2",
                "impact": {
                    "users_affected": "~800",
                    "estimated_revenue_loss": "$2,220",
                    "services_degraded": [],
                },
                "timeline": [
                    {"time": "11:10:00", "event": "recommendationservice@2.4.0 deployed"},
                    {"time": "11:15:33", "event": "First ValueError crashes"},
                    {"time": "11:20:00", "event": "Prometheus alert — 8% error rate"},
                    {
                        "time": "11:38:00",
                        "event": "Root cause: random.sample on empty list",
                    },
                    {"time": "11:44:00", "event": "Hotfix approved"},
                    {"time": "11:50:00", "event": "Hotfix deployed, no more crashes"},
                    {"time": "11:52:00", "event": "Error rate 0% — resolved"},
                ],
                "root_cause": (
                    "ListRecommendations called random.sample() on an empty range when all"
                    " products were already in the user's cart. Missing empty-list guard."
                ),
                "remediation_taken": (
                    "Added guard: return empty response"
                    " when filtered_products is empty."
                ),
                "prevention": [
                    "Add test for full-cart edge case (all products in cart)",
                    "Add test for empty product catalog scenario",
                    "Expand product catalog to reduce likelihood of full-cart edge case",
                ],
            },
        },
    ],
}


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------

async def seed_db(session: AsyncSession) -> None:
    """Insert seed data if the DB is empty."""
    result = await session.execute(select(IncidentRow).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    # Create incidents
    for inc in INCIDENTS:
        alert = ALERTS[inc["id"]]
        session.add(IncidentRow(
            id=inc["id"],
            status=inc["status"],
            severity=inc["severity"],
            service=inc["service"],
            environment=inc["environment"],
            summary=inc["summary"],
            alert=alert,
            created_at=inc["created_at"],
            updated_at=inc["updated_at"],
            resolved_at=inc["resolved_at"],
        ))

    # Create timeline events
    for incident_id, events in TIMELINES.items():
        for evt in events:
            session.add(TimelineEventRow(
                id=evt["id"],
                incident_id=incident_id,
                timestamp=evt["timestamp"],
                stage=evt["stage"],
                type=evt["type"],
                title=evt["title"],
                payload=evt["payload"],
            ))

    await session.commit()

    # Index resolved incidents for similar-incident search
    await _seed_embeddings(session)


async def _seed_embeddings(session: AsyncSession) -> None:
    """Compute and store embeddings for resolved seed incidents."""
    try:
        from app.services.embedding import get_embedding_service
        from app.services.similar_incidents import SimilarIncidentService

        svc = SimilarIncidentService(session, get_embedding_service())
        for inc in INCIDENTS:
            if inc["status"] == "resolved":
                await svc.index_incident(inc["id"])
                logger.info("Indexed %s for similarity search", inc["id"])
    except Exception:
        logger.exception(
            "Failed to seed embeddings"
            " — similarity search will be empty until incidents resolve"
        )
