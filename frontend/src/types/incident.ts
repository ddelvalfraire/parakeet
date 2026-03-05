import type { IncidentStatus, Severity, TimelineEventType } from './domain'
import type {
  TriageResult,
  InvestigationResult,
  RootCauseResult,
  RemediationResult,
  HumanDecision,
  PostMortem,
} from './agents'
import type { Alert } from './alert'

export type TimelinePayload =
  | TriageResult
  | InvestigationResult
  | RootCauseResult
  | RemediationResult
  | HumanDecision
  | PostMortem

export interface TimelineEvent {
  id: string
  incident_id: string
  timestamp: string
  stage: IncidentStatus
  type: TimelineEventType
  title: string
  payload: TimelinePayload
}

export interface IncidentSummary {
  id: string
  status: IncidentStatus
  severity: Severity
  service: string
  environment: string
  summary: string
  created_at: string
  updated_at: string
}

export interface Incident extends IncidentSummary {
  alert: Alert
  timeline: TimelineEvent[]
  resolved_at: string | null
}
