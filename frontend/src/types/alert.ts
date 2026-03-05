export interface Alert {
  id: string
  source: string
  service: string
  environment: string
  metric: string
  value: string
  threshold: string
  message: string
  timestamp: string
}
