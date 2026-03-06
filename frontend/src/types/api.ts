import type { IncidentSummary, Incident } from './incident'
import type { IncidentStatus } from './domain'
import type { PostMortem, DemoScenario } from './agents'
import type { Alert } from './alert'

// GET /incidents
export interface ListIncidentsResponse {
  incidents: IncidentSummary[]
  total: number
}

// GET /incidents/:id
export interface GetIncidentResponse {
  incident: Incident
}

// POST /incidents
export interface CreateIncidentRequest {
  alert: Alert
}
export interface CreateIncidentResponse {
  incident: IncidentSummary
}

// POST /incidents/:id/action  (HITL)
export interface SubmitActionRequest {
  approved_option_id: string
  approved_by: string
  notes?: string
}
export interface SubmitActionResponse {
  success: boolean
  incident_status: IncidentStatus
}

// POST /incidents/:id/retro
export interface GenerateRetroResponse {
  post_mortem: PostMortem
}

// GET /demo/scenarios
export interface ListScenariosResponse {
  scenarios: DemoScenario[]
}

// POST /demo/start
export interface StartDemoRequest {
  scenario_id: string
}
export interface StartDemoResponse {
  incident: IncidentSummary
}

// POST /demo/reset
export interface ResetDemoResponse {
  success: boolean
  prs_closed: number
  branches_deleted: number
}

// POST /incidents/:id/merge-fix
export interface MergeFixRequest {
  approved_by: string
  notes?: string
}

// POST /incidents/:id/resolve-manual
export interface ResolveManuallyRequest {
  explanation: string
  approved_by: string
}

// WebSocket — /ws/incidents/:id
export interface WSEvent {
  type: 'stage_change' | 'timeline_append' | 'awaiting_approval' | 'resolved'
  incident_id: string
  timestamp: string
  payload: import('./incident').TimelineEvent | { status: IncidentStatus }
}
