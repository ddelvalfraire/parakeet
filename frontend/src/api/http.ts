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
}
