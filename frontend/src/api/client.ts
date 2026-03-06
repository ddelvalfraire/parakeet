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

export interface ApiClient {
  listIncidents(): Promise<ListIncidentsResponse>
  getIncident(id: string): Promise<GetIncidentResponse>
  createIncident(req: CreateIncidentRequest): Promise<CreateIncidentResponse>
  submitAction(incidentId: string, req: SubmitActionRequest): Promise<SubmitActionResponse>
  generateRetro(incidentId: string): Promise<GenerateRetroResponse>

  // Demo
  listScenarios(): Promise<ListScenariosResponse>
  startDemo(req: StartDemoRequest): Promise<StartDemoResponse>
  resetDemo(): Promise<ResetDemoResponse>

  // Additional incident actions
  mergeFix(incidentId: string, req: MergeFixRequest): Promise<SubmitActionResponse>
  resolveManually(incidentId: string, req: ResolveManuallyRequest): Promise<SubmitActionResponse>

  // Similar incidents
  getSimilarIncidents(incidentId: string): Promise<SimilarIncidentsResponse>
}
