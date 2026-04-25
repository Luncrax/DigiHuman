<template>
  <div id="app" class="app-shell">
    <div class="shell-grid"></div>
    <div class="grain"></div>
    <NavBar />
    <main class="page-frame">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <Live2DCharacter />
    <StatusBar />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import StatusBar from './components/StatusBar.vue'
import Live2DCharacter from './components/Live2DCharacter.vue'
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
  console.log('DigiHuman App Started')
})
</script>

<style>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
