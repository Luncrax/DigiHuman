<template>
  <div class="space-y-8">
    <section class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <div class="panel-strong rounded-[36px] px-6 py-7 md:px-8 md:py-9">
        <div class="eyebrow">Multimodal Digital Human</div>
        <div class="mt-5 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <div>
            <h1 class="section-title text-[var(--text)]">
              支持多模态交互的
              <span class="block mt-2 text-[var(--accent)]">虚拟数字人助手</span>
            </h1>
            <p class="mt-5 max-w-2xl text-base leading-7 text-[var(--muted)] md:text-lg">
              主页现在聚焦展示这套系统最核心的能力：对话、语音、情绪、虚拟人表现、知识检索与学习辅助。
              你可以先从这里快速判断系统状态，再进入主功能页面开始使用。
            </p>

            <div class="mt-6 flex flex-wrap gap-3">
              <router-link to="/chat" class="action-btn primary no-underline">
                进入对话控制台
              </router-link>
              <router-link to="/study-assistant" class="action-btn secondary no-underline">
                打开学习助手
              </router-link>
            </div>

            <div class="mt-8 grid gap-4 sm:grid-cols-3">
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Conversation</div>
                <div class="mt-3 text-xl font-extrabold text-[var(--text)]">文本 + 语音</div>
                <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
                  支持文本输入、语音输入、流式回复与语音播报。
                </p>
              </div>
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Emotion</div>
                <div class="mt-3 text-xl font-extrabold text-[var(--text)]">情绪驱动</div>
                <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
                  识别情绪并统一编排文本、语音和角色表现。
                </p>
              </div>
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Knowledge</div>
                <div class="mt-3 text-xl font-extrabold text-[var(--text)]">知识增强</div>
                <p class="mt-2 text-sm leading-6 text-[var(--muted)]">
                  结合 SQLite 与 Milvus 支撑历史、配置和学习知识检索。
                </p>
              </div>
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
                自检会同时检查 LLM、TTS、ASR、Live2D 和 WebSocket，
                首页会把这些核心模块的状态集中展示出来。
              </p>
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Voice Engine</div>
                <div class="metric-value mt-3 text-[var(--text)]">{{ ttsState }}</div>
                <p class="mt-2 text-sm text-[var(--muted)]">当前语音合成链路状态</p>
              </div>
              <div class="metric-card panel-outline rounded-[24px]">
                <div class="feature-kicker">Avatar Stage</div>
                <div class="metric-value mt-3 text-[var(--text)]">{{ live2dState }}</div>
                <p class="mt-2 text-sm text-[var(--muted)]">虚拟人舞台与状态机状态</p>
              </div>
            </div>

            <div class="feature-card panel-outline rounded-[28px]">
              <div class="feature-kicker">Recommended Start</div>
              <div class="mt-2 text-xl font-extrabold text-[var(--text)]">建议先进入对话控制台</div>
              <p class="mt-3 text-sm leading-6 text-[var(--muted)]">
                如果你想最快体验完整主链路，请先进入对话控制台；
                如果你要导入学习资料、启动番茄钟或播放音乐，再进入学习助手。
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="panel rounded-[36px] p-6 md:p-7">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="feature-kicker">Pipeline</div>
            <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">
              系统主链路
            </h2>
          </div>
          <button class="action-btn secondary" type="button" :disabled="healthLoading" @click="fetchHealthDetail">
            {{ healthLoading ? '刷新中...' : '刷新状态' }}
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

    <section class="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
      <div class="panel rounded-[34px] p-6 md:p-7">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="feature-kicker">Quick Access</div>
            <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">
              核心入口
            </h2>
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
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="feature-kicker">Module Snapshot</div>
            <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">
              当前模块状态
            </h2>
          </div>
          <router-link to="/database" class="text-sm font-semibold text-[var(--accent)] no-underline">
            查看数据库
          </router-link>
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
  Microphone,
  Reading,
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
    description: '集中体验文本对话、语音输入、流式回复、语音播报和 Live2D 联动。',
    icon: ChatLineRound,
  },
  {
    to: '/study-assistant',
    kicker: 'Study Assistant',
    title: '学习助手',
    description: '生成学习计划，调用番茄钟、音乐播放和知识文件导入能力。',
    icon: Reading,
  },
  {
    to: '/dashboard',
    kicker: 'Runtime',
    title: '运行看板',
    description: '查看模块级健康状态、运行快照和主要链路当前可用性。',
    icon: DataLine,
  },
  {
    to: '/character',
    kicker: 'Persona',
    title: '角色配置',
    description: '配置 system prompt、情绪表达风格，并测试当前语音输出效果。',
    icon: Setting,
  },
]

const pipelineSteps = [
  {
    kicker: 'Step 1',
    title: '用户输入进入统一交互入口',
    description: '文本和语音输入都会先进入同一条后端链路，避免多套逻辑分叉。',
    icon: Microphone,
  },
  {
    kicker: 'Step 2',
    title: 'LLM 理解上下文并生成回复',
    description: '系统会结合历史会话、角色设定和情绪风格，生成当前轮次的自然语言回复。',
    icon: Connection,
  },
  {
    kicker: 'Step 3',
    title: 'Emotion Controller 统一编排表现',
    description: '把情绪结果映射为文本表达、语音参数和虚拟人动作控制，不再散落处理。',
    icon: MagicStick,
  },
  {
    kicker: 'Step 4',
    title: '语音输出与 Live2D 同步表现',
    description: '前端负责语音播放、嘴型同步和状态机切换，让虚拟人真正说出来并动起来。',
    icon: Service,
  },
]

const ttsState = computed(() => {
  const service = sortedServices.value.find((item) => item.key === 'qwen_tts' || item.key === 'tts')
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
