import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

export interface StatsSummary {
  active_fires_24h: number
  active_fires_trend_7d: number[]
  active_fires_trend_31d: number[]
  burned_area_hectares_total: number
  co2_estimate_tons_total: number
  active_alerts: number
}

export async function fetchStatsSummary(): Promise<StatsSummary> {
  const response = await axios.get<StatsSummary>(
    `${API_BASE_URL}/stats`,
  )

  return response.data
}