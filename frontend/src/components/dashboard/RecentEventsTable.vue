<template>
  <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between h-full">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">
        Historique des feux et analyses
      </h3>

      <span v-if="events.length > 0" class="text-[10px] text-slate-400">
        Page {{ currentPage }}/{{ totalPages }}
      </span>
    </div>

    <div v-if="isLoading" class="text-xs text-slate-400 py-6 text-center">
      Chargement...
    </div>

    <template v-else>
      <div v-if="loadError" class="text-xs text-red-500 mb-3">
        {{ loadError }}
      </div>

      <div v-if="events.length === 0" class="text-xs text-slate-400 py-6 text-center">
        Aucune donnée disponible.
      </div>

      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                <th class="pb-2 pl-1">Source</th>
                <th class="pb-2">Date / heure</th>
                <th class="pb-2">Localisation</th>
                <th class="pb-2">État</th>
                <th class="pb-2">Superficie</th>
                <th class="pb-2 pr-1 text-right">Carbone</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-50 text-slate-700 font-medium">
              <tr
                v-for="event in pageEvents"
                :key="event.key"
                class="hover:bg-slate-50/80"
              >
                <td class="py-2 pl-1 pr-2">
                  <span
                    class="inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold border whitespace-nowrap"
                    :class="sourceBadgeClass(event.source)"
                  >
                    {{ event.sourceLabel }}
                  </span>

                  <div
                    v-if="event.satellite"
                    class="text-[10px] text-slate-500 mt-1"
                  >
                    {{ event.satellite }}
                  </div>
                </td>

                <td class="py-2 pr-2 text-slate-500 font-mono whitespace-nowrap">
                  <div>{{ event.date }}</div>
                  <div v-if="event.time" class="text-[10px]">
                    {{ event.time }}
                  </div>
                </td>

                <td class="py-2 pr-2 text-slate-800">
                  {{ event.location }}
                </td>

                <td class="py-2 pr-2">
                  <div
                    :class="event.source === 'firms' ? 'text-amber-700' : 'text-emerald-700'"
                  >
                    {{ event.status }}
                  </div>
                  <div
                    v-if="event.frp !== null"
                    class="text-[10px] text-slate-500 mt-1"
                  >
                    FRP : {{ event.frp.toFixed(2) }} MW
                  </div>
                </td>

                <td class="py-2 pr-2 whitespace-nowrap">
                  {{
                    event.area === null
                      ? '—'
                      : `${event.area.toFixed(1)} ha`
                  }}
                </td>

                <td class="py-2 pr-1 text-right font-bold text-slate-900 whitespace-nowrap">
                  {{
                    event.carbon === null
                      ? '—'
                      : `${event.carbon.toFixed(0)} tC`
                  }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="text-[10px] text-slate-400 mt-3">
          FIRMS : détections des 7 derniers jours. Analyses : 365 derniers jours.
          Les analyses régionales ne sont pas encore associées aux points FIRMS.
        </p>

        <div
          v-if="totalPages > 1"
          class="flex items-center justify-end gap-1 mt-4"
        >
          <button
            type="button"
            class="h-7 px-2 text-[10px] font-bold rounded-lg border border-slate-200 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-50"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            ←
          </button>

          <button
            v-for="page in visiblePages"
            :key="page"
            type="button"
            class="min-w-7 h-7 px-2 text-[10px] font-bold rounded-lg border transition-colors"
            :class="
              page === currentPage
                ? 'bg-emerald-600 border-emerald-600 text-white'
                : 'border-slate-200 text-slate-500 hover:bg-slate-50'
            "
            @click="currentPage = page"
          >
            {{ page }}
          </button>

          <button
            type="button"
            class="h-7 px-2 text-[10px] font-bold rounded-lg border border-slate-200 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-50"
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            →
          </button>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { fetchCarbonHistory } from '@/services/carbonService'
import { fetchRecentFires } from '@/services/fireService'

interface HistoryEvent {
  key: string
  source: string
  sourceLabel: string
  satellite: string | null
  date: string
  time: string | null
  sortDate: string
  location: string
  status: string
  area: number | null
  carbon: number | null
  frp: number | null
}

const PAGE_SIZE = 4
const MAX_VISIBLE_PAGES = 10
const HISTORY_REFRESH_INTERVAL_MS = 60_000

const analysisEvents = ref<HistoryEvent[]>([])
const fireEvents = ref<HistoryEvent[]>([])
const isLoading = ref(true)
const loadError = ref<string | null>(null)
const currentPage = ref(1)

let refreshTimer: ReturnType<typeof setInterval> | null = null
let requestInProgress = false
let disposed = false

const events = computed(() =>
  [...fireEvents.value, ...analysisEvents.value].sort(
    (left, right) =>
      right.sortDate.localeCompare(left.sortDate) ||
      left.key.localeCompare(right.key),
  ),
)

const totalPages = computed(() =>
  Math.max(1, Math.ceil(events.value.length / PAGE_SIZE)),
)

const pageEvents = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return events.value.slice(start, start + PAGE_SIZE)
})

const visiblePages = computed(() => {
  const groupStart =
    Math.floor((currentPage.value - 1) / MAX_VISIBLE_PAGES) *
      MAX_VISIBLE_PAGES +
    1

  const groupEnd = Math.min(
    groupStart + MAX_VISIBLE_PAGES - 1,
    totalPages.value,
  )

  return Array.from(
    { length: groupEnd - groupStart + 1 },
    (_, index) => groupStart + index,
  )
})

const sourceLabel = (source: string): string => {
  if (source === 'sentinel2') return 'Sentinel-2'
  if (source === 'modis') return 'MODIS'
  return source
}

const sourceBadgeClass = (source: string): string => {
  if (source === 'firms') {
    return 'bg-orange-50 text-orange-700 border-orange-200'
  }
  if (source === 'sentinel2') {
    return 'bg-sky-50 text-sky-700 border-sky-200'
  }
  if (source === 'modis') {
    return 'bg-amber-50 text-amber-700 border-amber-200'
  }
  return 'bg-slate-50 text-slate-600 border-slate-200'
}

const satelliteLabel = (satellite?: string): string => {
  const labels: Record<string, string> = {
    VIIRS_SNPP_NRT: 'VIIRS — Suomi-NPP',
    VIIRS_NOAA20_NRT: 'VIIRS — NOAA-20',
    VIIRS_NOAA21_NRT: 'VIIRS — NOAA-21',
  }

  return satellite
    ? labels[satellite] ?? satellite
    : 'Satellite non précisé'
}

const normalizedTime = (value?: string): string | null => {
  if (!value) return null

  const raw = String(value).padStart(4, '0')
  if (!/^\d{4}$/.test(raw)) return null

  const hours = Number(raw.slice(0, 2))
  const minutes = Number(raw.slice(2, 4))

  if (hours > 23 || minutes > 59) return null

  return `${raw.slice(0, 2)}:${raw.slice(2, 4)}`
}

const loadHistory = async (showLoading = false) => {
  if (requestInProgress || disposed) return

  requestInProgress = true
  if (showLoading) isLoading.value = true

  try {
    const [carbonResult, firesResult] = await Promise.allSettled([
      fetchCarbonHistory(365),
      fetchRecentFires(7),
    ])

    if (disposed) return

    const errors: string[] = []

    if (carbonResult.status === 'fulfilled') {
      analysisEvents.value = carbonResult.value.map((item) => ({
        key: `analysis-${item.id}`,
        source: item.source,
        sourceLabel: sourceLabel(item.source),
        satellite: null,
        date: item.period_start,
        time: null,
        sortDate: `${item.period_start}T00:00:00Z`,
        location: item.region,
        status: 'Estimation régionale',
        area: item.area_hectares,
        carbon: item.carbon_tons_estimate,
        frp: null,
      }))
    } else {
      errors.push('Historique des estimations indisponible.')
      console.error('Erreur historique carbone :', carbonResult.reason)
    }

    if (firesResult.status === 'fulfilled') {
      const uniqueEvents = new Map<string, HistoryEvent>()

      for (const feature of firesResult.value.features) {
        const props = feature.properties
        const [longitude, latitude] = feature.geometry.coordinates
        const time = normalizedTime(props.acq_time)
        const date = props.acq_date ?? ''
        const satellite = props.satellite ?? ''

        const key = [
          'firms',
          satellite,
          date,
          props.acq_time ?? '',
          latitude,
          longitude,
        ].join('|')

        const region =
          typeof props.region === 'string' && props.region.trim()
            ? props.region
            : `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`

        uniqueEvents.set(key, {
          key,
          source: 'firms',
          sourceLabel: 'NASA FIRMS',
          satellite: satelliteLabel(satellite),
          date: date || 'Date non précisée',
          time: time ? `${time} UTC` : null,
          sortDate: date ? `${date}T${time ?? '00:00'}:00Z` : '',
          location: region,
          status: 'Surface non associée',
          area: null,
          carbon: null,
          frp: typeof props.frp === 'number' ? props.frp : null,
        })
      }

      fireEvents.value = [...uniqueEvents.values()]
    } else {
      errors.push('Détections FIRMS indisponibles.')
      console.error('Erreur historique FIRMS :', firesResult.reason)
    }

    loadError.value = errors.length > 0
      ? `${errors.join(' ')} Les dernières données chargées sont conservées.`
      : null

    currentPage.value = Math.min(currentPage.value, totalPages.value)
  } finally {
    requestInProgress = false
    if (!disposed) isLoading.value = false
  }
}

onMounted(() => {
  void loadHistory(true)

  refreshTimer = setInterval(() => {
    void loadHistory()
  }, HISTORY_REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  disposed = true

  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>