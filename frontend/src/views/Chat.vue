<template>
  <div class="grid gap-6 xl:grid-cols-[300px_1fr]">
    <aside class="panel rounded-[32px] p-5">
      <div class="flex items-center justify-between gap-3">
        <div>
          <div class="feature-kicker">Session</div>
          <h2 class="mt-2 text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">对话历史</h2>
        </div>
        <button class="action-btn secondary" type="button" :disabled="!connected" @click="createNewHistory">
          新建
        </button>
      </div>

      <div class="mt-5">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索历史记录"
          class="w-full rounded-2xl border border-[var(--line)] bg-white/25 px-4 py-3 text-sm text-[var(--text)] outline-none"
        />
      </div>

      <div class="mt-5 space-y-3">
        <button
          v-for="history in filteredHistories"
          :key="history.uid"
          type="button"
          class="feature-card panel-outline block w-full text-left"
          :class="{ 'ring-2 ring-[var(--accent)]': currentHistoryUid === history.uid }"
          @click="switchHistory(history.uid)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-bold text-[var(--text)]">{{ getHistoryTitle(history) }}</div>
              <div class="mt-2 truncate text-xs text-[var(--muted)]">{{ getHistoryPreview(history) }}</div>
              <div class="mt-3 text-[11px] text-[var(--muted)]">{{ formatTime(history.timestamp) }}</div>
            </div>
            <button
              class="text-xs font-semibold text-[var(--danger)]"
              type="button"
              @click.stop="deleteHistory(history.uid)"
            >
              删除
            </button>
          </div>
        </button>

        <div v-if="!filteredHistories.length" class="rounded-[24px] border border-dashed border-[var(--line)] px-4 py-8 text-center text-sm text-[var(--muted)]">
          暂无可显示的对话历史
        </div>
      </div>
    </aside>

    <section class="panel-strong rounded-[32px] p-5 md:p-6">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div class="feature-kicker">Chat + Voice Sync</div>
          <h1 class="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--text)]">对话控制台</h1>
          <p class="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted)]">
            发送消息后会先显示文本，再在音频准备好后自动开口说话。文字打字、语音播放和 Live2D 状态机会尽量并行，不再等整轮都完成才一起出现。
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <div class="status-chip">
            <span class="status-dot" :class="connected ? 'healthy' : 'error'"></span>
            <span>{{ connected ? '已连接' : '连接中' }}</span>
          </div>
          <div class="status-chip">
            <span class="status-dot" :class="isPlayingAudio ? 'healthy' : 'warning'"></span>
            <span>{{ isPlayingAudio ? '语音播放中' : '等待播放' }}</span>
          </div>
          <div class="status-chip">
            <span class="status-dot" :class="currentEmotion.assistant.emotion || 'neutral'"></span>
            <span>{{ emotionLabel(currentEmotion.assistant.emotion) }}</span>
          </div>
        </div>
      </div>

      <div v-if="systemNotice" class="mt-5 rounded-[22px] border border-[rgba(201,122,24,0.22)] bg-[rgba(201,122,24,0.08)] px-4 py-3 text-sm text-[var(--warning)]">
        {{ systemNotice }}
      </div>

      <div class="mt-4 rounded-[24px] border border-[var(--line)] bg-white/35 px-4 py-4 text-sm text-[var(--muted)]">
        <div class="mb-2 flex items-center justify-between gap-3">
          <div class="feature-kicker">Current Character Config</div>
          <router-link to="/character" class="text-xs font-bold text-[var(--accent)] no-underline">前往角色配置</router-link>
        </div>
        <div class="grid gap-3 lg:grid-cols-2">
          <div>
            <div class="mb-1 font-semibold text-[var(--text)]">当前生效的 LLM system prompt</div>
            <div class="line-clamp-3">{{ currentCharacterConfig.llm_system_prompt || '未配置，当前使用默认 prompt。' }}</div>
          </div>
          <div>
            <div class="mb-1 font-semibold text-[var(--text)]">当前生效的情绪表达风格</div>
            <div class="line-clamp-3">{{ currentCharacterConfig.emotion_style || '未配置，当前使用默认情绪表达风格。' }}</div>
          </div>
        </div>
      </div>

      <div v-if="runtimeWarnings.length" class="mt-4 space-y-2">
        <div
          v-for="warning in runtimeWarnings"
          :key="warning.code"
          class="rounded-[20px] border border-[rgba(201,122,24,0.22)] bg-[rgba(201,122,24,0.08)] px-4 py-3 text-sm text-[var(--warning)]"
        >
          {{ warning.message }}
        </div>
      </div>

      <div class="mt-5 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div class="panel rounded-[28px] p-4 md:p-5">
          <div id="chatContainer" class="flex h-[560px] flex-col gap-4 overflow-y-auto pr-2">
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="[
                'max-w-[82%] rounded-[24px] px-4 py-3 text-sm leading-7',
                msg.role === 'user'
                  ? 'ml-auto bg-[var(--accent)] text-[#fff8f0]'
                  : 'bg-white/50 text-[var(--text)]',
              ]"
            >
              <div class="mb-2 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.12em] opacity-70">
                <span>{{ msg.role === 'user' ? 'User' : 'Assistant' }}</span>
                <span v-if="msg.role === 'assistant' && msg.emotion" class="rounded-full bg-black/8 px-2 py-0.5 normal-case tracking-normal">
                  {{ emotionLabel(msg.emotion) }}
                </span>
                <span v-if="msg.status === 'thinking'">思考中</span>
                <span v-else-if="msg.status === 'typing'">输出中</span>
                <span v-else-if="msg.status === 'speaking'">说话中</span>
              </div>
              <p class="whitespace-pre-wrap break-words">{{ msg.content || (msg.role === 'assistant' ? '...' : '') }}</p>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="panel rounded-[28px] p-4">
            <div class="feature-kicker">Emotion</div>
            <div class="mt-3 text-2xl font-extrabold tracking-[-0.04em] text-[var(--text)]">
              {{ emotionLabel(currentEmotion.assistant.emotion) }}
            </div>
            <div class="mt-3 text-sm text-[var(--muted)]">
              置信度 {{ Math.round((currentEmotion.assistant.confidence || 0) * 100) }}%
            </div>
            <div class="mt-1 text-sm text-[var(--muted)]">
              强度 {{ currentEmotion.assistant.intensity || 'medium' }}
            </div>
          </div>

          <div class="panel rounded-[28px] p-4">
            <div class="feature-kicker">TTS / Live2D</div>
            <div class="mt-4 space-y-3 text-sm text-[var(--muted)]">
              <div>
                <div class="font-semibold text-[var(--text)]">语音模式</div>
                <div>{{ currentParams.tts?.model || '-' }}</div>
              </div>
              <div>
                <div class="font-semibold text-[var(--text)]">指令</div>
                <div class="line-clamp-3">{{ currentTtsInstruct || '-' }}</div>
              </div>
              <div>
                <div class="font-semibold text-[var(--text)]">Live2D 动作</div>
                <div>{{ currentParams.live2d?.motion || currentParams.live2d?.react_motion || '-' }}</div>
              </div>
            </div>
          </div>

          <div class="panel rounded-[28px] p-4">
            <div class="feature-kicker">Voice Input</div>
            <div v-if="isRecording" class="mt-4">
              <div class="text-sm font-semibold text-[var(--danger)]">录音中...</div>
              <div class="mt-3 h-2 overflow-hidden rounded-full bg-black/10">
                <div class="h-full bg-[var(--danger)] transition-all duration-100" :style="{ width: `${audioLevel}%` }"></div>
              </div>
            </div>
            <div v-else class="mt-4 text-sm text-[var(--muted)]">
              点击麦克风后录音，结束时会自动转写并走同一条对话链路。
            </div>
          </div>
        </div>
      </div>

      <div class="mt-5 flex flex-col gap-3">
        <textarea
          v-model="inputMessage"
          rows="3"
          class="w-full rounded-[24px] border border-[var(--line)] bg-white/30 px-4 py-4 text-[var(--text)] outline-none"
          placeholder="输入你想对数字人说的话"
          :disabled="!connected"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>

        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="text-sm text-[var(--muted)]">
            {{ currentReplyState }}
          </div>
          <div class="flex flex-wrap gap-3">
            <button class="action-btn secondary" type="button" :disabled="!connected || playerIsLoading" @click="toggleVoiceRecording">
              {{ isRecording ? '结束录音' : '语音输入' }}
            </button>
            <button class="action-btn primary" type="button" :disabled="!connected || !inputMessage.trim()" @click="sendMessage">
              发送消息
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import { useAudioRecorder } from '@/composables/useAudioRecorder'

const defaultAssistantMessage = {
  id: 'welcome-message',
  role: 'assistant',
  content: '你好，我已经准备好了。你发来一句话后，我会先显示文本，再尽快开始说话并驱动 Live2D。',
  status: 'ready',
  emotion: 'neutral',
}

const inputMessage = ref('')
const connected = ref(false)
const messages = ref([defaultAssistantMessage])
const historyList = ref([])
const currentHistoryUid = ref(null)
const searchKeyword = ref('')
const runtimeWarnings = ref([])
const currentTtsInstruct = ref('')
const currentParams = ref({
  tts: null,
  live2d: null,
})
const currentCharacterConfig = ref({
  llm_system_prompt: '',
  emotion_style: '',
})
const currentEmotion = ref({
  user: { emotion: 'neutral', confidence: 0.5, intensity: 'medium' },
  assistant: { emotion: 'neutral', confidence: 0.5, intensity: 'medium' },
})

const activeResponseId = ref(null)
const clientId = ref(localStorage.getItem('digiHuman_clientId') || '')
const isRecording = ref(false)

let ws = null
let reconnectTimer = null
let typingTimer = null
let sentenceAudioQueue = []
let sentenceAudioProcessing = false

const {
  audioLevel,
  errorMessage: recorderError,
  requestPermission,
  startRecording,
  stopRecording,
} = useAudioRecorder()

const {
  isPlaying: playerIsPlaying,
  isLoading: playerIsLoading,
  errorMessage: playerError,
  capabilityWarning: playerCapabilityWarning,
  primeAudio,
  playBase64Audio,
  stopPlayback,
} = useAudioPlayer()

const isPlayingAudio = computed(() => playerIsPlaying.value || playerIsLoading.value)

const filteredHistories = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return historyList.value
  return historyList.value.filter((history) => {
    const preview = history?.latest_message?.content || ''
    return preview.toLowerCase().includes(keyword)
  })
})

const systemNotice = computed(() => {
  if (!connected.value) return '正在连接后端服务，连接恢复后即可继续联调。'
  return playerCapabilityWarning.value || playerError.value || recorderError.value || ''
})

const currentReplyState = computed(() => {
  const message = messages.value.find((item) => item.responseId === activeResponseId.value)
  if (!message) return '等待输入'
  if (message.status === 'thinking') return '模型正在思考'
  if (message.status === 'typing') return '文本正在输出'
  if (message.status === 'speaking') return '音频已就绪，正在说话'
  return '本轮回复完成'
})

const normalizeRuntimeWarnings = (warnings = []) => {
  return (Array.isArray(warnings) ? warnings : []).filter(
    (warning) => warning?.code !== 'live2d_backend_disabled'
  )
}

const emotionLabel = (emotion) => {
  const labels = {
    joy: '开心',
    sadness: '难过',
    anger: '生气',
    surprise: '惊讶',
    fear: '紧张',
    disgust: '厌恶',
    shy: '害羞',
    neutral: '平静',
  }
  return labels[emotion] || labels.neutral
}

const makeId = (prefix = 'msg') => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`

const saveSession = () => {
  localStorage.setItem('digiHuman_messages_v2', JSON.stringify(messages.value))
  if (currentHistoryUid.value) {
    localStorage.setItem('digiHuman_currentHistoryUid', currentHistoryUid.value)
  }
}

const restoreSession = () => {
  const storedMessages = localStorage.getItem('digiHuman_messages_v2')
  const storedHistoryUid = localStorage.getItem('digiHuman_currentHistoryUid')

  if (storedMessages) {
    try {
      const parsedMessages = JSON.parse(storedMessages)
      if (Array.isArray(parsedMessages) && parsedMessages.length) {
        messages.value = parsedMessages
      }
    } catch (error) {
      console.warn('Failed to restore messages:', error)
    }
  }

  if (storedHistoryUid) {
    currentHistoryUid.value = storedHistoryUid
  }
}

const scrollToBottom = async () => {
  await nextTick()
  const container = document.getElementById('chatContainer')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

const dispatchLive2DCommand = (command) => {
  if (!command) return
  window.dispatchEvent(new CustomEvent('digihuman-live2d-command', { detail: command }))
}

const dispatchLive2DTalkEvent = (type, detail = {}) => {
  window.dispatchEvent(new CustomEvent(type, { detail }))
}

const getHistoryTitle = (history) => {
  const content = history?.latest_message?.content || ''
  if (!content) return '新对话'
  return content.length > 18 ? `${content.slice(0, 18)}...` : content
}

const getHistoryPreview = (history) => history?.latest_message?.content || '暂无消息'

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

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

const loadCharacterConfigSummary = async () => {
  try {
    const response = await fetch('/api/character-config')
    const data = await parseJsonResponse(response, '角色配置摘要接口返回格式错误')
    currentCharacterConfig.value = {
      llm_system_prompt: data.config?.llm_system_prompt || '',
      emotion_style: data.config?.emotion_style || '',
    }
  } catch (error) {
    console.warn('Failed to load character config summary:', error)
  }
}

const ensurePendingAssistant = () => {
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage?.role === 'assistant' && ['thinking', 'typing', 'speaking'].includes(lastMessage.status)) {
    return lastMessage
  }

  const message = {
    id: makeId('assistant'),
    role: 'assistant',
    content: '',
    status: 'thinking',
    responseId: null,
    emotion: 'neutral',
  }
  messages.value.push(message)
  return message
}

const ensurePendingAssistantForResponse = (responseId) => {
  const existing = messages.value.find((item) => item.responseId === responseId)
  if (existing) {
    return existing
  }
  const message = ensurePendingAssistant()
  message.responseId = responseId
  return message
}

const animateAssistantText = (message, text) => {
  if (typingTimer) {
    clearInterval(typingTimer)
    typingTimer = null
  }

  message.content = ''
  message.status = 'typing'

  const chars = Array.from(text || '')
  let index = 0
  const step = chars.length > 80 ? 3 : 2

  typingTimer = window.setInterval(() => {
    index = Math.min(chars.length, index + step)
    message.content = chars.slice(0, index).join('')
    scrollToBottom()

    if (index >= chars.length) {
      clearInterval(typingTimer)
      typingTimer = null
      if (message.status === 'typing') {
        message.status = 'ready'
      }
      saveSession()
    }
  }, 22)
}

const processSentenceAudioQueue = async () => {
  if (sentenceAudioProcessing) {
    return
  }

  sentenceAudioProcessing = true

  while (sentenceAudioQueue.length) {
    const item = sentenceAudioQueue.shift()
    if (!item?.audio) {
      continue
    }

    const message = messages.value.find((entry) => entry.responseId === item.response_id)
    if (message) {
      message.status = 'speaking'
    }

    const talkCommand = currentParams.value.live2d || item.live2d_command || {}
    dispatchLive2DTalkEvent('digihuman-live2d-talk-start', talkCommand)

    try {
      await playBase64Audio(item.audio, item.audio_format || 'audio/wav')
    } catch (error) {
      runtimeWarnings.value = [{
        code: 'tts_playback_failed',
        message: playerError.value || '语音播放失败，已保留文本回复。',
      }]
      console.error('Sentence audio playback failed:', error)
    } finally {
      dispatchLive2DTalkEvent('digihuman-live2d-talk-end', talkCommand)
      if (message && message.status === 'speaking') {
        message.status = 'ready'
      }
      saveSession()
    }
  }

  sentenceAudioProcessing = false
}

const handleResponseAudio = async (data) => {
  runtimeWarnings.value = normalizeRuntimeWarnings(data.warnings).slice(0, 3) || runtimeWarnings.value

  if (!data.audio) {
    return
  }

  const message = messages.value.find((item) => item.responseId === data.response_id)
  if (message) {
    message.status = 'speaking'
  }

  dispatchLive2DTalkEvent('digihuman-live2d-talk-start', currentParams.value.live2d || {})

  try {
    await playBase64Audio(data.audio, data.audio_format || 'audio/wav')
  } catch (error) {
    runtimeWarnings.value = [{
      code: 'tts_playback_failed',
      message: playerError.value || '语音播放失败，已保留文本回复。',
    }]
    console.error('Audio playback failed:', error)
  } finally {
    dispatchLive2DTalkEvent('digihuman-live2d-talk-end', currentParams.value.live2d || {})
    if (message) {
      message.status = 'ready'
    }
    saveSession()
  }
}

const handleResponseStart = async (data) => {
  if (data.user_text) {
    const lastMessage = messages.value[messages.value.length - 1]
    if (!lastMessage || lastMessage.role !== 'user' || lastMessage.content !== data.user_text) {
      messages.value.push({
        id: makeId('user'),
        role: 'user',
        content: data.user_text,
        status: 'ready',
      })
    }
  }

  const assistantMessage = ensurePendingAssistantForResponse(data.response_id)
  assistantMessage.status = 'thinking'
  assistantMessage.content = ''
  activeResponseId.value = data.response_id
  await scrollToBottom()
}

const handleResponseDelta = async (data) => {
  const assistantMessage = ensurePendingAssistantForResponse(data.response_id)
  assistantMessage.status = 'typing'
  assistantMessage.content = data.text || `${assistantMessage.content || ''}${data.delta || ''}`
  activeResponseId.value = data.response_id
  saveSession()
  await scrollToBottom()
}

const handleFullResponse = async (data) => {
  runtimeWarnings.value = normalizeRuntimeWarnings(data.warnings).slice(0, 3)

  if (data.user_text) {
    const lastMessage = messages.value[messages.value.length - 1]
    if (!lastMessage || lastMessage.role !== 'user' || lastMessage.content !== data.user_text) {
      messages.value.push({
        id: makeId('user'),
        role: 'user',
        content: data.user_text,
        status: 'ready',
      })
    }
  }

  if (data.emotion) {
    currentEmotion.value = data.emotion
  }
  if (data.tts_params) {
    currentParams.value.tts = data.tts_params
  }
  if (data.live2d_params) {
    currentParams.value.live2d = data.live2d_params
  }
  currentTtsInstruct.value = data.tts_instruct || ''

  const content = data.text?.enhanced || data.text?.original || data.text || ''
  const assistantMessage = ensurePendingAssistantForResponse(data.response_id)
  assistantMessage.emotion = data.emotion?.assistant?.emotion || 'neutral'
  assistantMessage.params = {
    tts: data.tts_params,
    live2d: data.live2d_params,
  }
  activeResponseId.value = data.response_id

  dispatchLive2DCommand(data.live2d_command)
  if (data.streaming) {
    assistantMessage.content = content
    if (assistantMessage.status !== 'speaking') {
      assistantMessage.status = 'ready'
    }
  } else {
    animateAssistantText(assistantMessage, content)
  }
  saveSession()
  await scrollToBottom()

  if (data.audio) {
    await handleResponseAudio({
      type: 'response-audio',
      response_id: data.response_id,
      audio: data.audio,
      audio_format: data.audio_format,
      warnings: data.warnings,
    })
  }
}

const handleWebSocketMessage = async (data) => {
  switch (data.type) {
    case 'connection_established':
      clientId.value = data.client_id
      localStorage.setItem('digiHuman_clientId', data.client_id)
      connected.value = true
      runtimeWarnings.value = []
      fetchHistoryList()
      break

    case 'full-response':
      await handleFullResponse(data)
      break

    case 'response-start':
      await handleResponseStart(data)
      break

    case 'response-delta':
      await handleResponseDelta(data)
      break

    case 'response-audio':
      await handleResponseAudio(data)
      break

    case 'sentence-audio':
      break

    case 'emotion_update':
      if (data.source === 'user') {
        currentEmotion.value.user = {
          emotion: data.emotion,
          confidence: data.confidence,
          intensity: data.intensity,
        }
      } else if (data.source === 'assistant') {
        currentEmotion.value.assistant = {
          emotion: data.emotion,
          confidence: data.confidence,
          intensity: data.intensity,
        }
        if (data.live2d_command) {
          currentParams.value.live2d = data.live2d_command
          dispatchLive2DCommand(data.live2d_command)
        }
      }
      break

    case 'history-list':
        historyList.value = data.histories || []
        if (currentHistoryUid.value && historyList.value.some((item) => item.uid === currentHistoryUid.value)) {
          ws?.send(JSON.stringify({
            type: 'fetch-and-set-history',
            history_uid: currentHistoryUid.value,
          }))
        }
        break

    case 'history-data':
      messages.value = (data.messages || []).map((msg) => ({
        id: makeId(msg.role === 'human' ? 'user' : 'assistant'),
        role: msg.role === 'human' ? 'user' : 'assistant',
        content: msg.content,
        status: 'ready',
        emotion: msg.role === 'human' ? null : 'neutral',
      }))
      if (!messages.value.length) {
        messages.value = [defaultAssistantMessage]
      }
      saveSession()
      await scrollToBottom()
      break

    case 'new-history-created':
      currentHistoryUid.value = data.history_uid
      messages.value = [defaultAssistantMessage]
      saveSession()
      fetchHistoryList()
      break

    case 'history-deleted':
      fetchHistoryList()
      break

    case 'error':
      runtimeWarnings.value = [{
        code: 'server_error',
        message: data.message || '处理失败，请重试。',
      }]
      ElMessage.error(data.message || '处理失败，请重试。')
      break

    default:
      break
  }
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const query = clientId.value ? `?client_id=${encodeURIComponent(clientId.value)}` : ''
  const wsUrl = `${protocol}//${window.location.host}/ws${query}`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    connected.value = true
  }

  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      await handleWebSocketMessage(data)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }

  ws.onclose = () => {
    connected.value = false
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }
    reconnectTimer = window.setTimeout(connectWebSocket, 2000)
  }

  ws.onerror = (error) => {
    connected.value = false
    console.error('WebSocket error:', error)
  }
}

const fetchHistoryList = () => {
  if (!ws || !connected.value) return
  ws.send(JSON.stringify({ type: 'fetch-history-list' }))
}

const createNewHistory = () => {
  if (!ws || !connected.value) return
  ws.send(JSON.stringify({ type: 'create-new-history' }))
}

const switchHistory = (historyUid) => {
  if (!ws || !connected.value || currentHistoryUid.value === historyUid) return
  currentHistoryUid.value = historyUid
  ws.send(JSON.stringify({
    type: 'fetch-and-set-history',
    history_uid: historyUid,
  }))
}

const deleteHistory = (historyUid) => {
  if (!ws || !connected.value) return
  if (!window.confirm('确定删除这条对话历史吗？')) return
  ws.send(JSON.stringify({
    type: 'delete-history',
    history_uid: historyUid,
  }))
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || !connected.value || !ws) return

  await primeAudio()

  messages.value.push({
    id: makeId('user'),
    role: 'user',
    content: message,
    status: 'ready',
  })

  ensurePendingAssistant()
  inputMessage.value = ''
  runtimeWarnings.value = []
  await scrollToBottom()
  saveSession()

  ws.send(JSON.stringify({
    type: 'text-input',
    text: message,
    client_id: clientId.value,
  }))
}

const toggleVoiceRecording = async () => {
  if (isRecording.value) {
    const audioBase64 = await stopRecording()
    isRecording.value = false

    if (!audioBase64 || !ws || !connected.value) {
      ElMessage.warning('录音失败，请重试。')
      return
    }

    ensurePendingAssistant()
    ws.send(JSON.stringify({
      type: 'mic-audio-data',
      audio: audioBase64,
      client_id: clientId.value,
    }))
    ws.send(JSON.stringify({
      type: 'mic-audio-end',
      client_id: clientId.value,
    }))
    return
  }

  const granted = await requestPermission()
  if (!granted) {
    ElMessage.error(recorderError.value || '无法获取麦克风权限。')
    return
  }

  await primeAudio()

  const started = await startRecording()
  if (!started) {
    ElMessage.error('启动录音失败，请检查浏览器权限。')
    return
  }

  isRecording.value = true
}

onMounted(async () => {
  restoreSession()
  await loadCharacterConfigSummary()
  connectWebSocket()
  await scrollToBottom()
})

onUnmounted(() => {
  saveSession()
  if (typingTimer) {
    clearInterval(typingTimer)
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
  stopPlayback()
  sentenceAudioQueue = []
  sentenceAudioProcessing = false
  if (ws) {
    ws.close()
  }
})
</script>
