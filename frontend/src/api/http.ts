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
} from '@/types/api'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const httpClient: ApiClient = {
  async listIncidents(): Promise<ListIncidentsResponse> {
    return request('/incidents')
  },

  async getIncident(id: string): Promise<GetIncidentResponse> {
    return request(`/incidents/${id}`)
  },

  async createIncident(req: CreateIncidentRequest): Promise<CreateIncidentResponse> {
    return request('/incidents', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  async submitAction(
    incidentId: string,
    req: SubmitActionRequest,
  ): Promise<SubmitActionResponse> {
    return request(`/incidents/${incidentId}/action`, {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  async generateRetro(incidentId: string): Promise<GenerateRetroResponse> {
    return request(`/incidents/${incidentId}/retro`, {
      method: 'POST',
    })
  },

  // Demo
  async listScenarios(): Promise<ListScenariosResponse> {
    return request('/demo/scenarios')
  },

  async startDemo(req: StartDemoRequest): Promise<StartDemoResponse> {
    return request('/demo/start', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  async resetDemo(): Promise<ResetDemoResponse> {
    return request('/demo/reset', {
      method: 'POST',
    })
  },

  // Additional incident actions
  async mergeFix(
    incidentId: string,
    req: MergeFixRequest,
  ): Promise<SubmitActionResponse> {
    return request(`/incidents/${incidentId}/merge-fix`, {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  async resolveManually(
    incidentId: string,
    req: ResolveManuallyRequest,
  ): Promise<SubmitActionResponse> {
    return request(`/incidents/${incidentId}/resolve-manual`, {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },
}
