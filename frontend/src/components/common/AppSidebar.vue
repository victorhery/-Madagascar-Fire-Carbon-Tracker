<template>
  <aside class="w-64 bg-white border-r border-slate-100 flex flex-col h-screen shrink-0">
    <!-- Logo -->
    <div class="p-6 flex items-center gap-3 border-b border-slate-50">
      <div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center">
        <Leaf class="w-6 h-6 text-emerald-600" />
      </div>
      <div>
        <h1 class="font-bold text-slate-800 text-sm leading-tight tracking-wider uppercase">
          Madagascar
        </h1>
        <span class="text-xs font-semibold text-emerald-600 tracking-widest">
          ENV-WATCH
        </span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-4 space-y-1">
      <button 
        v-for="item in menuItems" 
        :key="item.name"
        @click="activeRoute = item.name"
        :class="[
          'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200',
          activeRoute === item.name 
            ? 'bg-blue-50 text-blue-600' 
            : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
        ]"
      >
        <component :is="item.icon" class="w-5 h-5" />
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { ref, type Component } from 'vue'
import { 
  LayoutDashboard, 
  Map, 
  FlameKindling, 
  FileText, 
  Database, 
  Settings,
  Leaf
} from 'lucide-vue-next'

const activeRoute = ref<string>('Dashboard')

interface MenuItem {
  name: string
  label: string
  icon: Component
}

const menuItems: MenuItem[] = [
  { name: 'Dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { name: 'FireMap', label: 'Carte des feux', icon: Map },
  { name: 'Carbon', label: 'Estimation carbone', icon: FlameKindling },
  { name: 'Reports', label: 'Rapports', icon: FileText },
  { name: 'Sources', label: 'Sources de données', icon: Database },
  { name: 'Settings', label: 'Paramètres', icon: Settings },
]
</script>