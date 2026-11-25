<template>
  <div
    class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm flex flex-col h-full"
  >
    <div class="mb-4">
      <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">
        Évolution des feux (J−30 à aujourd’hui)
      </h3>

      <p class="mt-1 text-xs text-slate-400">
        Toutes sources — détections et analyses enregistrées par jour
      </p>

      <div class="flex flex-wrap items-center gap-4 mt-3 text-[10px] text-slate-500">
        <span class="inline-flex items-center gap-1.5">
          <span
            class="w-2 h-2 rounded-full bg-red-600"
            aria-hidden="true"
          ></span>
          Feux détecté 
        </span>

        <span class="inline-flex items-center gap-1.5">
          <span
            class="w-2 h-2 rounded-full bg-emerald-600"
            aria-hidden="true"
          ></span>
          Rien Feux
        </span>
      </div>
    </div>

    <div
      v-if="loading || isHistoryLoading"
      class="h-80 flex items-center justify-center text-sm text-slate-500"
      role="status"
    >
      Chargement des données…
    </div>

    <div
      v-else-if="error || historyError"
      class="h-80 flex items-center justify-center text-center text-sm text-red-600"
      role="alert"
    >
      {{ error || historyError }}
    </div>

    <div
      v-else-if="!hasValidFireData"
      class="h-80 flex items-center justify-center text-center text-sm text-amber-700"
    >
      La série des détections doit contenir 31 valeurs.
      Vérifiez que le backend actualisé est démarré.
    </div>

    <div v-else class="relative w-full h-80">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { fetchCarbonHistory } from '@/services/carbonService'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
)

const props = withDefaults(
  defineProps<{
    trend: number[]
    loading?: boolean
    error?: string | null
  }>(),
  {
    loading: false,
    error: null,
  },
)

interface AnalysisRecord {
  id: number | string
  source: string
  date: string
}

const PERIOD_DAYS = 31
const REFRESH_INTERVAL_MS = 60_000

const LINE_COLOR = '#0284c7'
const ACTIVE_POINT_COLOR = '#dc2626'
const ZERO_POINT_COLOR = '#059669'

const analysisRecords = ref<AnalysisRecord[]>([])
const isHistoryLoading = ref(true)
const historyError = ref<string | null>(null)
const referenceDate = ref(new Date())

let refreshTimer: ReturnType<typeof setInterval> | null = null
let requestInProgress = false
let disposed = false

const toDateKey = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

const periodDates = computed(() => {
  const today = referenceDate.value

  return Array.from({ length: PERIOD_DAYS }, (_, index) => {
    const date = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
    )

    date.setDate(date.getDate() - 30 + index)

    return toDateKey(date)
  })
})

const labels = Array.from(
  { length: PERIOD_DAYS },
  (_, index) => {
    const daysAgo = 30 - index

    if (daysAgo === 0) return 'Aujourd’hui'
    if (daysAgo === 1) return 'Hier'

    return `J-${daysAgo}`
  },
)

const formatDate = (value: string): string => {
  const parts = value.split('-')

  if (parts.length !== 3) return value

  return `${parts[2]}/${parts[1]}/${parts[0]}`
}

const hasValidFireData = computed(
  () =>
    props.trend.length === PERIOD_DAYS &&
    props.trend.every(
      (value) => Number.isInteger(value) && value >= 0,
    ),
)

const analysesByDay = computed(() => {
  const counts = new Map<string, number>()

  for (const record of analysisRecords.value) {
    counts.set(
      record.date,
      (counts.get(record.date) ?? 0) + 1,
    )
  }

  return counts
})

const combinedTrend = computed(() =>
  periodDates.value.map((date, index) => {
    const detections = props.trend[index] ?? 0
    const analyses = analysesByDay.value.get(date) ?? 0

    return detections + analyses
  }),
)

const pointColors = computed(() =>
  combinedTrend.value.map((value) =>
    value > 0 ? ACTIVE_POINT_COLOR : ZERO_POINT_COLOR,
  ),
)

const chartData = computed<ChartData<'line'>>(() => ({
  labels,
  datasets: [
    {
      label: 'Enregistrements toutes sources',
      data: combinedTrend.value,
      borderColor: LINE_COLOR,
      backgroundColor: LINE_COLOR,
      borderWidth: 2,
      tension: 0,
      fill: false,

      pointBackgroundColor: pointColors.value,
      pointBorderColor: pointColors.value,
      pointHoverBackgroundColor: pointColors.value,
      pointHoverBorderColor: pointColors.value,

      pointRadius: 3,
      pointBorderWidth: 1,
      pointHoverRadius: 6,
      pointHoverBorderWidth: 2,
      pointHitRadius: 8,
    },
  ],
}))

const chartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      callbacks: {
        title: (items) => {
          const index = items[0]?.dataIndex

          if (index === undefined) return ''

          return formatDate(periodDates.value[index] ?? '')
        },
        afterBody: (items) => {
          const index = items[0]?.dataIndex

          if (index === undefined) return []

          const date = periodDates.value[index]

          if (!date) return []

          const detections = props.trend[index] ?? 0
          const records = analysisRecords.value.filter(
            (record) => record.date === date,
          )

          const countsBySource = new Map<string, number>()

          for (const record of records) {
            countsBySource.set(
              record.source,
              (countsBySource.get(record.source) ?? 0) + 1,
            )
          }

          const details = [
            `Détections FIRMS : ${detections}`,
          ]

          for (const [source, count] of countsBySource) {
            const displaySource =
              source === 'sentinel2'
                ? 'Sentinel-2'
                : source === 'modis'
                  ? 'MODIS'
                  : source || 'Source non précisée'

            details.push(`Analyses ${displaySource} : ${count}`)
          }

          return details
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        autoSkip: true,
        maxTicksLimit: 8,
        minRotation: 0,
        maxRotation: 45,
        font: {
          size: 10,
        },
      },
    },
    y: {
      beginAtZero: true,
      suggestedMax: 10,
      title: {
        display: true,
        text: 'Nombre d’enregistrements',
      },
      ticks: {
        precision: 0,
        font: {
          size: 10,
        },
      },
      grid: {
        color: '#f1f5f9',
      },
    },
  },
}

const loadHistory = async (showLoading = false) => {
  if (requestInProgress || disposed) return

  requestInProgress = true

  if (showLoading) {
    isHistoryLoading.value = true
  }

  try {
    const history = await fetchCarbonHistory(365)

    if (disposed) return

    const uniqueRecords = new Map<string, AnalysisRecord>()

    for (const item of history) {
      const date = item.period_start.slice(0, 10)

      if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        throw new Error(
          `Date d’analyse invalide pour l’enregistrement ${item.id}`,
        )
      }

      uniqueRecords.set(String(item.id), {
        id: item.id,
        source: item.source,
        date,
      })
    }

    analysisRecords.value = [...uniqueRecords.values()]
    referenceDate.value = new Date()
    historyError.value = null
  } catch (err) {
    if (!disposed) {
      historyError.value =
        'Impossible de charger les analyses : le total toutes sources ne peut pas être affiché.'
    }

    console.error('Chargement du graphique toutes sources :', err)
  } finally {
    requestInProgress = false

    if (!disposed) {
      isHistoryLoading.value = false
    }
  }
}

onMounted(() => {
  void loadHistory(true)

  refreshTimer = setInterval(() => {
    void loadHistory()
  }, REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  disposed = true

  if (refreshTimer !== null) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>