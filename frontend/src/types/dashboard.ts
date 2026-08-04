import type { Component } from 'vue'

export interface StatCardData {
  id: string
  label: string
  value: string | number
  unit?: string
  subtitle: string
  icon: Component
  iconColor: string
  iconBg: string
  trend: number[]
}