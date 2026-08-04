<template>
  <div class="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex items-center justify-between">
    <div>
      <p class="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-2">
        {{ label }}
      </p>
      <div class="flex items-baseline gap-1">
        <span class="text-2xl font-bold text-slate-800">{{ value }}</span>
        <span v-if="unit" class="text-sm text-slate-400">{{ unit }}</span>
      </div>
      <p v-if="subtitle" class="text-xs text-slate-400 mt-1">{{ subtitle }}</p>
    </div>
    <div class="flex flex-col items-end gap-2">
      <div class="w-11 h-11 rounded-xl flex items-center justify-center" :style="{ backgroundColor: iconBg }">
        <component :is="icon" class="w-5 h-5" :style="{ color: iconColor }" />
      </div>
      <TrendSparkline v-if="trend?.length" :data="trend" :color="iconColor" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import TrendSparkline from './TrendSparkline.vue'

defineProps<{
  label: string
  value: string | number
  unit?: string
  subtitle?: string
  icon: Component
  iconColor: string
  iconBg: string
  trend?: number[]
}>()
</script>