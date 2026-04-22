<template>
  <div id="app" class="min-h-screen bg-gradient-to-b from-gray-50 to-gray-200 dark:from-gray-900 dark:to-gray-800 text-gray-900 dark:text-white transition-colors duration-300">
    <NavBar />
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
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

onMounted(() => {
  useTheme()
  console.log('DigiHuman App Started')
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
