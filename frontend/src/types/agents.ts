import type { Severity, RiskLevel, ServiceStatus, ImpactLevel } from './domain'

export interface TriageResult {
  severity: Severity
  category: string
  tags: string[]
  is_duplicate: boolean
  summary: string
}

export interface LogFindings {
  error_pattern: string
  first_occurrence: string
  frequency: string
  affected_versions: string[]
  last_healthy_version: string
  correlated_event: string | null
  sample_stack_trace: string | null
}

export interface AffectedService {
  service: string
  status: ServiceStatus
  impact: ImpactLevel
}

export interface InvestigationResult {
  log_findings: LogFindings
  affected_services: AffectedService[]
  estimated_users_affected: string
}

export interface RootCauseResult {
  probable_cause: string
  confidence_score: number
  evidence: string[]
  contributing_factors: string[]
}

export interface RemediationOption {
  id: string
  title: string
  description: string
  confidence: number
  risk_level: RiskLevel
  estimated_recovery_time: string
  steps: string[]
}

export interface PRInfo {
  pr_number: number
  pr_url: string
  diff: string
  file_path: string
  branch: string
}

export interface RemediationResult {
  options: RemediationOption[]
  pr?: PRInfo
}

export interface DemoScenario {
  id: string
  title: string
  service: string
  severity: string
  language: string
  description: string
}

export interface HumanDecision {
  approved_option_id: string
  approved_by: string
  notes: string | null
}

export interface PostMortemImpact {
  users_affected: string
  services_degraded: string[]
}

export interface PostMortemTimelineEntry {
  time: string
  event: string
}

export interface LessonsLearned {
  went_well: string[]
  went_wrong: string[]
  got_lucky: string[]
}

export interface PostMortem {
  title: string
  duration: string
  severity: Severity
  summary: string
  impact: PostMortemImpact
  timeline: PostMortemTimelineEntry[]
  root_cause: string
  contributing_factors: string[]
  remediation_taken: string
  lessons_learned: LessonsLearned
  prevention: string[]
}

export interface SimilarIncident {
  incident_id: string
  service: string
  severity: Severity
  summary: string
  root_cause: string
  remediation_taken: string
  resolved_at: string
  similarity_score: number
}
