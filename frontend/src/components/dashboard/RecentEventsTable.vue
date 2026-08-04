<template>
  <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between h-full">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-xs font-bold text-slate-800 uppercase tracking-wider">
        Derniers événements détectés
      </h3>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead>
          <tr class="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
            <th class="pb-3 pl-1">Timestamp</th>
            <th class="pb-3">Région</th>
            <th class="pb-3">Type</th>
            <th class="pb-3">Superficie</th>
            <th class="pb-3 pr-1 text-right">Carbon</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-50 text-slate-700 font-medium">
          <tr
            v-for="event in events"
            :key="event.id"
            class="hover:bg-slate-50/80 transition-colors"
          >
            <td class="py-3 pl-1 text-slate-500 font-mono">{{ event.timestamp }}</td>
            <td class="py-3 font-semibold text-slate-800">{{ event.region }}</td>
            <td class="py-3">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                {{ event.type }}
              </span>
            </td>
            <td class="py-3">{{ event.surface }}</td>
            <td class="py-3 pr-1 text-right font-bold text-slate-900">{{ event.carbon }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface FireEvent {
  id: string
  timestamp: string
  region: string
  type: string
  surface: string
  carbon: string
}

const events = ref<FireEvent[]>([
  {
    id: '1',
    timestamp: '2026-07-25 14:15',
    region: 'Haute Matsiatra',
    type: 'Brousse',
    surface: '18ha',
    carbon: '145t'
  },
  {
    id: '2',
    timestamp: '2026-07-25 12:40',
    region: 'Amoron\'i Mania',
    type: 'Forêt basse',
    surface: '24ha',
    carbon: '210t'
  },
  {
    id: '3',
    timestamp: '2026-07-25 09:10',
    region: 'Ihorombe',
    type: 'Savane',
    surface: '42ha',
    carbon: '180t'
  },
  {
    id: '4',
    timestamp: '2026-07-24 22:05',
    region: 'Vatovavy',
    type: 'Brousse',
    surface: '12ha',
    carbon: '95t'
  }
])
</script>