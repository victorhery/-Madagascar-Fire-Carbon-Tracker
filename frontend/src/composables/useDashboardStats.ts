import { ref, onMounted } from 'vue'
import { Flame, TreeDeciduous, CloudFog, BellRing } from 'lucide-vue-next'
import type { StatCardData } from '@/types/dashboard'

export function useDashboardStats() {
  const stats = ref<StatCardData[]>([])
  const isLoading = ref(true)

  onMounted(async () => {
    // TODO: remplacer par services/dashboardService.ts -> API FastAPI
    stats.value = [
      { id: 'active-fires', label: 'Feux actifs', value: 92, subtitle: 'détections, 24h', icon: Flame, iconColor: '#ea580c', iconBg: '#fff7ed', trend: [20, 35, 28, 40, 55, 48, 60, 92] },
      { id: 'burned-area', label: 'Surface brûlée', value: '1,450', unit: 'hectares', subtitle: '', icon: TreeDeciduous, iconColor: '#065f46', iconBg: '#ecfdf5', trend: [800, 950, 1020, 1150, 1200, 1300, 1400, 1450] },
      { id: 'co2', label: 'Émissions estimées', value: '54.2k', unit: 'tonnes CO2eq', subtitle: '', icon: CloudFog, iconColor: '#334155', iconBg: '#f1f5f9', trend: [30, 34, 38, 42, 45, 48, 51, 54] },
      { id: 'alerts', label: 'Alertes du jour', value: 12, subtitle: 'zones critiques', icon: BellRing, iconColor: '#d97706', iconBg: '#fffbeb', trend: [4, 6, 5, 8, 7, 9, 10, 12] },
    ]
    isLoading.value = false
  })

  return { stats, isLoading }
}