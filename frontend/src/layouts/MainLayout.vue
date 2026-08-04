<template>
  <div class="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans antialiased text-slate-600">
    <!-- Sidebar (Gauche) -->
    <AppSidebar />

    <!-- Conteneur Principal (Droite) -->
    <div class="flex flex-col flex-1 h-full overflow-hidden">
      <!-- Header (Haut) -->
      <AppHeader />

      <!-- Zone de contenu dynamique -->
      <main class="flex-1 overflow-y-auto p-8">
        <div class="max-w-7xl mx-auto space-y-6">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppHeader from '@/components/common/AppHeader.vue'
</script>