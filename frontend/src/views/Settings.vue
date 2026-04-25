<template>
  <div class="space-y-8">
    <section class="panel-strong rounded-[36px] p-6 md:p-8">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="eyebrow">Startup Health</div>
          <h1 class="mt-4 section-title text-[var(--text)]">
            启动自检面板
            <span class="block text-[var(--accent)]">一次看清整套虚拟人链路是否在线。</span>
          </h1>
          <p class="mt-5 max-w-3xl text-base leading-7 text-[var(--muted)]">
            这里会直接检查后端的 LLM、Qwen3-TTS、ASR、Live2D 和 WebSocket 模块。你不需要先去聊天页试一次，再回头猜到底是哪一层没有准备好。
          </p>
        </div>

        <div class="flex flex-col items-start gap-3 lg:items-end">
          <div class="status-chip">
            <span class="status-dot" :class="overallStatus"></span>
            <span>总体 {{ overallStatusText }}</span>
          </div>
          <button class="action-btn primary" type="button" :disabled="healthLoading" @click="fetchHealthDetail">
            {{ healthLoading ? '体检中...' : '重新体检' }}
          </button>
        </div>
      </div>

      <div v-if="healthError" class="mt-6 rounded-[24px] border border-[rgba(170,61,49,0.2)] bg-[rgba(170,61,49,0.08)] px-4 py-3 text-sm text-[var(--danger)]">
        {{ healthError }}
      </div>

      <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <div v-for="service in sortedServices" :key="service.key" class="feature-card panel">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-lg font-bold text-[var(--text)]">{{ service.label }}</div>
              <div class="mt-1 text-sm text-[var(--muted)]">{{ service.summary }}</div>
            </div>
            <div class="status-chip">
              <span class="status-dot" :class="service.status"></span>
              <span>{{ service.statusText }}</span>
            </div>
          </div>

          <div v-if="Object.keys(service.details).length" class="mt-4 space-y-2 text-sm">
            <div
              v-for="(value, key) in service.details"
              :key="key"
              class="flex items-start justify-between gap-4 border-t border-[var(--line)] pt-2 text-[var(--muted)]"
            >
              <span>{{ key }}</span>
              <span class="max-w-[60%] break-all text-right text-[var(--text)]">
                {{ formatDetailValue(value) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <div class="panel rounded-[34px] p-6 md:p-7">
        <div class="feature-kicker">Quick Meaning</div>
        <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">看到这些状态时怎么理解</h2>

        <div class="mt-6 space-y-4">
          <div class="feature-card panel-outline">
            <div class="text-lg font-bold text-[var(--text)]">正常</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
              模块已就绪，可以直接参与当前链路，比如 Qwen 可访问、WebSocket 正常、ASR 可用。
            </p>
          </div>
          <div class="feature-card panel-outline">
            <div class="text-lg font-bold text-[var(--text)]">降级</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
              系统还能工作，但不是理想状态。例如 Live2D 前端资源正常、后端本地模型未启用，这时界面会走前端状态机降级模式。
            </p>
          </div>
          <div class="feature-card panel-outline">
            <div class="text-lg font-bold text-[var(--text)]">异常</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
              当前链路中有关键模块不可用，通常意味着你需要回到启动流程检查配置、端口或依赖环境。
            </p>
          </div>
        </div>
      </div>

      <div class="panel-strong rounded-[34px] p-6 md:p-7">
        <div class="feature-kicker">Reserved Controls</div>
        <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">基础配置占位</h2>
        <p class="mt-3 text-sm leading-6 text-[var(--muted)]">
          这一区先保留最小配置面板，方便后续继续把 ASR、Qwen 模式、默认音色和 Live2D 策略逐步搬进来。
        </p>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <label class="feature-card panel-outline block">
            <div class="feature-kicker">ASR</div>
            <div class="mt-2 text-lg font-bold text-[var(--text)]">语音识别模型</div>
            <select v-model="settings.asrModel" class="mt-4 w-full rounded-2xl border border-[var(--line)] bg-white/25 px-4 py-3 text-[var(--text)] outline-none">
              <option value="whisper-tiny">Whisper Tiny</option>
              <option value="whisper-base">Whisper Base</option>
              <option value="whisper-medium">Whisper Medium</option>
            </select>
          </label>

          <label class="feature-card panel-outline block">
            <div class="feature-kicker">TTS</div>
            <div class="mt-2 text-lg font-bold text-[var(--text)]">默认语音模式</div>
            <select v-model="settings.ttsMode" class="mt-4 w-full rounded-2xl border border-[var(--line)] bg-white/25 px-4 py-3 text-[var(--text)] outline-none">
              <option value="custom_voice">Custom Voice</option>
              <option value="voice_design">Voice Design</option>
              <option value="base">Base</option>
            </select>
          </label>
        </div>

        <div class="mt-6 flex flex-wrap gap-3">
          <button class="action-btn primary" type="button" @click="saveSettings">保存占位配置</button>
          <router-link to="/chat" class="action-btn secondary no-underline">去聊天页联调</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useHealthDetail } from '../composables/useHealthDetail'

const {
  healthError,
  healthLoading,
  sortedServices,
  overallStatus,
  overallStatusText,
  fetchHealthDetail,
} = useHealthDetail()

const settings = reactive({
  asrModel: 'whisper-medium',
  ttsMode: 'custom_voice',
})

const formatDetailValue = (value) => {
  if (Array.isArray(value)) return value.join(', ') || '-'
  if (typeof value === 'object' && value !== null) return JSON.stringify(value)
  return String(value)
}

const saveSettings = () => {
  console.log('Saving settings placeholder:', settings)
  ElMessage.success('占位配置已保存，后续可以继续接入真实后端设置接口。')
}

onMounted(() => {
  fetchHealthDetail()
})
</script>
