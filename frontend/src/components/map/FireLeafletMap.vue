<template>
  <div class="relative w-full h-112.5 rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
    <!-- Conteneur Leaflet -->
    <div ref="mapContainer" class="w-full h-full z-0"></div>

    <!-- Indicateur de chargement -->
    <div
      v-if="isLoading"
      class="absolute bottom-4 left-4 z-10 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/50 flex items-center gap-2 text-xs text-slate-300"
    >
      <span class="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
      <span>Chargement des feux récents...</span>
    </div>

    <!-- Légende interactive -->
    <div class="absolute top-4 right-4 z-10 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-xl shadow-md border border-slate-700/50 flex items-center gap-4 text-xs font-medium text-slate-200">
      <div class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse"></span>
        <span>Feux actifs ({{ fireCount }})</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
        <span>Corridor COFAV</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { COFAV_BOUNDS, COFAV_POLYGON, COFAV_CITIES } from '@/constants/map'
import { fetchRecentFires } from '@/services/fireService'

const mapContainer = ref<HTMLElement | null>(null)
const isLoading = ref<boolean>(false)
const fireCount = ref<number>(0)

let mapInstance: L.Map | null = null
let fireLayerGroup: L.LayerGroup | null = null

const loadFireData = async () => {
  if (!mapInstance) return
  
  isLoading.value = true
  try {
    // Appel au backend FastAPI (7 jours par défaut pour assurer l'affichage)
    const geojsonData = await fetchRecentFires(7)
    
    if (fireLayerGroup) {
      fireLayerGroup.clearLayers()
    } else {
      fireLayerGroup = L.layerGroup().addTo(mapInstance)
    }

    fireCount.value = geojsonData.features?.length || 0

    // Injection du GeoJSON sur la carte
    L.geoJSON(geojsonData, {
      pointToLayer: (feature, latlng) => {
        return L.circleMarker(latlng, {
          radius: 7,
          fillColor: '#f97316', // Orange feux
          color: '#ef4444',     // Bordure rouge
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.85
        })
      },
      onEachFeature: (feature, layer) => {
        const props = feature.properties || {}
        const date = props.acq_date || 'N/A'
        const time = props.acq_time ? `${props.acq_time} UTC` : ''
        const brightness = props.brightness ? `${props.brightness} K` : 'N/A'
        const frp = props.frp ? `${props.frp} MW` : 'N/A'

        const popupContent = `
          <div class="text-xs font-sans text-slate-800 p-1">
            <h4 class="font-bold text-orange-600 mb-1">🔥 Détection de feu</h4>
            <p><strong>Date:</strong> ${date} ${time}</p>
            <p><strong>Luminosité:</strong> ${brightness}</p>
            <p><strong>Puissance (FRP):</strong> ${frp}</p>
          </div>
        `
        layer.bindPopup(popupContent)
      }
    }).addTo(fireLayerGroup)

  } catch (error) {
    console.error('Erreur lors du chargement des foyers de feux :', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  if (!mapContainer.value) return

  // 1. Initialisation de la carte
  mapInstance = L.map(mapContainer.value, {
    zoomControl: true,
    attributionControl: false
  })

  // Cadrage automatique sur la zone COFAV
  mapInstance.fitBounds(COFAV_BOUNDS, { padding: [10, 10] })

  // 2. Couche Satellite (Esri World Imagery)
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 18,
  }).addTo(mapInstance)

  // 3. Trace du polygone COFAV
  L.polygon(COFAV_POLYGON, {
    color: '#10b981',
    weight: 2,
    dashArray: '6, 6',
    fillColor: '#059669',
    fillOpacity: 0.2
  }).addTo(mapInstance)

  // 4. Ajout des labels des villes
  COFAV_CITIES.forEach((city) => {
    if (!mapInstance) return

    const cityIcon = L.divIcon({
      className: 'custom-city-label',
      html: `
        <div style="display: flex; align-items: center; gap: 4px; whitespace: nowrap;">
          <div style="width: 6px; height: 6px; background-color: #ffffff; border-radius: 50%; border: 1px solid #000;"></div>
          <span style="color: #ffffff; font-size: 11px; font-weight: 600; text-shadow: 1px 1px 2px #000, -1px -1px 2px #000, 1px -1px 2px #000, -1px 1px 2px #000;">
            ${city.name}
          </span>
        </div>
      `,
      iconSize: [100, 20],
      iconAnchor: [0, 10]
    })

    L.marker([city.lat, city.lng], { icon: cityIcon, interactive: false }).addTo(mapInstance)
  })

  // 5. Chargement dynamique des feux récents
  await loadFireData()
})

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<style>
/* Style pour éviter tout encadrement par défaut de Leaflet DivIcon */
.custom-city-label {
  background: transparent !important;
  border: none !important;
}
</style>