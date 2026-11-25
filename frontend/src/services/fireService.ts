import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

export interface FireFeatureCollection {
  type: 'FeatureCollection'
  features: Array<{
    type: 'Feature'
    geometry: {
      type: 'Point'
      coordinates: [number, number] // [longitude, latitude]
    }
    properties: {
      brightness?: number
      confidence?: string | number
      acq_date?: string
      acq_time?: string
      frp?: number
      satellite?: string
      [key: string]: unknown
    }
  }>
}

export async function fetchRecentFires(
  dayRange: number = 7
): Promise<FireFeatureCollection> {
  const response = await axios.get<FireFeatureCollection>(
    `${API_BASE_URL}/fires/recent`,
    {
      params: { day_range: dayRange },
    }
  )

  return response.data
}