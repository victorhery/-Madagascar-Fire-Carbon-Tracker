<template>
  <header class="h-20 bg-white border-b border-slate-100 px-8 flex items-center justify-between shrink-0">
    <!-- Titre principal -->
    <h2 class="text-lg font-bold text-slate-800 tracking-wide uppercase">
      Dashboard Madagascar : Suivi des feux et du carbone affecté
    </h2>

    <!-- Actions & Profil -->
    <div class="flex items-center gap-6">
      <!-- Barre de recherche -->
      <div class="relative w-72">
        <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Search class="h-4 w-4 text-slate-400" />
        </span>
        <input 
          type="text" 
          placeholder="Rechercher feux, zones..." 
          class="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
        />
      </div>

      <!-- Séparateur -->
      <div class="h-6 w-px bg-slate-200"></div>

      <!-- Utilisateur -->
      <div class="flex items-center gap-3 cursor-pointer group">
        <div class="w-10 h-10 rounded-full bg-blue-900 text-white flex items-center justify-center font-bold text-sm">
          JD
        </div>
        <div class="text-left hidden md:block">
          <p class="text-sm font-semibold text-slate-800 leading-tight group-hover:text-blue-600 transition-colors">
            Jean Dubois
          </p>
          <p class="text-xs text-slate-400">admin</p>
        </div>
        <ChevronDown class="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Search, ChevronDown } from 'lucide-vue-next'
</script>