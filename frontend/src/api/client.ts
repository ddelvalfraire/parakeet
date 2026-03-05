import type {
  ListIncidentsResponse,
  GetIncidentResponse,
  CreateIncidentRequest,
  CreateIncidentResponse,
  SubmitActionRequest,
  SubmitActionResponse,
  GenerateRetroResponse,
} from '@/types/api'

export interface ApiClient {
  listIncidents(): Promise<ListIncidentsResponse>
  getIncident(id: string): Promise<GetIncidentResponse>
  createIncident(req: CreateIncidentRequest): Promise<CreateIncidentResponse>
  submitAction(incidentId: string, req: SubmitActionRequest): Promise<SubmitActionResponse>
  generateRetro(incidentId: string): Promise<GenerateRetroResponse>
}
