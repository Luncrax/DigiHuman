<template>
  <div class="space-y-8">
    <section class="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <div class="panel-strong rounded-[34px] p-6 md:p-7">
        <div class="eyebrow">Runtime Overview</div>
        <h1 class="mt-5 section-title text-[var(--text)]">
          运行看板
          <span class="block text-[var(--accent)]">把链路健康与表现状态放在一屏里。</span>
        </h1>
        <p class="mt-5 max-w-2xl text-base leading-7 text-[var(--muted)]">
          这里不是传统系统监控，而是围绕你的虚拟人业务链路：LLM、情绪控制、Qwen 语音、Live2D 舞台和 WebSocket 通讯是否都在同一节奏上工作。
        </p>

        <div class="mt-6 grid gap-4 sm:grid-cols-2">
          <div class="metric-card panel-outline rounded-[24px]">
            <div class="feature-kicker">Overall</div>
            <div class="mt-3 flex items-center gap-3">
              <span class="status-dot" :class="overallStatus"></span>
              <span class="text-2xl font-extrabold tracking-[-0.04em] text-[var(--text)]">{{ overallStatusText }}</span>
            </div>
            <div class="mt-3 text-sm text-[var(--muted)]">当前系统整体就绪程度</div>
          </div>
          <div class="metric-card panel-outline rounded-[24px]">
            <div class="feature-kicker">Services</div>
            <div class="metric-value mt-3 text-[var(--text)]">{{ sortedServices.length }}</div>
            <div class="mt-3 text-sm text-[var(--muted)]">已纳入统一检查的模块数量</div>
          </div>
        </div>
      </div>

      <div class="panel rounded-[34px] p-6 md:p-7">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="feature-kicker">System Summary</div>
            <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">模块状态矩阵</h2>
          </div>
          <button class="action-btn primary" type="button" :disabled="healthLoading" @click="fetchHealthDetail">
            {{ healthLoading ? '刷新中...' : '重新体检' }}
          </button>
        </div>

        <div v-if="healthError" class="mt-5 rounded-[22px] border border-[rgba(170,61,49,0.22)] bg-[rgba(170,61,49,0.08)] px-4 py-3 text-sm text-[var(--danger)]">
          {{ healthError }}
        </div>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <div v-for="service in sortedServices" :key="service.key" class="feature-card panel-outline">
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
      </div>
    </section>

    <section class="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <div class="panel rounded-[34px] p-6 md:p-7">
        <div class="feature-kicker">Runtime Flow</div>
        <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">一轮完整响应怎么走</h2>

        <div class="mt-6 space-y-4">
          <div v-for="item in flowItems" :key="item.title" class="feature-card panel-outline">
            <div class="flex items-start gap-4">
              <div class="feature-icon shrink-0">
                <el-icon size="22"><component :is="item.icon" /></el-icon>
              </div>
              <div>
                <div class="feature-kicker">{{ item.kicker }}</div>
                <div class="mt-1 text-lg font-bold text-[var(--text)]">{{ item.title }}</div>
                <p class="mt-2 text-sm leading-6 text-[var(--muted)]">{{ item.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel-strong rounded-[34px] p-6 md:p-7">
        <div class="feature-kicker">Operator Notes</div>
        <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">当前前端能展示什么</h2>

        <div class="mt-6 space-y-4">
          <div class="feature-card panel-outline">
            <div class="text-lg font-bold text-[var(--text)]">对话与情绪</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
              聊天页会展示文本回复、情绪标签、Live2D 指令、TTS 参数和系统告警，不再只是一段聊天记录。
            </p>
          </div>
          <div class="feature-card panel-outline">
            <div class="text-lg font-bold text-[var(--text)]">语音与嘴型</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
              语音播放时会进入 talk 状态，音频能量会直接驱动嘴型开合，失败时也会优雅降级成基础说话状态。
            </p>
          </div>
          <div class="feature-card panel-outline">
            <div class="text-lg font-bold text-[var(--text)]">启动自检</div>
            <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
              设置页和状态条共用同一份健康检查数据，任何一个模块降级都会在界面上有明确提示。
            </p>
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
  MagicStick,
  Microphone,
  Service,
  VideoPlay,
} from '@element-plus/icons-vue'
import { onMounted } from 'vue'
import { useHealthDetail } from '../composables/useHealthDetail'

const {
  healthError,
  healthLoading,
  sortedServices,
  overallStatus,
  overallStatusText,
  fetchHealthDetail,
} = useHealthDetail()

const flowItems = [
  {
    kicker: 'Input',
    title: '文字或语音进入 WebSocket',
    description: '所有实时交互先进入统一的会话处理路径，语音输入会先完成转写再进入同一条业务链路。',
    icon: Connection,
  },
  {
    kicker: 'Reasoning',
    title: 'LLM 回复并输出情绪',
    description: '保留现有 LLM 情感分析，把情绪结果标准化后送入 Emotion Controller。',
    icon: ChatLineRound,
  },
  {
    kicker: 'Control',
    title: 'Emotion Controller 生成控制参数',
    description: '把文本增强、Qwen 指令、音色策略和 Live2D 参数统一编排，避免在多个文件里重复判断。',
    icon: MagicStick,
  },
  {
    kicker: 'Expression',
    title: 'Qwen 语音与 Live2D 同步表现',
    description: '后端返回完整响应，前端播放音频、驱动嘴型，并让角色在 idle、talk、react 之间自然切换。',
    icon: VideoPlay,
  },
  {
    kicker: 'Fallback',
    title: '异常时保持可解释的降级表现',
    description: 'TTS、嘴型或 Live2D 任何一环失败，都尽量保留文本与状态提示，不让用户误以为系统直接卡住。',
    icon: Service,
  },
]

const formatDetailValue = (value) => {
  if (Array.isArray(value)) return value.join(', ') || '-'
  if (typeof value === 'object' && value !== null) return JSON.stringify(value)
  return String(value)
}

onMounted(() => {
  fetchHealthDetail()
})
</script>
