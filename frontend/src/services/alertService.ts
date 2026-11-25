import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

export type AlertLevel = 'low' | 'medium' | 'high'

export interface Alert {
  id: number
  region: string
  level: AlertLevel
  message: string
  triggered_at: string
  resolved: boolean
}

export async function fetchActiveAlerts(): Promise<Alert[]> {
  const response = await axios.get<Alert[]>(`${API_BASE_URL}/alerts/active`)
  return response.data
}
