<template>
  <div>
    <div class="flex items-center justify-between mb-2">
      <span
        class="px-2 py-0.5 rounded-full text-[10px] font-bold border"
        :class="badgeClass"
      >
        {{ label }}
      </span>
      <span class="text-[10px] text-slate-400">Page {{ page }}/{{ totalPages }}</span>
    </div>

    <table class="w-full text-left text-xs">
      <thead>
        <tr class="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
          <th class="pb-2 pl-1">Date</th>
          <th class="pb-2">Région</th>
          <th class="pb-2">Superficie</th>
          <th class="pb-2 pr-1 text-right">Carbone</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-50 text-slate-700 font-medium">
        <tr v-for="event in pageEvents" :key="event.id" class="hover:bg-slate-50/80">
          <td class="py-2 pl-1 text-slate-500 font-mono">{{ event.period_start }}</td>
          <td class="py-2 font-semibold text-slate-800">{{ event.region }}</td>
          <td class="py-2">{{ event.area_hectares.toFixed(1) }}ha</td>
          <td class="py-2 pr-1 text-right font-bold text-slate-900">{{ event.carbon_tons_estimate.toFixed(0) }}tC</td>
        </tr>
      </tbody>
    </table>

    <div class="flex justify-end gap-2 mt-2">
      <button
        type="button"
        class="px-2 py-1 text-[10px] font-semibold rounded-lg border border-slate-200 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-50"
        :disabled="page <= 1"
        @click="$emit('prev')"
      >
        ← Précédent
      </button>
      <button
        type="button"
        class="px-2 py-1 text-[10px] font-semibold rounded-lg border border-slate-200 text-slate-500 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-50"
        :disabled="page >= totalPages"
        @click="$emit('next')"
      >
        Suivant →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { BurnedArea } from '@/services/carbonService'

const props = defineProps<{
  label: string
  badgeClass: string
  events: BurnedArea[]
  page: number
  pageSize: number
}>()

defineEmits<{
  (e: 'next'): void
  (e: 'prev'): void
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.events.length / props.pageSize)))

const pageEvents = computed(() => {
  const start = (props.page - 1) * props.pageSize
  return props.events.slice(start, start + props.pageSize)
})
</script>
