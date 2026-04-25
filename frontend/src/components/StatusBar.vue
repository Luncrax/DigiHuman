<template>
  <div class="fixed inset-x-0 bottom-0 z-40 px-4 pb-4">
    <div class="panel mx-auto flex w-full max-w-[1280px] flex-col gap-3 rounded-[26px] px-4 py-3 md:flex-row md:items-center md:justify-between md:px-5">
      <div class="flex flex-wrap items-center gap-3">
        <div class="status-chip">
          <span class="status-dot" :class="overallStatus"></span>
          <span>系统状态 {{ overallStatusText }}</span>
        </div>
        <div v-for="service in compactServices" :key="service.key" class="status-chip">
          <span class="status-dot" :class="service.status"></span>
          <span>{{ service.label }}</span>
        </div>
      </div>

      <div class="flex items-center gap-2 self-end md:self-auto">
        <span class="hidden text-sm text-[var(--muted)] lg:inline">
          {{ statusMessage }}
        </span>
        <button class="action-btn secondary" type="button" :disabled="healthLoading" @click="fetchHealthDetail">
          {{ healthLoading ? '刷新中...' : '刷新状态' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useHealthDetail } from '../composables/useHealthDetail'

const {
  healthError,
  healthLoading,
  lastUpdated,
  sortedServices,
  overallStatus,
  overallStatusText,
  fetchHealthDetail,
} = useHealthDetail()

const compactServices = computed(() => sortedServices.value.slice(0, 4))

const statusMessage = computed(() => {
  if (healthError.value) return `状态检查失败：${healthError.value}`
  if (!lastUpdated.value) return '等待首次状态检查'
  return `上次刷新 ${lastUpdated.value.toLocaleTimeString()}`
})

onMounted(() => {
  if (!lastUpdated.value && !healthLoading.value) {
    fetchHealthDetail()
  }
})
</script>
