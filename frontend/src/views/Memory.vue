<template>
  <div class="overview-page">
    <section class="overview-shell">
      <div class="hero-block panel-strong">
        <div>
          <p class="eyebrow">Overview</p>
          <h1 class="hero-title">会话与角色配置总览</h1>
          <p class="hero-copy">
            这里集中展示当前生效的角色设定、当前会话绑定情况、系统健康状态，以及所有历史会话。
          </p>
        </div>

        <div class="hero-actions">
          <button class="action-btn primary" type="button" :disabled="loading" @click="refreshAll">
            {{ loading ? '刷新中' : '刷新总览' }}
          </button>
        </div>
      </div>

      <div class="stats-grid">
        <div class="metric-card panel">
          <div class="feature-kicker">Client</div>
          <div class="metric-value">{{ sessionSummary.clientIdShort }}</div>
          <p class="metric-copy">当前浏览器绑定的 client id</p>
        </div>

        <div class="metric-card panel">
          <div class="feature-kicker">Current History</div>
          <div class="metric-value">{{ sessionSummary.currentHistoryShort }}</div>
          <p class="metric-copy">当前会话正在使用的 history uid</p>
        </div>

        <div class="metric-card panel">
          <div class="feature-kicker">Messages</div>
          <div class="metric-value">{{ sessionSummary.messageCount }}</div>
          <p class="metric-copy">当前聊天面板本地消息数</p>
        </div>

        <div class="metric-card panel">
          <div class="feature-kicker">Histories</div>
          <div class="metric-value">{{ overview.history_count || 0 }}</div>
          <p class="metric-copy">当前 client id 下可恢复的历史数</p>
        </div>
      </div>

      <div class="overview-grid">
        <section class="panel-strong card-section">
          <div class="section-head">
            <div>
              <div class="feature-kicker">Character</div>
              <h2>当前角色配置</h2>
            </div>
            <router-link to="/character" class="action-btn secondary no-underline">前往配置</router-link>
          </div>

          <div class="content-stack">
            <div class="detail-card">
              <div class="detail-label">LLM system prompt</div>
              <div class="detail-value prewrap">{{ characterConfig.llm_system_prompt || '未配置，当前使用默认 prompt。' }}</div>
            </div>

            <div class="detail-card">
              <div class="detail-label">情绪表达风格</div>
              <div class="detail-value prewrap">{{ characterConfig.emotion_style || '未配置，当前使用默认情绪语气。' }}</div>
            </div>
          </div>
        </section>

        <section class="panel-strong card-section">
          <div class="section-head">
            <div>
              <div class="feature-kicker">Session</div>
              <h2>当前会话状态</h2>
            </div>
            <router-link to="/chat" class="action-btn secondary no-underline">前往聊天</router-link>
          </div>

          <div class="content-stack">
            <div class="detail-row">
              <span>client id</span>
              <strong class="break-all">{{ sessionSummary.clientIdFull }}</strong>
            </div>
            <div class="detail-row">
              <span>current history uid</span>
              <strong class="break-all">{{ sessionSummary.currentHistoryFull }}</strong>
            </div>
            <div class="detail-row">
              <span>当前历史消息数</span>
              <strong>{{ overview.current_history_message_count || 0 }}</strong>
            </div>
            <div class="detail-row">
              <span>本地最后一条消息</span>
              <strong class="break-all">{{ sessionSummary.latestMessage }}</strong>
            </div>
          </div>
        </section>

        <section class="panel-strong card-section">
          <div class="section-head">
            <div>
              <div class="feature-kicker">Health</div>
              <h2>系统健康状态</h2>
            </div>
            <router-link to="/settings" class="action-btn secondary no-underline">详细自检</router-link>
          </div>

          <div class="service-list">
            <div v-for="service in healthServices" :key="service.key" class="service-card">
              <div class="service-top">
                <div class="status-chip">
                  <span class="status-dot" :class="service.status"></span>
                  <span>{{ service.label }}</span>
                </div>
                <strong>{{ service.status }}</strong>
              </div>
              <p>{{ service.summary }}</p>
            </div>
          </div>
        </section>

        <section class="panel-strong card-section history-section">
          <div class="section-head">
            <div>
              <div class="feature-kicker">History</div>
              <h2>历史会话总览</h2>
            </div>
            <span class="history-hint">刷新页面后应从这里恢复，而不是消失</span>
          </div>

          <div v-if="overview.histories?.length" class="history-list">
            <div v-for="history in overview.histories" :key="history.uid" class="history-card" :class="{ active: history.uid === overview.current_history_uid }">
              <div class="history-top">
                <strong class="break-all">{{ history.uid }}</strong>
                <span class="tag">{{ history.is_new ? '新会话' : '已有内容' }}</span>
              </div>
              <div class="history-preview">{{ history.latest_message?.content || '暂无预览' }}</div>
              <div class="history-meta">
                <span>{{ history.timestamp || '--' }}</span>
                <span>{{ history.latest_message?.role || '--' }}</span>
              </div>
            </div>
          </div>

          <div v-else class="empty-card">
            当前还没有可恢复的历史会话。发送一轮消息后，这里会自动出现。
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const { currentUser, getAuthHeaders } = useAuth()

const loading = ref(false)
const healthDetail = reactive({
  services: {},
})
const characterConfig = reactive({
  llm_system_prompt: '',
  emotion_style: '',
})
const overview = reactive({
  client_id: '',
  current_history_uid: '',
  history_count: 0,
  current_history_message_count: 0,
  histories: [],
})

const parseJsonResponse = async (response, fallbackMessage) => {
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    const text = await response.text()
    if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html')) {
      throw new Error('后端接口未生效，当前返回的是 HTML。请重启后端服务。')
    }
    throw new Error(fallbackMessage)
  }
  return response.json()
}

const parseLocalMessages = () => {
  try {
    const clientId = localStorage.getItem('digiHuman_clientId') || (currentUser.value?.client_id || 'guest')
    const raw = localStorage.getItem(`digiHuman_messages_v2_${clientId}`)
    const parsed = JSON.parse(raw || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const sessionSummary = computed(() => {
  const clientId = localStorage.getItem('digiHuman_clientId') || '未建立'
  const currentHistoryUid = localStorage.getItem(`digiHuman_currentHistoryUid_${clientId}`) || '未绑定'
  const messages = parseLocalMessages()
  const latest = messages[messages.length - 1]

  return {
    clientIdFull: clientId,
    currentHistoryFull: currentHistoryUid,
    clientIdShort: clientId === '未建立' ? clientId : `${clientId.slice(0, 8)}...`,
    currentHistoryShort: currentHistoryUid === '未绑定' ? currentHistoryUid : `${currentHistoryUid.slice(0, 12)}...`,
    messageCount: messages.length,
    latestMessage: latest?.content || '暂无消息',
  }
})

const healthServices = computed(() => {
  const services = healthDetail.services || {}
  return Object.entries(services).map(([key, value]) => ({
    key,
    label: value.label || key,
    status: value.status || 'warning',
    summary: value.summary || '暂无摘要',
  }))
})

const loadCharacterConfig = async () => {
  const response = await fetch('/api/character-config', {
    headers: {
      ...getAuthHeaders(),
    },
  })
  const data = await parseJsonResponse(response, '角色配置接口返回格式错误')
  characterConfig.llm_system_prompt = data.config?.llm_system_prompt || ''
  characterConfig.emotion_style = data.config?.emotion_style || ''
}

const loadHealthDetail = async () => {
  const response = await fetch('/health/detail')
  const data = await parseJsonResponse(response, '健康检查接口返回格式错误')
  healthDetail.services = data.services || {}
}

const loadOverview = async () => {
  const clientId = localStorage.getItem('digiHuman_clientId') || ''
  const currentHistoryUid = localStorage.getItem(`digiHuman_currentHistoryUid_${clientId || (currentUser.value?.client_id || 'guest')}`) || ''
  const params = new URLSearchParams({
    client_id: clientId || (currentUser.value?.client_id || ''),
    current_history_uid: currentHistoryUid,
  })
  const response = await fetch(`/api/session-overview?${params.toString()}`, {
    headers: {
      ...getAuthHeaders(),
    },
  })
  const data = await parseJsonResponse(response, '会话总览接口返回格式错误')
  overview.client_id = data.client_id || ''
  overview.current_history_uid = data.current_history_uid || ''
  overview.history_count = data.history_count || 0
  overview.current_history_message_count = data.current_history_message_count || 0
  overview.histories = Array.isArray(data.histories) ? data.histories : []
}

const refreshAll = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadCharacterConfig(),
      loadHealthDetail(),
      loadOverview(),
    ])
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.overview-page {
  padding: 104px 24px 40px;
}

.overview-shell {
  max-width: 1260px;
  margin: 0 auto;
  display: grid;
  gap: 24px;
}

.hero-block {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 28px 30px;
  border-radius: 30px;
}

.hero-title {
  margin: 10px 0 0;
  font-size: clamp(2rem, 3.2vw, 3.1rem);
  line-height: 0.98;
  color: var(--text);
}

.hero-copy {
  margin: 12px 0 0;
  max-width: 760px;
  color: var(--muted);
}

.hero-actions {
  display: flex;
  align-items: flex-start;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-copy {
  margin: 12px 0 0;
  color: var(--muted);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.card-section {
  padding: 24px;
  border-radius: 28px;
}

.history-section {
  grid-column: 1 / -1;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.section-head h2 {
  margin: 8px 0 0;
  color: var(--text);
  font-size: 1.45rem;
}

.history-hint {
  color: var(--muted);
  font-size: 0.92rem;
}

.content-stack {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

.detail-card,
.service-card,
.history-card,
.empty-card {
  padding: 16px 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid var(--line);
}

.detail-label {
  margin-bottom: 8px;
  font-size: 0.76rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

.detail-value {
  color: var(--text);
  line-height: 1.7;
}

.prewrap {
  white-space: pre-wrap;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  color: var(--text);
}

.break-all {
  word-break: break-all;
}

.service-list {
  margin-top: 18px;
  display: grid;
  gap: 12px;
}

.service-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.service-card p {
  margin: 12px 0 0;
  color: var(--muted);
  line-height: 1.6;
}

.history-list {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.history-card.active {
  border-color: rgba(196, 79, 45, 0.34);
  box-shadow: 0 14px 30px rgba(196, 79, 45, 0.12);
}

.history-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.history-preview {
  margin-top: 12px;
  color: var(--text);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.history-meta {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted);
  font-size: 0.9rem;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.76rem;
  font-weight: 700;
}

.empty-card {
  margin-top: 18px;
  color: var(--muted);
}

@media (max-width: 1100px) {
  .stats-grid,
  .overview-grid,
  .history-list {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 820px) {
  .overview-page {
    padding: 92px 16px 24px;
  }

  .hero-block,
  .stats-grid,
  .overview-grid,
  .history-list {
    grid-template-columns: 1fr;
  }
}
</style>
