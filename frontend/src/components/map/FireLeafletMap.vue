<template>
  <div class="relative w-full h-112.5 rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
    <div ref="mapContainer" class="w-full h-full z-0"></div>

    <div
      v-if="isLoading"
      class="absolute bottom-4 left-4 z-10 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/50 flex items-center gap-2 text-xs text-slate-300"
    >
      <span class="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
      <span>Mise à jour des feux récents...</span>
    </div>

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

const FIRE_REFRESH_INTERVAL_MS = 60_000

const mapContainer = ref<HTMLElement | null>(null)
const isLoading = ref(false)
const fireCount = ref(0)

let mapInstance: L.Map | null = null
let fireLayerGroup: L.LayerGroup | null = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const formatSatellite = (satellite?: string): string => {
  const labels: Record<string, string> = {
    VIIRS_SNPP_NRT: 'VIIRS — Suomi-NPP',
    VIIRS_NOAA20_NRT: 'VIIRS — NOAA-20',
    VIIRS_NOAA21_NRT: 'VIIRS — NOAA-21',
  }

  return labels[satellite ?? ''] ?? satellite ?? 'VIIRS — non précisé'
}

const formatTime = (acqTime?: string): string => {
  if (!acqTime) return 'N/A'

  const normalized = acqTime.padStart(4, '0')

  return `${normalized.slice(0, 2)}:${normalized.slice(2, 4)} UTC`
}

const loadFireData = async () => {
  if (!mapInstance) return

  isLoading.value = true

  try {
    const geojsonData = await fetchRecentFires(7)

    if (fireLayerGroup) {
      fireLayerGroup.clearLayers()
    } else {
      fireLayerGroup = L.layerGroup().addTo(mapInstance)
    }

    fireCount.value = geojsonData.features?.length ?? 0

    L.geoJSON(geojsonData, {
      pointToLayer: (_feature, latlng) =>
        L.circleMarker(latlng, {
          radius: 7,
          fillColor: '#f97316',
          color: '#ef4444',
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.85,
        }),
      onEachFeature: (feature, layer) => {
        const props = feature.properties || {}
        const date = props.acq_date || 'N/A'
        const time = formatTime(props.acq_time)
        const brightness = props.brightness !== undefined && props.brightness !== null
          ? `${Number(props.brightness).toFixed(2)} K`
          : 'N/A'
        const frp = props.frp !== undefined && props.frp !== null
          ? `${Number(props.frp).toFixed(2)} MW`
          : 'N/A'
        const satellite = formatSatellite(props.satellite)

        layer.bindPopup(`
          <div class="text-xs font-sans text-slate-800 p-1">
            <h4 class="font-bold text-orange-600 mb-1">🔥 Détection de feu</h4>
            <p><strong>Source :</strong> NASA FIRMS</p>
            <p><strong>Satellite :</strong> ${satellite}</p>
            <p><strong>Date :</strong> ${date} ${time}</p>
            <p><strong>Luminosité :</strong> ${brightness}</p>
            <p><strong>Puissance (FRP) :</strong> ${frp}</p>
          </div>
        `)
      },
    }).addTo(fireLayerGroup)
  } catch (error) {
    console.error('Erreur lors du chargement des foyers de feux :', error)
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  if (!mapContainer.value) return

  mapInstance = L.map(mapContainer.value, {
    zoomControl: true,
    attributionControl: false,
  })

  mapInstance.fitBounds(COFAV_BOUNDS, { padding: [10, 10] })

  L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 18 },
  ).addTo(mapInstance)

  L.polygon(COFAV_POLYGON, {
    color: '#10b981',
    weight: 2,
    dashArray: '6, 6',
    fillColor: '#059669',
    fillOpacity: 0.2,
  }).addTo(mapInstance)

  COFAV_CITIES.forEach((city) => {
    if (!mapInstance) return

    const cityIcon = L.divIcon({
      className: 'custom-city-label',
      html: `
        <div style="display:flex;align-items:center;gap:4px;white-space:nowrap;">
          <div style="width:6px;height:6px;background:#fff;border-radius:50%;border:1px solid #000;"></div>
          <span style="color:#fff;font-size:11px;font-weight:600;text-shadow:1px 1px 2px #000,-1px -1px 2px #000,1px -1px 2px #000,-1px 1px 2px #000;">
            ${city.name}
          </span>
        </div>
      `,
      iconSize: [100, 20],
      iconAnchor: [0, 10],
    })

    L.marker([city.lat, city.lng], {
      icon: cityIcon,
      interactive: false,
    }).addTo(mapInstance)
  })

  await loadFireData()

  refreshTimer = setInterval(() => {
    void loadFireData()
  }, FIRE_REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }

  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }

  fireLayerGroup = null
})
</script>

<style>
.custom-city-label {
  background: transparent !important;
  border: none !important;
}
</style>