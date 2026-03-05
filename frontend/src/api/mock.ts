import type { ApiClient } from './client'
import type {
  ListIncidentsResponse,
  GetIncidentResponse,
  CreateIncidentRequest,
  CreateIncidentResponse,
  SubmitActionRequest,
  SubmitActionResponse,
  GenerateRetroResponse,
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
    return { incidents: INCIDENT_SUMMARIES }
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
}
