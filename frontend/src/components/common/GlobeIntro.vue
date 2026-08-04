<template>
  <div class="relative w-full h-full min-h-112.5 bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center">
    <!-- Conteneur 3D Canvas pour Globe.gl -->
    <div ref="globeContainer" class="w-full h-full cursor-grab active:cursor-grabbing"></div>

    <!-- Bouton pour passer l'intro -->
    <button
      type="button"
      @click="finishAnimation"
      class="absolute top-4 right-4 z-10 px-4 py-2 bg-slate-900/80 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg backdrop-blur-md border border-slate-700/50 transition-all shadow-lg cursor-pointer"
    >
      Passer l'intro ➔
    </button>

    <!-- Overlay de texte explicatif -->
    <div class="absolute bottom-6 left-6 z-10 text-white pointer-events-none">
      <p class="text-xs uppercase tracking-widest text-emerald-400 font-bold mb-1">Localisation de la zone</p>
      <h3 class="text-lg font-bold text-slate-100">Zoom sur le Corridor COFAV</h3>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import Globe, { type GlobeInstance } from 'globe.gl'

const emit = defineEmits<{
  (e: 'finish'): void
}>()

const globeContainer = ref<HTMLElement | null>(null)
let globeInstance: GlobeInstance | null = null
let animationTimeout: number | null = null

// Coordonnées cibles : Madagascar / COFAV
const TARGET_LAT = -21.84
const TARGET_LNG = 47.30

const finishAnimation = () => {
  if (animationTimeout !== null) {
    clearTimeout(animationTimeout)
    animationTimeout = null
  }
  emit('finish')
}

onMounted(() => {
  if (!globeContainer.value) return

  // 1. Instanciation du Globe
  globeInstance = new Globe(globeContainer.value)
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
    .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
    .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
    .width(globeContainer.value.clientWidth)
    .height(globeContainer.value.clientHeight)

  // Configuration initiale de la caméra
  globeInstance.pointOfView({ lat: 10, lng: 0, altitude: 2.8 }, 0)

  // 2. Rotation automatique LENTE
  const controls = globeInstance.controls()
  if (controls) {
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.6 // Rotation douce et lente
  }

  // 3. Séquence d'animation
  animationTimeout = window.setTimeout(() => {
    if (!globeInstance) return

    const activeControls = globeInstance.controls()
    if (activeControls) {
      activeControls.autoRotate = false
    }

    // ZOOM TRÈS RAPPROCHÉ sur Madagascar / COFAV
    globeInstance.pointOfView(
      {
        lat: TARGET_LAT,
        lng: TARGET_LNG,
        altitude: 0.18, // Zoom très poussé vers la zone forestière
      },
      3000 // Transition de zoom sur 3 secondes
    )

    // Temps de pause une fois le zoom maximal atteint avant de basculer
    animationTimeout = window.setTimeout(() => {
      finishAnimation()
    }, 4500)
  }, 2000)
})

onBeforeUnmount(() => {
  if (animationTimeout !== null) {
    clearTimeout(animationTimeout)
  }
  if (globeInstance && globeContainer.value) {
    globeContainer.value.replaceChildren()
    globeInstance = null
  }
})
</script>