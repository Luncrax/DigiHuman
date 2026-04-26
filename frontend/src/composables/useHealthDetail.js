import { computed, ref } from 'vue'

const healthDetail = ref(null)
const healthLoading = ref(false)
const healthError = ref('')
const lastUpdated = ref(null)

const STATUS_TEXT = {
  healthy: '正常',
  warning: '降级',
  degraded: '异常',
  error: '异常',
  unknown: '未知',
}

const serviceOrder = ['llm', 'qwen_tts', 'tts', 'asr', 'live2d', 'websocket']

const toTagType = (status) => {
  if (status === 'healthy') return 'success'
  if (status === 'warning') return 'warning'
  if (status === 'degraded' || status === 'error') return 'danger'
  return 'info'
}

const getStatusText = (status) => STATUS_TEXT[status] || STATUS_TEXT.unknown

const sortedServices = computed(() => {
  const services = healthDetail.value?.services || {}

  return Object.entries(services)
    .sort(([leftKey], [rightKey]) => {
      const leftIndex = serviceOrder.indexOf(leftKey)
      const rightIndex = serviceOrder.indexOf(rightKey)

      if (leftIndex === -1 && rightIndex === -1) return leftKey.localeCompare(rightKey)
      if (leftIndex === -1) return 1
      if (rightIndex === -1) return -1
      return leftIndex - rightIndex
    })
    .map(([key, service]) => ({
      key,
      label: service.label || key,
      status: service.status || 'unknown',
      statusText: getStatusText(service.status),
      tagType: toTagType(service.status),
      summary: service.summary || '暂无摘要',
      details: service.details || {},
    }))
})

const overallStatus = computed(() => healthDetail.value?.status || 'unknown')
const overallStatusText = computed(() => getStatusText(overallStatus.value))
const overallTagType = computed(() => toTagType(overallStatus.value))

const fetchHealthDetail = async () => {
  healthLoading.value = true
  healthError.value = ''

  try {
    const response = await fetch('/health/detail')

    if (!response.ok) {
      throw new Error(`Health detail request failed: ${response.status}`)
    }

    healthDetail.value = await response.json()
    lastUpdated.value = new Date()
  } catch (error) {
    healthError.value = error.message || '获取健康检查失败'
  } finally {
    healthLoading.value = false
  }
}

export function useHealthDetail() {
  return {
    healthDetail,
    healthLoading,
    healthError,
    lastUpdated,
    sortedServices,
    overallStatus,
    overallStatusText,
    overallTagType,
    fetchHealthDetail,
    getStatusText,
    toTagType,
  }
}
