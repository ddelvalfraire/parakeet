import type { ApiClient } from './client'
import type {
  ListIncidentsResponse,
  GetIncidentResponse,
  CreateIncidentRequest,
  CreateIncidentResponse,
  SubmitActionRequest,
  SubmitActionResponse,
  GenerateRetroResponse,
  ListScenariosResponse,
  StartDemoRequest,
  StartDemoResponse,
  ResetDemoResponse,
  MergeFixRequest,
  ResolveManuallyRequest,
  SimilarIncidentsResponse,
} from '@/types/api'
import {
  INCIDENT_SUMMARIES,
  INCIDENT_DETAIL,
  POSTMORTEM_FIXTURE,
} from '@/mocks/fixtures'

const delay = (ms = 300) => new Promise((r) => setTimeout(r, ms))

export const mockClient: ApiClient = {
  async listIncidents(): Promise<ListIncidentsResponse> {
    await delay()
    return { incidents: INCIDENT_SUMMARIES, total: INCIDENT_SUMMARIES.length }
  },

  async getIncident(id: string): Promise<GetIncidentResponse> {
    await delay()
    if (id === INCIDENT_DETAIL.id) {
      return { incident: INCIDENT_DETAIL }
    }
    throw new Error(`Incident ${id} not found`)
  },

  async createIncident(_req: CreateIncidentRequest): Promise<CreateIncidentResponse> {
    await delay()
    return { incident: INCIDENT_SUMMARIES[0] }
  },

  async submitAction(_incidentId: string, _req: SubmitActionRequest): Promise<SubmitActionResponse> {
    await delay(500)
    return { success: true, incident_status: 'resolving' }
  },

  async generateRetro(_incidentId: string): Promise<GenerateRetroResponse> {
    await delay(800)
    return { post_mortem: POSTMORTEM_FIXTURE }
  },

  async listScenarios(): Promise<ListScenariosResponse> {
    await delay()
    return { scenarios: [], demo_active: false }
  },

  async startDemo(_req: StartDemoRequest): Promise<StartDemoResponse> {
    await delay()
    return { incident: INCIDENT_SUMMARIES[0] }
  },

  async resetDemo(): Promise<ResetDemoResponse> {
    await delay()
    return { success: true, prs_closed: 0, branches_deleted: 0 }
  },

  async mergeFix(_incidentId: string, _req: MergeFixRequest): Promise<SubmitActionResponse> {
    await delay()
    return { success: true, incident_status: 'resolving' }
  },

  async resolveManually(
    _incidentId: string,
    _req: ResolveManuallyRequest,
  ): Promise<SubmitActionResponse> {
    await delay()
    return { success: true, incident_status: 'resolved' }
  },

  async getSimilarIncidents(_incidentId: string): Promise<SimilarIncidentsResponse> {
    await delay()
    return { similar: [], query_incident_id: _incidentId }
  },
}
