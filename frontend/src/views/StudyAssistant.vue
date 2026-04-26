<template>
  <div class="space-y-8">
    <section class="panel-strong rounded-[36px] p-6 md:p-8">
      <div class="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
        <div class="max-w-3xl">
          <div class="eyebrow">Study Assistant</div>
          <h1 class="mt-4 text-3xl font-extrabold tracking-[-0.04em] text-[var(--text)]">学习助手模块</h1>
          <p class="mt-4 text-sm leading-7 text-[var(--muted)]">
            这里可以生成学习计划、调用番茄钟和音乐工具，并把学习计划模板、学科笔记、工具策略文件导入 Milvus 作为知识库。
          </p>
        </div>

        <div class="flex flex-wrap gap-3">
          <button class="action-btn secondary" type="button" :disabled="loadingStatus" @click="fetchStatus">
            {{ loadingStatus ? '刷新中...' : '刷新状态' }}
          </button>
          <button class="action-btn primary" type="button" :disabled="bootstrapping" @click="bootstrapKnowledge">
            {{ bootstrapping ? '初始化中...' : '初始化模板知识库' }}
          </button>
        </div>
      </div>

      <div v-if="errorMessage" class="mt-6 rounded-[24px] border border-[rgba(170,61,49,0.2)] bg-[rgba(170,61,49,0.08)] px-4 py-3 text-sm text-[var(--danger)]">
        {{ errorMessage }}
      </div>

      <div v-if="successMessage" class="mt-6 rounded-[24px] border border-[rgba(41,125,77,0.2)] bg-[rgba(41,125,77,0.08)] px-4 py-3 text-sm text-[var(--success)]">
        {{ successMessage }}
      </div>

      <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="panel rounded-[26px] p-4">
          <div class="feature-kicker">Milvus</div>
          <div class="mt-3 text-2xl font-extrabold text-[var(--text)]">{{ statusData.milvus?.backend || 'unknown' }}</div>
          <div class="mt-2 text-sm text-[var(--muted)]">
            {{ statusData.milvus?.available ? '已连接' : (statusData.milvus?.reason || '当前走本地 fallback') }}
          </div>
        </div>
        <div class="panel rounded-[26px] p-4">
          <div class="feature-kicker">Collection</div>
          <div class="mt-3 text-2xl font-extrabold text-[var(--text)]">{{ statusData.milvus?.collection_name || '-' }}</div>
          <div class="mt-2 text-sm text-[var(--muted)]">用于存储学习计划模板与知识片段</div>
        </div>
        <div class="panel rounded-[26px] p-4">
          <div class="feature-kicker">Knowledge Root</div>
          <div class="mt-3 break-all text-sm font-semibold text-[var(--text)]">{{ statusData.knowledge_root || '-' }}</div>
        </div>
        <div class="panel rounded-[26px] p-4">
          <div class="feature-kicker">Music Root</div>
          <div class="mt-3 break-all text-sm font-semibold text-[var(--text)]">{{ statusData.music_root || '-' }}</div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <div class="space-y-6">
        <section class="panel rounded-[32px] p-6">
          <div class="feature-kicker">Knowledge Upload</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">上传并导入知识文件</h2>
          <p class="mt-3 text-sm leading-7 text-[var(--muted)]">
            支持 `.md`、`.txt`、`.json`。文件会保存到知识目录并立即导入 Milvus。
          </p>

          <div class="mt-5 rounded-[24px] border border-[var(--line)] bg-white/20 p-4">
            <input
              ref="fileInput"
              class="block w-full text-sm text-[var(--muted)]"
              type="file"
              accept=".md,.txt,.json"
              multiple
              @change="handleFileChange"
            />
            <div v-if="selectedFiles.length" class="mt-4 space-y-2">
              <div class="text-sm font-semibold text-[var(--text)]">待上传文件</div>
              <div
                v-for="file in selectedFiles"
                :key="`${file.name}-${file.size}`"
                class="rounded-[18px] border border-[var(--line)] bg-white/20 px-3 py-2 text-sm text-[var(--muted)]"
              >
                {{ file.name }} · {{ formatBytes(file.size) }}
              </div>
            </div>
            <div class="mt-4 flex flex-wrap gap-3">
              <button class="action-btn primary" type="button" :disabled="uploading || !selectedFiles.length" @click="uploadKnowledge">
                {{ uploading ? '上传中...' : '上传并导入' }}
              </button>
              <button class="action-btn secondary" type="button" :disabled="uploading || !selectedFiles.length" @click="clearSelectedFiles">
                清空选择
              </button>
            </div>
          </div>

          <div v-if="lastImportResult" class="mt-5 rounded-[24px] border border-[var(--line)] bg-white/20 p-4 text-sm">
            <div class="font-semibold text-[var(--text)]">最近一次导入结果</div>
            <div class="mt-2 text-[var(--muted)]">后端：{{ lastImportResult.data?.backend || '-' }}</div>
            <div class="mt-1 text-[var(--muted)]">导入片段：{{ lastImportResult.data?.count || 0 }}</div>
            <div class="mt-2 text-[var(--muted)]">文件：{{ (lastImportResult.imported_files || []).join('、') || '无' }}</div>
            <div v-if="(lastImportResult.skipped_files || []).length" class="mt-3 text-[var(--warning)]">
              跳过：{{ lastImportResult.skipped_files.map((item) => `${item.name}(${item.reason})`).join('；') }}
            </div>
          </div>
        </section>

        <section class="panel rounded-[32px] p-6">
          <div class="feature-kicker">Plan Builder</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">生成学习计划</h2>
          <textarea
            v-model="goal"
            class="mt-5 min-h-[150px] w-full rounded-[24px] border border-[var(--line)] bg-white/30 px-4 py-4 text-sm text-[var(--text)] outline-none transition focus:border-[var(--accent)]"
            placeholder="例如：我要学习数学 90 分钟，帮我安排专注时间、休息时间，并推荐适合的音乐。"
          />
          <div class="mt-4 flex flex-wrap gap-3">
            <button class="action-btn primary" type="button" :disabled="planning" @click="generatePlan">
              {{ planning ? '生成中...' : '生成学习计划' }}
            </button>
            <button class="action-btn secondary" type="button" @click="fillDemoGoal">填入示例</button>
          </div>

          <div v-if="planData" class="mt-8 space-y-5">
            <div class="rounded-[24px] border border-[var(--line)] bg-white/20 px-5 py-4">
              <div class="text-sm font-semibold text-[var(--muted)]">计划概览</div>
              <div class="mt-2 text-lg font-bold text-[var(--text)]">{{ planData.goal }}</div>
              <p class="mt-2 text-sm leading-7 text-[var(--muted)]">{{ planData.overview }}</p>
            </div>

            <div class="space-y-3">
              <div
                v-for="(step, index) in planData.plan_steps"
                :key="`${step.title}-${index}`"
                class="rounded-[24px] border border-[var(--line)] bg-white/20 px-5 py-4"
              >
                <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div class="text-sm font-semibold text-[var(--muted)]">步骤 {{ index + 1 }}</div>
                    <div class="mt-1 text-lg font-bold text-[var(--text)]">{{ step.title }}</div>
                    <div class="mt-1 text-sm text-[var(--muted)]">建议时长：{{ step.duration_minutes }} 分钟</div>
                    <p class="mt-2 text-sm leading-6 text-[var(--muted)]">{{ step.notes }}</p>
                  </div>
                  <button class="action-btn secondary shrink-0" type="button" @click="executeTool(step.tool_command, buildStepPayload(step))">
                    执行 {{ commandLabel(step.tool_command) }}
                  </button>
                </div>
              </div>
            </div>

            <div>
              <div class="text-sm font-semibold text-[var(--muted)]">推荐工具</div>
              <div class="mt-3 flex flex-wrap gap-3">
                <button
                  v-for="tool in planData.suggested_tools"
                  :key="tool.command + JSON.stringify(tool.payload)"
                  class="action-btn secondary"
                  type="button"
                  @click="executeTool(tool.command, tool.payload)"
                >
                  {{ tool.label }}
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="space-y-6">
        <section class="panel rounded-[32px] p-6">
          <div class="feature-kicker">Knowledge Files</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">当前知识文件</h2>
          <div class="mt-5 space-y-3">
            <div
              v-for="file in statusData.knowledge_files || []"
              :key="file.relative_path"
              class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3"
            >
              <div class="font-bold text-[var(--text)]">{{ file.name }}</div>
              <div class="mt-1 text-sm text-[var(--muted)]">{{ file.relative_path }}</div>
              <div class="mt-1 text-xs text-[var(--muted)]">{{ file.suffix }} · {{ formatBytes(file.size) }}</div>
              <div class="mt-3 flex flex-wrap gap-3">
                <button
                  class="action-btn secondary"
                  type="button"
                  :disabled="previewLoadingPath === file.relative_path"
                  @click="previewKnowledgeFile(file)"
                >
                  {{ previewLoadingPath === file.relative_path ? '预览中...' : '预览文件内容' }}
                </button>
                <button
                  class="action-btn secondary"
                  type="button"
                  :disabled="deletingFilePath === file.relative_path"
                  @click="deleteKnowledgeFile(file, 'local_only')"
                >
                  {{ deletingFilePath === file.relative_path && deletingMode === 'local_only' ? '删除中...' : '仅删除本地文件' }}
                </button>
                <button
                  class="action-btn primary"
                  type="button"
                  :disabled="deletingFilePath === file.relative_path"
                  @click="deleteKnowledgeFile(file, 'delete_and_reimport')"
                >
                  {{ deletingFilePath === file.relative_path && deletingMode === 'delete_and_reimport' ? '重导中...' : '删除并从 Milvus 重导' }}
                </button>
              </div>
            </div>
            <div v-if="!(statusData.knowledge_files || []).length" class="text-sm text-[var(--muted)]">
              还没有知识文件，先上传一份学习计划模板试试。
            </div>
          </div>

          <div v-if="previewData" class="mt-5 rounded-[24px] border border-[var(--line)] bg-white/20 p-4">
            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <div class="text-sm font-semibold text-[var(--muted)]">文件预览</div>
                <div class="mt-1 text-lg font-bold text-[var(--text)]">{{ previewData.name }}</div>
                <div class="mt-1 text-xs text-[var(--muted)]">{{ previewData.relative_path }} · {{ previewData.suffix }}</div>
              </div>
              <button class="action-btn secondary shrink-0" type="button" @click="clearPreview">
                关闭预览
              </button>
            </div>
            <pre class="mt-4 max-h-[420px] overflow-auto rounded-[20px] border border-[var(--line)] bg-[rgba(255,255,255,0.45)] p-4 text-xs leading-6 text-[var(--text)] whitespace-pre-wrap break-words">{{ previewData.content }}</pre>
          </div>
        </section>

        <section class="panel rounded-[32px] p-6">
          <div class="feature-kicker">Knowledge Hits</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">RAG</h2>
          <div class="mt-5 space-y-3">
            <div
              v-for="(hit, index) in planData?.knowledge_hits || []"
              :key="`${hit.title}-${index}`"
              class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3"
            >
              <div class="text-sm font-semibold text-[var(--muted)]">{{ hit.item_type }} / {{ hit.category }}</div>
              <div class="mt-1 font-bold text-[var(--text)]">{{ hit.title }}</div>
              <p class="mt-2 text-sm leading-6 text-[var(--muted)]">{{ hit.description }}</p>
              <div class="mt-2 text-xs text-[var(--muted)]">score: {{ hit.score }}</div>
            </div>
            <div v-if="!(planData?.knowledge_hits || []).length" class="text-sm text-[var(--muted)]">
              先生成一次学习计划，这里就会显示匹配到的模板与知识片段。
            </div>
          </div>
        </section>

        <section class="panel rounded-[32px] p-6">
          <div class="feature-kicker">Music Library</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">音乐文件夹</h2>
          <div class="mt-4 space-y-4">
            <div v-for="(tracks, category) in statusData.music_library || {}" :key="category" class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3">
              <div class="font-bold capitalize text-[var(--text)]">{{ category }}</div>
              <div class="mt-1 text-sm text-[var(--muted)]">{{ tracks.length }} 首</div>
              <div class="mt-2 text-xs text-[var(--muted)]">
                把音频文件放到 [e:\big_work\DigiHuman\study_assets\music\{{ category }}](e:/big_work/DigiHuman/study_assets/music/{{ category }}) 下。
              </div>
            </div>
          </div>
          <audio ref="musicAudio" v-if="currentAudioUrl" class="mt-5 w-full" :src="currentAudioUrl" controls autoplay />
        </section>

        <section class="panel rounded-[32px] p-6">
          <div class="feature-kicker">Pomodoro</div>
          <h2 class="mt-2 text-2xl font-extrabold tracking-[-0.03em] text-[var(--text)]">当前番茄钟</h2>
          <div class="mt-5 space-y-3">
            <div
              v-for="session in activePomodoroSessions"
              :key="session.session_id"
              class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3"
            >
              <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <div class="font-bold text-[var(--text)]">{{ session.title }}</div>
                  <div class="mt-1 text-sm text-[var(--muted)]">
                    {{ session.status === 'paused' ? '已暂停' : (session.status === 'focus' ? '专注中' : '休息中') }} · 剩余 {{ formatDuration(getSessionRemainingSeconds(session)) }}
                  </div>
                  <div class="mt-1 text-xs text-[var(--muted)]">
                    总时长 {{ formatDuration(getSessionTotalSeconds(session)) }}
                  </div>
                </div>
                <div class="flex flex-wrap gap-3">
                  <button
                    class="action-btn secondary shrink-0"
                    type="button"
                    @click="executeTool(session.status === 'paused' ? 'resume_pomodoro' : 'pause_pomodoro', { session_id: session.session_id })"
                  >
                    {{ session.status === 'paused' ? '继续' : '暂停' }}
                  </button>
                  <button class="action-btn secondary shrink-0" type="button" @click="executeTool('stop_pomodoro', { session_id: session.session_id })">
                    停止
                  </button>
                </div>
              </div>
              <div class="mt-4">
                <div class="h-3 overflow-hidden rounded-full bg-[rgba(80,56,38,0.12)]">
                  <div
                    class="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),#f2b56f)] transition-[width] duration-700 ease-out"
                    :style="{ width: `${getSessionProgressPercent(session)}%` }"
                  />
                </div>
                <div class="mt-2 flex items-center justify-between text-xs text-[var(--muted)]">
                  <span>已进行 {{ formatDuration(getSessionElapsedSeconds(session)) }}</span>
                  <span>{{ Math.round(getSessionProgressPercent(session)) }}%</span>
                </div>
              </div>
            </div>
            <div v-if="!activePomodoroSessions.length" class="text-sm text-[var(--muted)]">
              当前没有正在运行的番茄钟。
            </div>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const { getAuthHeaders } = useAuth()

const fileInput = ref(null)
const musicAudio = ref(null)
const goal = ref('')
const selectedFiles = ref([])
const loadingStatus = ref(false)
const planning = ref(false)
const bootstrapping = ref(false)
const uploading = ref(false)
const deletingFilePath = ref('')
const deletingMode = ref('')
const previewLoadingPath = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const statusData = ref({})
const activePomodoroSessions = ref([])
const planData = ref(null)
const currentAudioUrl = ref('')
const lastImportResult = ref(null)
const previewData = ref(null)
const nowTick = ref(Date.now())
const pomodoroDebug = ref('')

let countdownTimer = null
let statusSyncTimer = null

const commandLabel = (command) => {
  const mapping = {
    start_pomodoro: '番茄钟',
    pause_pomodoro: '暂停番茄钟',
    resume_pomodoro: '继续番茄钟',
    play_music: '音乐',
    tts_reminder: '语音提醒',
    stop_pomodoro: '停止番茄钟',
  }
  return mapping[command] || command
}

const clearMessages = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const revokeCurrentAudio = () => {
  if (currentAudioUrl.value && currentAudioUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(currentAudioUrl.value)
  }
}

const fillDemoGoal = () => {
  goal.value = '我要学习数学 90 分钟，帮我安排专注时间、休息时间，并推荐适合的音乐。'
}

const formatBytes = (bytes) => {
  const size = Number(bytes || 0)
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const formatDuration = (seconds) => {
  const safe = Math.max(0, Number(seconds || 0))
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const secs = safe % 60
  if (hours > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

const getSessionEndMs = (session) => {
  if (session?.ends_at_ms) {
    return Number(session.ends_at_ms)
  }
  const value = Date.parse(session?.ends_at || '')
  return Number.isFinite(value) ? value : nowTick.value
}

const getSessionStartMs = (session) => {
  if (session?.started_at_ms) {
    return Number(session.started_at_ms)
  }
  const value = Date.parse(session?.started_at || '')
  return Number.isFinite(value) ? value : nowTick.value
}

const getSessionRemainingSeconds = (session) => {
  return Math.max(0, Number(session?.remaining_seconds || 0))
}

const getSessionTotalSeconds = (session) => {
  if (session?.total_seconds) {
    return Math.max(1, Number(session.total_seconds))
  }
  const total = Math.floor((getSessionEndMs(session) - getSessionStartMs(session)) / 1000)
  return Math.max(1, total)
}

const getSessionElapsedSeconds = (session) => {
  return Math.min(getSessionTotalSeconds(session), Math.max(0, getSessionTotalSeconds(session) - getSessionRemainingSeconds(session)))
}

const getSessionProgressPercent = (session) => {
  const total = getSessionTotalSeconds(session)
  const elapsed = getSessionElapsedSeconds(session)
  return Math.max(0, Math.min(100, (elapsed / total) * 100))
}

const handleFileChange = (event) => {
  selectedFiles.value = Array.from(event.target.files || [])
}

const clearSelectedFiles = () => {
  selectedFiles.value = []
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const clearPreview = () => {
  previewData.value = null
  previewLoadingPath.value = ''
}

const updatePomodoroDebug = (command, payload, result = null) => {
  pomodoroDebug.value = JSON.stringify(
    {
      at: new Date().toLocaleTimeString(),
      command,
      payload,
      session_status: result?.session?.status || null,
      remaining_seconds: result?.session?.remaining_seconds ?? null,
      session_id: result?.session?.session_id || result?.session_id || null,
    },
    null,
    2,
  )
}

const applyStatusData = (data) => {
  const next = data || {}
  statusData.value = next
  activePomodoroSessions.value = [...(next.active_pomodoro_sessions || [])]
}

const fetchStatus = async () => {
  loadingStatus.value = true
  clearMessages()
  try {
    const response = await fetch('/api/study-assistant/status', {
      headers: {
        ...getAuthHeaders(),
      },
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '读取学习助手状态失败。')
    }
    applyStatusData(data.data)
  } catch (error) {
    errorMessage.value = error.message || '读取学习助手状态失败。'
  } finally {
    loadingStatus.value = false
  }
}

const bootstrapKnowledge = async () => {
  bootstrapping.value = true
  clearMessages()
  try {
    const response = await fetch('/api/study-assistant/bootstrap', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '初始化知识库失败。')
    }
    successMessage.value = '学习助手模板知识库已初始化。'
    await fetchStatus()
  } catch (error) {
    errorMessage.value = error.message || '初始化知识库失败。'
  } finally {
    bootstrapping.value = false
  }
}

const uploadKnowledge = async () => {
  if (!selectedFiles.value.length) {
    errorMessage.value = '请先选择知识文件。'
    return
  }

  uploading.value = true
  clearMessages()
  try {
    const formData = new FormData()
    selectedFiles.value.forEach((file) => {
      formData.append('files', file)
    })

    const response = await fetch('/api/study-assistant/import-knowledge', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
      body: formData,
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '导入知识文件失败。')
    }

    lastImportResult.value = data
    successMessage.value = `已导入 ${data.imported_files?.length || 0} 个文件。`
    clearSelectedFiles()
    await fetchStatus()
  } catch (error) {
    errorMessage.value = error.message || '导入知识文件失败。'
  } finally {
    uploading.value = false
  }
}

const deleteKnowledgeFile = async (file, mode) => {
  const label = mode === 'delete_and_reimport' ? '删除并从 Milvus 重导' : '仅删除本地文件'
  const confirmed = window.confirm(`确认执行：${label}？\n\n${file.relative_path}`)
  if (!confirmed) {
    return
  }

  deletingFilePath.value = file.relative_path
  deletingMode.value = mode
  clearMessages()

  try {
    const query = new URLSearchParams({
      relative_path: file.relative_path,
      mode,
    })
    const response = await fetch(`/api/study-assistant/knowledge-file?${query.toString()}`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeaders(),
      },
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '删除知识文件失败。')
    }

    successMessage.value = mode === 'delete_and_reimport'
      ? `已删除 ${file.name}，并同步更新 Milvus。`
      : `已删除本地文件：${file.name}`
    if (previewData.value?.relative_path === file.relative_path) {
      clearPreview()
    }
    await fetchStatus()
  } catch (error) {
    errorMessage.value = error.message || '删除知识文件失败。'
  } finally {
    deletingFilePath.value = ''
    deletingMode.value = ''
  }
}

const previewKnowledgeFile = async (file) => {
  previewLoadingPath.value = file.relative_path
  clearMessages()
  try {
    const query = new URLSearchParams({
      relative_path: file.relative_path,
    })
    const response = await fetch(`/api/study-assistant/knowledge-file-preview?${query.toString()}`, {
      headers: {
        ...getAuthHeaders(),
      },
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '预览知识文件失败。')
    }
    previewData.value = data.data || null
  } catch (error) {
    errorMessage.value = error.message || '预览知识文件失败。'
  } finally {
    previewLoadingPath.value = ''
  }
}

const generatePlan = async () => {
  planning.value = true
  clearMessages()
  try {
    const response = await fetch('/api/study-assistant/plan', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        goal: goal.value,
      }),
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '生成学习计划失败。')
    }
    planData.value = data.data
    successMessage.value = '学习计划已生成。'
  } catch (error) {
    errorMessage.value = error.message || '生成学习计划失败。'
  } finally {
    planning.value = false
  }
}

const buildStepPayload = (step) => {
  if (step.tool_command === 'start_pomodoro') {
    return {
      title: step.title,
      focus_minutes: step.duration_minutes,
      break_minutes: 5,
      rounds: 1,
    }
  }
  if (step.tool_command === 'play_music') {
    return {
      category: planData.value?.music_category || 'focus',
    }
  }
  if (step.tool_command === 'tts_reminder') {
    return {
      message: `请开始：${step.title}`,
    }
  }
  return {}
}

const base64ToBlobUrl = (base64, mimeType) => {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index)
  }
  return URL.createObjectURL(new Blob([bytes], { type: mimeType }))
}

const executeTool = async (command, payload = {}) => {
  clearMessages()
  updatePomodoroDebug(command, payload)

  if (command === 'pause_pomodoro') {
    activePomodoroSessions.value = activePomodoroSessions.value.map((session) => (
      session.session_id === payload.session_id ? { ...session, status: 'paused' } : session
    ))
  }

  if (command === 'resume_pomodoro') {
    activePomodoroSessions.value = activePomodoroSessions.value.map((session) => (
      session.session_id === payload.session_id ? { ...session, status: 'focus' } : session
    ))
  }
  try {
    const response = await fetch('/api/study-assistant/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        command,
        payload,
      }),
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '执行工具失败。')
    }
    const result = data.data || {}
    updatePomodoroDebug(command, payload, result)
    successMessage.value = result.message || '工具执行成功。'

    if (command === 'play_music' && result.track?.url) {
      revokeCurrentAudio()
      currentAudioUrl.value = result.track.url
      await new Promise((resolve) => window.setTimeout(resolve, 0))
      if (musicAudio.value?.play) {
        try {
          await musicAudio.value.play()
        } catch (playError) {
          console.warn('Music autoplay failed:', playError)
        }
      }
    }

    if (command === 'tts_reminder' && result.audio_base64) {
      revokeCurrentAudio()
      currentAudioUrl.value = base64ToBlobUrl(result.audio_base64, result.audio_format || 'audio/mpeg')
    }

    if (command === 'start_pomodoro' && result.session) {
      activePomodoroSessions.value = [
        ...activePomodoroSessions.value.filter((session) => session.session_id !== result.session.session_id),
        result.session,
      ]
    }

    if ((command === 'pause_pomodoro' || command === 'resume_pomodoro') && result.session) {
      activePomodoroSessions.value = activePomodoroSessions.value.map((session) => (
        session.session_id === result.session.session_id ? result.session : session
      ))
    }

    if (command === 'stop_pomodoro' && result.session_id) {
      activePomodoroSessions.value = activePomodoroSessions.value.filter((session) => session.session_id !== result.session_id)
    }

    await fetchStatus()
  } catch (error) {
    errorMessage.value = error.message || '执行工具失败。'
  }
}

onMounted(() => {
  fetchStatus()
  countdownTimer = window.setInterval(() => {
    nowTick.value = Date.now()
    if (activePomodoroSessions.value.length) {
      activePomodoroSessions.value = activePomodoroSessions.value.map((session) => {
        if (session.status === 'paused') {
          return session
        }
        return {
          ...session,
          remaining_seconds: Math.max(0, Number(session.remaining_seconds || 0) - 1),
        }
      })
    }
  }, 1000)
  statusSyncTimer = window.setInterval(() => {
    if (activePomodoroSessions.value.length) {
      fetchStatus()
    }
  }, 15000)
})

onBeforeUnmount(() => {
  revokeCurrentAudio()
  if (countdownTimer) {
    window.clearInterval(countdownTimer)
  }
  if (statusSyncTimer) {
    window.clearInterval(statusSyncTimer)
  }
})
</script>
