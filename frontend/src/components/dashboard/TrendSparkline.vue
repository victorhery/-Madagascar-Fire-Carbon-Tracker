<template>
  <svg :width="width" :height="height" viewBox="0 0 100 30" preserveAspectRatio="none">
    <polyline
      :points="points"
      fill="none"
      :stroke="color"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  data: number[]
  color?: string
  width?: number
  height?: number
}>(), {
  color: '#ea580c',
  width: 64,
  height: 24,
})

const points = computed(() => {
  const min = Math.min(...props.data)
  const max = Math.max(...props.data)
  const range = max - min || 1
  const step = 100 / (props.data.length - 1)
  return props.data
    .map((val, i) => `${i * step},${30 - ((val - min) / range) * 30}`)
    .join(' ')
})
</script>