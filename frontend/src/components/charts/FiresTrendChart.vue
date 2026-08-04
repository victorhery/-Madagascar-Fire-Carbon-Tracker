<template>
  <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between h-full">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">
        Évolution des feux (12 jours)
      </h3>
    </div>

    <div class="relative w-full h-56">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
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
  type ChartOptions
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const chartData: ChartData<'line'> = {
  labels: ['J-11', 'J-10', 'J-9', 'J-8', 'J-7', 'J-6', 'J-5', 'J-4', 'J-3', 'J-2', 'J-1', 'Aujourd\'hui'],
  datasets: [
    {
      label: 'Detections',
      data: [10, 20, 38, 35, 12, 28, 30, 48, 42, 38, 45, 52],
      borderColor: '#0284c7', // Sky-600
      backgroundColor: '#0284c7',
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6
    },
    {
      label: 'Totals',
      data: [5, 6, 18, 10, 5, 18, 18, 35, 30, 32, 40, 48],
      borderColor: '#ea580c', // Orange-600
      backgroundColor: '#ea580c',
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 6
    }
  ]
}

const chartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      align: 'end',
      labels: {
        usePointStyle: true,
        boxWidth: 8,
        font: {
          size: 11,
          weight: 'bold'
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: {
          size: 10
        }
      }
    },
    y: {
      min: 0,
      max: 60,
      ticks: {
        stepSize: 20,
        font: {
          size: 10
        }
      },
      grid: {
        color: '#f1f5f9'
      }
    }
  }
}
</script>