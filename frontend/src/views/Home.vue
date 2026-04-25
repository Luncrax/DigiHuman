<template>
  <div class="space-y-8">
    <section class="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
      <div class="panel-strong rounded-[36px] px-6 py-7 md:px-8 md:py-9">
        <div class="eyebrow">Local Emotion Pipeline</div>
        <div class="mt-5 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div>
            <h1 class="section-title text-[var(--text)]">
              让 AI 不只是开口说话，
              <span class="block text-[var(--accent)]">而是带着情绪出现。</span>
            </h1>
            <p class="mt-5 max-w-2xl text-base leading-7 text-[var(--muted)] md:text-lg">
              这套前端围绕完整链路重做成控制台形态：对话、情绪、Qwen3-TTS、Live2D、嘴型同步和启动自检都能在一套界面里看清楚。
            </p>
            <div class="mt-6 flex flex-wrap gap-3">
              <router-link to="/chat" class="action-btn primary no-underline">
                进入对话控制台
              </router-link>
              <router-link to="/dashboard" class="action-btn secondary no-underline">
                查看运行看板
              </router-link>
            </div>
          </div>

          <div class="grid gap-4">
            <div class="metric-card panel rounded-[30px]">
              <div class="feature-kicker">Current Readiness</div>
              <div class="mt-3 flex items-center gap-3">
                <span class="status-dot" :class="overallStatus"></span>
                <span class="text-lg font-bold text-[var(--text)]">{{ overallStatusText }}</span>
              </div>
              <p class="mt-4 text-sm leading-6 text-[var(--muted)]">
                启动自检会直接检查 LLM、Qwen3-TTS、ASR、Live2D 和 WebSocket，不再需要分散到多个页面里判断。
              </p>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Voice Engine</div>
                <div class="metric-value mt-3 text-[var(--text)]">{{ qwenState }}</div>
                <p class="mt-2 text-sm text-[var(--muted)]">Qwen3-TTS 情绪语音输出状态</p>
              </div>
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Avatar Stage</div>
                <div class="metric-value mt-3 text-[var(--text)]">{{ live2dState }}</div>
                <p class="mt-2 text-sm text-[var(--muted)]">Pixi Live2D 舞台与状态机</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel rounded-[36px] p-6 md:p-7">
        <div class="flex items-center justify-between">
          <div>
            <div class="feature-kicker">Pipeline</div>
            <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">完整功能链路</h2>
          </div>
          <button class="action-btn secondary" type="button" :disabled="healthLoading" @click="fetchHealthDetail">
            {{ healthLoading ? '刷新中...' : '更新状态' }}
          </button>
        </div>

        <div class="mt-6 space-y-3">
          <div v-for="step in pipelineSteps" :key="step.title" class="feature-card panel-outline">
            <div class="flex items-start gap-4">
              <div class="feature-icon shrink-0">
                <el-icon size="24"><component :is="step.icon" /></el-icon>
              </div>
              <div>
                <div class="text-sm font-bold uppercase tracking-[0.12em] text-[var(--muted)]">{{ step.kicker }}</div>
                <div class="mt-1 text-lg font-bold text-[var(--text)]">{{ step.title }}</div>
                <p class="mt-2 text-sm leading-6 text-[var(--muted)]">{{ step.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div class="panel rounded-[34px] p-6 md:p-7">
        <div class="flex items-center justify-between">
          <div>
            <div class="feature-kicker">Quick Access</div>
            <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">核心功能入口</h2>
          </div>
          <router-link to="/settings" class="text-sm font-semibold text-[var(--accent)] no-underline">
            查看自检
          </router-link>
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <router-link
            v-for="feature in featureCards"
            :key="feature.title"
            :to="feature.to"
            class="feature-card panel-outline no-underline"
          >
            <div class="feature-icon">
              <el-icon size="22"><component :is="feature.icon" /></el-icon>
            </div>
            <div class="mt-5 feature-kicker">{{ feature.kicker }}</div>
            <div class="mt-2 text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">{{ feature.title }}</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">{{ feature.description }}</p>
          </router-link>
        </div>
      </div>

      <div class="panel-strong rounded-[34px] p-6 md:p-7">
        <div>
          <div class="feature-kicker">Module Snapshot</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">当前模块状态</h2>
        </div>

        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <div
            v-for="service in sortedServices"
            :key="service.key"
            class="feature-card panel-outline"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="text-lg font-bold text-[var(--text)]">{{ service.label }}</div>
              <div class="status-chip">
                <span class="status-dot" :class="service.status"></span>
                <span>{{ service.statusText }}</span>
              </div>
            </div>
            <p class="mt-3 text-sm leading-6 text-[var(--muted)]">{{ service.summary }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  ChatLineRound,
  Connection,
  DataLine,
  MagicStick,
  Opportunity,
  Service,
  Setting,
} from '@element-plus/icons-vue'
import { computed, onMounted } from 'vue'
import { useHealthDetail } from '../composables/useHealthDetail'

const {
  healthLoading,
  sortedServices,
  overallStatus,
  overallStatusText,
  fetchHealthDetail,
} = useHealthDetail()

const featureCards = [
  {
    to: '/chat',
    kicker: 'Conversation',
    title: '对话控制台',
    description: '统一处理文本对话、语音输入、情绪驱动、TTS 参数和 Live2D 联动，不再拆成多个弱页面。',
    icon: ChatLineRound,
  },
  {
    to: '/dashboard',
    kicker: 'Runtime',
    title: '运行看板',
    description: '集中查看链路健康、自检结果、模块细节和系统能力现状。',
    icon: DataLine,
  },
  {
    to: '/settings',
    kicker: 'Startup Health',
    title: '启动自检',
    description: '在一个页面里确认 LLM、Qwen3-TTS、ASR、Live2D 与 WebSocket 是否准备完成。',
    icon: Setting,
  },
]

const pipelineSteps = [
  {
    kicker: 'Step 1',
    title: '用户输入进入对话链路',
    description: '文字或语音都从 WebSocket 进入后端，再交给统一的对话处理路径。',
    icon: Connection,
  },
  {
    kicker: 'Step 2',
    title: 'LLM 生成内容并做情绪分析',
    description: '保留现有 LLM 情感分析，输出标准化情绪名称和强度，用于后续所有表现层。',
    icon: Opportunity,
  },
  {
    kicker: 'Step 3',
    title: 'Emotion Controller 编排输出',
    description: '把情绪转换成文本增强、Qwen 指令、TTS 参数和 Live2D 参数，不再散落在各模块里。',
    icon: MagicStick,
  },
  {
    kicker: 'Step 4',
    title: 'Qwen3-TTS 和 Live2D 同步表现',
    description: 'Qwen 输出情绪语音，前端用状态机和音频嘴型同步，把情绪真的演出来。',
    icon: Service,
  },
]

const qwenState = computed(() => {
  const service = sortedServices.value.find((item) => item.key === 'qwen_tts')
  return service?.statusText || '未知'
})

const live2dState = computed(() => {
  const service = sortedServices.value.find((item) => item.key === 'live2d')
  return service?.statusText || '未知'
})

onMounted(() => {
  fetchHealthDetail()
})
</script>
