<template>
  <div class="space-y-6">
    <!-- Cartes de statistiques -->
    <div
      v-if="statsError"
      class="bg-red-50 border border-red-200 text-red-600 text-xs font-medium rounded-2xl p-4"
    >
      {{ statsError }}
    </div>

    <div
      v-else-if="isStatsLoading"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      <div
        v-for="n in 4"
        :key="n"
        class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 h-24 animate-pulse"
      ></div>
    </div>

    <div
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      <StatCard
        v-for="stat in stats"
        :key="stat.id"
        :label="stat.label"
        :value="stat.value"
        :unit="stat.unit"
        :subtitle="stat.subtitle"
        :icon="stat.icon"
        :icon-color="stat.iconColor"
        :icon-bg="stat.iconBg"
        :trend="stat.trend"
      />
    </div>

    <!-- Carte avec animation d’introduction -->
    <div
      class="relative w-full rounded-2xl overflow-hidden shadow-sm border border-slate-100 bg-slate-900"
    >
      <Transition
        mode="out-in"
        enter-active-class="transition-opacity duration-500 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-500 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <GlobeIntro
          v-if="showIntro"
          key="globe"
          @finish="handleIntroFinish"
        />

        <FireLeafletMap
          v-else
          key="map"
        />
      </Transition>
    </div>

    <!-- Graphique sur 7 jours et tableau des événements -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <FiresTrendChart
        :trend="fireTrend"
        :loading="isStatsLoading"
        :error="statsError"
      />

      <RecentEventsTable />
    </div>

    <!-- Attribution des données -->
    <footer
      class="pt-2 text-center text-xs text-slate-400 font-medium"
    >
      Source données:
      <span class="text-slate-600 font-semibold">
        NASA FIRMS API
      </span>
      | © 2026 ENV-WATCH Madagascar
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import GlobeIntro from '@/components/common/GlobeIntro.vue'
import FireLeafletMap from '@/components/map/FireLeafletMap.vue'
import FiresTrendChart from '@/components/charts/FiresTrendChart.vue'
import RecentEventsTable from '@/components/dashboard/RecentEventsTable.vue'
import { useDashboardStats } from '@/composables/useDashboardStats'

const {
  stats,
  fireTrend,
  isLoading: isStatsLoading,
  error: statsError,
} = useDashboardStats()

const showIntro = ref(true)

const handleIntroFinish = () => {
  showIntro.value = false
}
</script>