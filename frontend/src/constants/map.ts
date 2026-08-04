// Centre géographique du COFAV
export const COFAV_CENTER: [number, number] = [-21.84, 47.30]

// Coordonnées du polygone COFAV (Ambositra - Vondrozo)
export const COFAV_POLYGON: [number, number][] = [
  [-20.58, 47.25], // Nord (Ambositra)
  [-20.80, 47.45],
  [-21.50, 47.55],
  [-22.30, 47.40],
  [-23.06, 47.20], // Sud (Vondrozo)
  [-23.00, 46.85],
  [-22.10, 46.90],
  [-21.20, 47.05],
]

// Villes clés le long du Corridor (comme sur l'image carte_2.jpg)
export interface CityMarker {
  name: string
  lat: number
  lng: number
  isMain?: boolean
}

export const COFAV_CITIES: CityMarker[] = [
  { name: 'Commune Urbaine Ambositra', lat: -20.531, lng: 47.243, isMain: true },
  { name: 'Ivato', lat: -20.613, lng: 47.182 },
  { name: 'Fianarantsoa', lat: -21.453, lng: 47.086, isMain: true },
  { name: 'Ambalavao', lat: -21.833, lng: 46.933 },
  { name: 'Vondrozo', lat: -22.817, lng: 47.317, isMain: true },
  { name: 'Mananjary', lat: -21.231, lng: 48.333 },
  { name: 'Manakara', lat: -22.148, lng: 48.010 },
  { name: 'Farafangana', lat: -22.817, lng: 47.833 },
  { name: 'Ihosy', lat: -22.400, lng: 46.117 }
]

// Emprise géographique resserrée
export const COFAV_BOUNDS: [[number, number], [number, number]] = [
  [-23.15, 46.10],
  [-20.30, 48.40]
]

export const DEFAULT_MAP_ZOOM = 8