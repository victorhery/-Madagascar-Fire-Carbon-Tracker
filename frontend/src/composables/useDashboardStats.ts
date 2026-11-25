import { ref, onMounted, onBeforeUnmount } from 'vue'
import {
  Flame,
  TreeDeciduous,
  CloudFog,
  BellRing,
} from 'lucide-vue-next'
import type { StatCardData } from '@/types/dashboard'
import { fetchStatsSummary } from '@/services/statsService'

const DASHBOARD_REFRESH_INTERVAL_MS = 60_000

export function useDashboardStats() {
  const stats = ref<StatCardData[]>([])
  const fireTrend = ref<number[]>([])
  const fireTrendError = ref<string | null>(null)
  const isLoading = ref(true)
  const error = ref<string | null>(null)

  let refreshTimer: ReturnType<typeof setInterval> | null = null
  let requestInProgress = false
  let disposed = false

  const loadStats = async (showLoading = false) => {
    if (requestInProgress || disposed) {
      return
    }

    requestInProgress = true

    if (showLoading) {
      isLoading.value = true
    }

    try {
      const summary = await fetchStatsSummary()

      if (disposed) {
        return
      }

      const dailyTrend = summary.active_fires_trend_31d

      if (
        Array.isArray(dailyTrend) &&
        dailyTrend.length === 31 &&
        dailyTrend.every(
          (value) => Number.isInteger(value) && value >= 0,
        )
      ) {
        fireTrend.value = [...dailyTrend]
        fireTrendError.value = null
      } else {
        fireTrend.value = []
        fireTrendError.value =
          "L’API ne fournit pas la série attendue de 31 jours. Enregistrez les fichiers backend et redémarrez le serveur."
      }

      stats.value = [
        {
          id: 'active-fires',
          label: 'Feux actifs',
          value: summary.active_fires_24h,
          subtitle: 'détections, 24h',
          icon: Flame,
          iconColor: '#ea580c',
          iconBg: '#fff7ed',
          trend: Array.isArray(summary.active_fires_trend_7d)
            ? [...summary.active_fires_trend_7d]
            : [],
        },
        {
          id: 'burned-area',
          label: 'Surface brûlée',
          value: summary.burned_area_hectares_total.toLocaleString(
            'fr-FR',
            {
              maximumFractionDigits: 1,
            },
          ),
          unit: 'hectares',
          subtitle: '',
          icon: TreeDeciduous,
          iconColor: '#065f46',
          iconBg: '#ecfdf5',
          trend: [],
        },
        {
          id: 'carbon',
          label: 'Carbone affecté estimé',
          value: summary.co2_estimate_tons_total.toLocaleString(
            'fr-FR',
            {
              maximumFractionDigits: 1,
            },
          ),
          unit: 'tC',
          subtitle: '',
          icon: CloudFog,
          iconColor: '#334155',
          iconBg: '#f1f5f9',
          trend: [],
        },
        {
          id: 'alerts',
          label: 'Alertes actives',
          value: summary.active_alerts,
          subtitle: 'zones critiques',
          icon: BellRing,
          iconColor: '#d97706',
          iconBg: '#fffbeb',
          trend: [],
        },
      ]

      error.value = null
    } catch (err) {
      if (!disposed) {
        error.value =
          'Impossible de charger ou de traiter les statistiques du dashboard.'
      }

      console.error('Chargement des statistiques :', err)
    } finally {
      requestInProgress = false

      if (!disposed) {
        isLoading.value = false
      }
    }
  }

  onMounted(() => {
    void loadStats(true)

    refreshTimer = setInterval(() => {
      void loadStats()
    }, DASHBOARD_REFRESH_INTERVAL_MS)
  })

  onBeforeUnmount(() => {
    disposed = true

    if (refreshTimer !== null) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  })

  return {
    stats,
    fireTrend,
    fireTrendError,
    isLoading,
    error,
    refresh: loadStats,
  }
}