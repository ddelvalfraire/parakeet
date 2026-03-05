import type { Incident, IncidentSummary } from '@/types/incident'
import type { PostMortem } from '@/types/agents'

export const INCIDENT_SUMMARIES: IncidentSummary[] = [
  {
    id: 'inc-001',
    status: 'awaiting_approval',
    severity: 'P1',
    service: 'checkout-service',
    environment: 'production',
    summary:
      'Checkout service experiencing near-total failure. 94% error rate. Revenue impact immediate.',
    created_at: '2026-03-04T14:23:11Z',
    updated_at: '2026-03-04T14:26:45Z',
  },
  {
    id: 'inc-002',
    status: 'investigating',
    severity: 'P2',
    service: 'auth-service',
    environment: 'production',
    summary:
      'Elevated login failure rate detected. 23% of authentication requests failing.',
    created_at: '2026-03-04T13:10:00Z',
    updated_at: '2026-03-04T13:18:30Z',
  },
  {
    id: 'inc-003',
    status: 'resolved',
    severity: 'P2',
    service: 'recommendations-service',
    environment: 'production',
    summary:
      'Recommendations service latency spike. p99 latency exceeded 8s threshold.',
    created_at: '2026-03-04T11:45:00Z',
    updated_at: '2026-03-04T12:10:00Z',
  },
  {
    id: 'inc-004',
    status: 'triaging',
    severity: 'P3',
    service: 'email-notification-service',
    environment: 'production',
    summary:
      'Email delivery queue backlog growing. Processing delay exceeding 15 minutes.',
    created_at: '2026-03-04T14:30:00Z',
    updated_at: '2026-03-04T14:30:45Z',
  },
  {
    id: 'inc-005',
    status: 'resolved',
    severity: 'P1',
    service: 'payments-service',
    environment: 'production',
    summary:
      'Payment processing failures. Stripe webhook handler throwing 503s.',
    created_at: '2026-03-03T22:15:00Z',
    updated_at: '2026-03-03T22:47:00Z',
  },
]

export const INCIDENT_DETAIL: Incident = {
  id: 'inc-001',
  status: 'awaiting_approval',
  severity: 'P1',
  service: 'checkout-service',
  environment: 'production',
  summary:
    'Checkout service experiencing near-total failure. 94% error rate. Revenue impact immediate.',
  created_at: '2026-03-04T14:23:11Z',
  updated_at: '2026-03-04T14:26:45Z',
  resolved_at: null,

  alert: {
    id: 'alert-001',
    source: 'CloudWatch',
    service: 'checkout-service',
    environment: 'production',
    metric: '5xx_error_rate',
    value: '94%',
    threshold: '5%',
    message: 'checkout-service error rate exceeded threshold',
    timestamp: '2026-03-04T14:23:11Z',
  },

  timeline: [
    {
      id: 'evt-001',
      incident_id: 'inc-001',
      timestamp: '2026-03-04T14:23:11Z',
      stage: 'triaging',
      type: 'system_event',
      title: 'Incident created from CloudWatch alert',
      payload: {
        severity: 'P1',
        category: 'service_degradation',
        tags: [
          'revenue-impacting',
          'customer-facing',
          'checkout',
          'high-error-rate',
        ],
        is_duplicate: false,
        summary:
          'Checkout service experiencing near-total failure in production. 94% error rate. Revenue impact immediate.',
      },
    },
    {
      id: 'evt-002',
      incident_id: 'inc-001',
      timestamp: '2026-03-04T14:24:02Z',
      stage: 'triaging',
      type: 'agent_output',
      title: 'Triage complete — P1 declared',
      payload: {
        severity: 'P1',
        category: 'service_degradation',
        tags: [
          'revenue-impacting',
          'customer-facing',
          'checkout',
          'high-error-rate',
        ],
        is_duplicate: false,
        summary:
          'Checkout service experiencing near-total failure in production. 94% error rate. Revenue impact immediate.',
      },
    },
    {
      id: 'evt-003',
      incident_id: 'inc-001',
      timestamp: '2026-03-04T14:24:45Z',
      stage: 'investigating',
      type: 'agent_output',
      title: 'Investigation complete — logs and blast radius mapped',
      payload: {
        log_findings: {
          error_pattern:
            'NullPointerException in PaymentGatewayClient.processPayment()',
          first_occurrence: '2026-03-04T14:21:03Z',
          frequency: '~340 errors/min',
          affected_versions: ['checkout-service@2.4.1'],
          last_healthy_version: 'checkout-service@2.4.0',
          correlated_event: 'deployment at 2026-03-04T14:19:45Z',
          sample_stack_trace:
            'PaymentGatewayClient.java:142 → null reference on stripeApiKey',
        },
        affected_services: [
          {
            service: 'checkout-service',
            status: 'down',
            impact: 'primary',
          },
          {
            service: 'order-service',
            status: 'degraded',
            impact: 'downstream',
          },
          {
            service: 'inventory-service',
            status: 'degraded',
            impact: 'downstream',
          },
          {
            service: 'notification-service',
            status: 'healthy',
            impact: 'none',
          },
        ],
        estimated_users_affected: '~4,200 active sessions',
        revenue_impact_per_minute: '$2,800',
      },
    },
    {
      id: 'evt-004',
      incident_id: 'inc-001',
      timestamp: '2026-03-04T14:26:45Z',
      stage: 'root_cause',
      type: 'agent_output',
      title: 'Root cause identified — 91% confidence',
      payload: {
        probable_cause:
          'Deployment of checkout-service@2.4.1 introduced a null reference on stripeApiKey. The Stripe API key environment variable is absent from the new deployment configuration.',
        confidence_score: 0.91,
        evidence: [
          'Error pattern began 78 seconds after deployment at 14:19:45',
          'NullPointerException consistently at PaymentGatewayClient.java:142',
          'checkout-service@2.4.0 had no errors in preceding 48 hours',
          'stripeApiKey referenced in 2.4.1 changelog under config changes',
        ],
        contributing_factors: [
          'No canary deployment — change went straight to 100% traffic',
          'Missing environment variable validation on startup',
        ],
      },
    },
    {
      id: 'evt-005',
      incident_id: 'inc-001',
      timestamp: '2026-03-04T14:27:30Z',
      stage: 'awaiting_approval',
      type: 'agent_output',
      title: 'Remediation options ready — awaiting approval',
      payload: {
        options: [
          {
            id: 'opt-1',
            title: 'Rollback to v2.4.0',
            description:
              'Revert checkout-service to last known good version.',
            confidence: 0.95,
            risk_level: 'low',
            estimated_recovery_time: '3-5 minutes',
            steps: [
              'kubectl rollout undo deployment/checkout-service',
              'Verify pod health — wait for 3/3 running',
              'Confirm error rate drops below 1% in CloudWatch',
              'Notify on-call team of rollback completion',
            ],
          },
          {
            id: 'opt-2',
            title: 'Inject missing environment variable',
            description:
              'Patch deployment config with missing stripeApiKey and re-deploy.',
            confidence: 0.78,
            risk_level: 'medium',
            estimated_recovery_time: '8-12 minutes',
            steps: [
              'kubectl set env deployment/checkout-service STRIPE_API_KEY=<value>',
              'Trigger rolling restart',
              'Monitor error rate for 5 minutes post-restart',
            ],
          },
          {
            id: 'opt-3',
            title: 'Feature flag — disable new payment flow',
            description:
              'Toggle off the v2.4.1 payment path, fall back to legacy flow.',
            confidence: 0.61,
            risk_level: 'medium',
            estimated_recovery_time: '2 minutes',
            steps: [
              'Set feature flag CHECKOUT_V2=false in LaunchDarkly',
              'Confirm traffic routing to legacy payment handler',
              'Monitor legacy flow error rate',
            ],
          },
        ],
      },
    },
  ],
}

export const POSTMORTEM_FIXTURE: PostMortem = {
  title: 'P1: Checkout Service Outage — 2026-03-04',
  duration: '14:21 - 14:38 UTC (17 minutes)',
  severity: 'P1',
  impact: {
    users_affected: '~4,200',
    estimated_revenue_loss: '$47,600',
    services_degraded: ['order-service', 'inventory-service'],
  },
  timeline: [
    {
      time: '14:19:45',
      event: 'checkout-service@2.4.1 deployed to production',
    },
    { time: '14:21:03', event: 'First 5xx errors detected' },
    {
      time: '14:23:11',
      event: 'CloudWatch alert fired — 94% error rate',
    },
    { time: '14:24:02', event: 'Incident created, triage complete (P1)' },
    {
      time: '14:26:45',
      event: 'Root cause identified — missing STRIPE_API_KEY',
    },
    {
      time: '14:31:10',
      event: 'Rollback approved by on-call engineer',
    },
    {
      time: '14:36:22',
      event: 'checkout-service@2.4.0 running, error rate < 1%',
    },
    { time: '14:38:00', event: 'Incident resolved' },
  ],
  root_cause:
    'Missing STRIPE_API_KEY environment variable in v2.4.1 deployment config.',
  remediation_taken: 'Rolled back to v2.4.0 via kubectl rollout undo.',
  prevention: [
    'Add environment variable validation to deployment startup checks',
    'Enforce canary deployments for checkout-service',
    'Add pre-deploy config diff check to CI/CD pipeline',
  ],
}
