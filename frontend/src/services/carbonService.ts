import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

export type CarbonSource = 'modis' | 'sentinel2'

export interface BurnedArea {
  id: number
  region: string
  area_hectares: number
  carbon_tons_estimate: number
  period_start: string
  period_end: string
  computed_at: string
  source: CarbonSource
}

/**
 * Historique JOUR PAR JOUR : chaque ligne = un jour où une combustion a
 * été détectée par un satellite précis. C'est celle-ci que l'UI utilise
 * pour afficher l'évolution réelle, pas un blob agrégé par fenêtre.
 */
export async function fetchCarbonHistory(sinceDays: number = 90): Promise<BurnedArea[]> {
  const response = await axios.get<BurnedArea[]>(`${API_BASE_URL}/carbon/history`, {
    params: { since_days: sinceDays }
  })
  return response.data
}

/**
 * Liste BRUTE de tous les runs (debug/admin, inclut les anciens scans par
 * fenêtre) -> pas pour l'UI principale.
 */
export async function fetchCarbonEstimatesHistory(sinceDays: number = 90): Promise<BurnedArea[]> {
  const response = await axios.get<BurnedArea[]>(`${API_BASE_URL}/carbon/estimates`, {
    params: { since_days: sinceDays }
  })
  return response.data
}
