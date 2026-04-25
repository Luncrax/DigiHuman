<template>
  <div class="tts-lab-page">
    <section class="tts-lab-shell">
      <div class="hero-block">
        <div>
          <p class="eyebrow">Character Studio</p>
          <h1 class="hero-title">角色配置与 TTS 测试台</h1>
          <p class="hero-copy">
            先保存角色的 LLM system prompt 和情绪表达风格，再用同一页面直接测试语音效果和耗时。
          </p>
        </div>

        <div class="hero-meta">
          <div class="meta-card">
            <span class="meta-label">当前主模式</span>
            <strong>custom_voice</strong>
          </div>
          <div class="meta-card">
            <span class="meta-label">Prompt 文件</span>
            <strong class="truncate-path">voice_clone_prompt_wzc.pt</strong>
          </div>
        </div>
      </div>

      <div class="panel-strong panel-form">
        <div class="panel-header">
          <h2>角色配置</h2>
          <p>这里保存后，聊天页下一轮对话会自动使用新的 system prompt 和情绪表达风格。</p>
        </div>

        <el-form label-position="top" class="tts-form">
          <el-form-item label="LLM system prompt">
            <el-input
              v-model="characterConfig.llm_system_prompt"
              type="textarea"
              :rows="6"
              placeholder="例如：你是一位温柔、可靠、带一点成熟幽默感的虚拟人助手。回答时保持陪伴感。"
            />
          </el-form-item>

          <el-form-item label="情绪表达风格">
            <el-input
              v-model="characterConfig.emotion_style"
              type="textarea"
              :rows="4"
              placeholder="例如：表达情绪时更自然、轻柔、偏陪伴感，不要过度夸张。"
            />
          </el-form-item>

          <div class="action-row">
            <el-button type="primary" :loading="configSaving" @click="saveCharacterConfig">保存角色配置</el-button>
            <el-button :loading="configLoading" @click="loadCharacterConfig">重新读取</el-button>
          </div>
        </el-form>
      </div>

      <div class="lab-grid">
        <div class="panel-strong panel-form">
          <div class="panel-header">
            <h2>测试参数</h2>
            <p>直接切换模式，判断速度和声音差异。</p>
          </div>

          <el-form label-position="top" class="tts-form">
            <el-form-item label="测试文本">
              <el-input
                v-model="form.text"
                type="textarea"
                :rows="5"
                placeholder="输入一段你想测试的文案"
              />
            </el-form-item>

            <div class="inline-grid">
              <el-form-item label="模式">
                <el-select v-model="form.mode">
                  <el-option label="custom_voice（推荐，主链路）" value="custom_voice" />
                  <el-option label="prompt_clone（Base + .pt）" value="prompt_clone" />
                  <el-option label="voice_design" value="voice_design" />
                </el-select>
              </el-form-item>

              <el-form-item label="说话人">
                <el-input v-model="form.voice" />
              </el-form-item>
            </div>

            <div class="inline-grid">
              <el-form-item label="情绪">
                <el-select v-model="form.emotion">
                  <el-option label="neutral" value="neutral" />
                  <el-option label="joy" value="joy" />
                  <el-option label="sadness" value="sadness" />
                  <el-option label="anger" value="anger" />
                  <el-option label="surprise" value="surprise" />
                  <el-option label="fear" value="fear" />
                  <el-option label="shy" value="shy" />
                </el-select>
              </el-form-item>

              <el-form-item label="强度">
                <el-select v-model="form.intensity">
                  <el-option label="low" value="low" />
                  <el-option label="medium" value="medium" />
                  <el-option label="high" value="high" />
                </el-select>
              </el-form-item>
            </div>

            <el-form-item label="TTS instruct（可选）">
              <el-input
                v-model="form.instruct"
                type="textarea"
                :rows="3"
                placeholder="留空时会由 Emotion Controller 自动生成语气指令"
              />
            </el-form-item>

            <el-form-item label=".pt Prompt 路径（仅 prompt_clone 生效）">
              <el-input v-model="form.voice_prompt_path" />
            </el-form-item>

            <div class="action-row">
              <el-button type="primary" :loading="loading" @click="runTest">开始测试</el-button>
              <el-button :loading="abLoading" @click="runABTest">AB 对比</el-button>
              <el-button :disabled="!audioUrl" @click="playAudio">播放结果</el-button>
              <el-button :disabled="!audioUrl" @click="stopAudio">停止播放</el-button>
            </div>
          </el-form>
        </div>

        <div class="panel-strong panel-result">
          <div class="panel-header">
            <h2>测试结果</h2>
            <p>重点看耗时、实际模式和输出音频。</p>
          </div>

          <div class="result-stack">
            <div class="result-kpis">
              <div class="kpi-card">
                <span class="meta-label">状态</span>
                <strong>{{ result.status || '未开始' }}</strong>
              </div>
              <div class="kpi-card">
                <span class="meta-label">耗时</span>
                <strong>{{ result.elapsed_ms ? `${result.elapsed_ms} ms` : '--' }}</strong>
              </div>
              <div class="kpi-card">
                <span class="meta-label">音频大小</span>
                <strong>{{ result.audio_size ? `${result.audio_size} bytes` : '--' }}</strong>
              </div>
            </div>

            <div class="detail-card">
              <div class="detail-row">
                <span>实际模式</span>
                <strong>{{ result.mode || '--' }}</strong>
              </div>
              <div class="detail-row">
                <span>说话人</span>
                <strong>{{ result.voice || '--' }}</strong>
              </div>
              <div class="detail-row">
                <span>Prompt 路径</span>
                <strong class="truncate-path">{{ result.voice_prompt_path || '--' }}</strong>
              </div>
            </div>

            <el-alert
              v-if="result.message"
              :title="result.message"
              :type="result.status === 'error' ? 'error' : 'info'"
              :closable="false"
              show-icon
            />

            <audio
              v-if="audioUrl || abResults.length"
              ref="audioRef"
              :src="audioUrl"
              controls
              preload="metadata"
              class="audio-player"
            ></audio>

            <div v-if="abResults.length" class="ab-grid">
              <div
                v-for="item in abResults"
                :key="item.mode"
                class="ab-card"
                :class="{ active: activeABMode === item.mode }"
              >
                <div class="ab-topline">
                  <strong>{{ item.mode }}</strong>
                  <span>{{ item.elapsed_ms ? `${item.elapsed_ms} ms` : '--' }}</span>
                </div>
                <div class="ab-meta">
                  <span>状态：{{ item.status }}</span>
                  <span>大小：{{ item.audio_size ? `${item.audio_size} bytes` : '--' }}</span>
                </div>
                <div class="ab-actions">
                  <el-button size="small" @click="playABAudio(item.mode)">播放</el-button>
                  <el-button size="small" @click="useABResult(item.mode)">设为主结果</el-button>
                </div>
                <p v-if="item.message" class="ab-message">{{ item.message }}</p>
              </div>
            </div>

            <div class="tip-card">
              <p>说明：</p>
              <p>`custom_voice` 是当前聊天主链路，通常更快更稳定。</p>
              <p>`prompt_clone` 会走 `Base + voice_clone_prompt_wzc.pt`，更适合单独比对音色相似度。</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

const characterConfig = reactive({
  llm_system_prompt: '',
  emotion_style: '',
})
const form = reactive({
  text: '你好，我现在在做音色对比测试。',
  mode: 'custom_voice',
  voice: 'Vivian',
  emotion: 'neutral',
  intensity: 'low',
  instruct: '',
  voice_prompt_path: '/mnt/e/big_work/DigiHuman/backend/tts/voice_clone_prompt_wzc.pt',
})

const loading = ref(false)
const abLoading = ref(false)
const configLoading = ref(false)
const configSaving = ref(false)
const result = reactive({
  status: '',
  elapsed_ms: null,
  audio_size: null,
  mode: '',
  voice: '',
  voice_prompt_path: '',
  message: '',
})
const abResults = ref([])
const activeABMode = ref('')

const audioRef = ref(null)
const audioUrl = ref('')
const abAudioUrls = ref({})

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

const revokeAudioUrl = () => {
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = ''
  }
}

const revokeABAudioUrls = () => {
  Object.values(abAudioUrls.value).forEach((url) => {
    if (url) {
      URL.revokeObjectURL(url)
    }
  })
  abAudioUrls.value = {}
}

const resetResult = () => {
  result.status = ''
  result.elapsed_ms = null
  result.audio_size = null
  result.mode = ''
  result.voice = ''
  result.voice_prompt_path = ''
  result.message = ''
}

const buildAudioUrl = async (audioBase64, audioFormat = 'audio/wav') => {
  const mime = audioFormat || 'audio/wav'
  const binary = atob(audioBase64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  revokeAudioUrl()
  audioUrl.value = URL.createObjectURL(new Blob([bytes], { type: mime }))
}

const buildStandaloneAudioUrl = (audioBase64, audioFormat = 'audio/wav') => {
  const mime = audioFormat || 'audio/wav'
  const binary = atob(audioBase64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return URL.createObjectURL(new Blob([bytes], { type: mime }))
}

const requestTTSTest = async (payload) => {
  const response = await fetch('/api/tts/test', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  return parseJsonResponse(response, 'TTS 测试接口返回格式错误')
}

const loadCharacterConfig = async () => {
  configLoading.value = true
  try {
    const response = await fetch('/api/character-config')
    const data = await parseJsonResponse(response, '角色配置接口返回格式错误')
    const config = data.config || {}
    characterConfig.llm_system_prompt = config.llm_system_prompt || ''
    characterConfig.emotion_style = config.emotion_style || ''
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '读取角色配置失败')
  } finally {
    configLoading.value = false
  }
}

const saveCharacterConfig = async () => {
  configSaving.value = true
  try {
    const response = await fetch('/api/character-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        llm_system_prompt: characterConfig.llm_system_prompt,
        emotion_style: characterConfig.emotion_style,
      }),
    })
    const data = await parseJsonResponse(response, '保存角色配置失败')
    if (data.status !== 'ok') {
      throw new Error(data.message || '保存角色配置失败')
    }
    ElMessage.success('角色配置已保存，新的聊天会自动生效')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存角色配置失败')
  } finally {
    configSaving.value = false
  }
}

const runTest = async () => {
  loading.value = true
  resetResult()
  revokeAudioUrl()

  try {
    const data = await requestTTSTest({
      text: form.text,
      mode: form.mode,
      voice: form.voice,
      emotion: form.emotion,
      intensity: form.intensity,
      instruct: form.instruct || null,
      voice_prompt_path: form.mode === 'prompt_clone' ? form.voice_prompt_path : null,
    })
    result.status = data.status || 'error'
    result.elapsed_ms = data.elapsed_ms ?? null
    result.audio_size = data.audio_size ?? null
    result.mode = data.mode || form.mode
    result.voice = data.voice || form.voice
    result.voice_prompt_path = data.voice_prompt_path || ''
    result.message = data.message || ''

    if (data.audio_base64) {
      await buildAudioUrl(data.audio_base64, data.audio_format)
    }
  } catch (error) {
    result.status = 'error'
    result.message = error instanceof Error ? error.message : '测试请求失败'
  } finally {
    loading.value = false
  }
}

const runABTest = async () => {
  abLoading.value = true
  abResults.value = []
  activeABMode.value = ''
  revokeABAudioUrls()

  const modes = [
    {
      mode: 'custom_voice',
      voice_prompt_path: null,
    },
    {
      mode: 'prompt_clone',
      voice_prompt_path: form.voice_prompt_path,
    },
  ]

  try {
    const settled = await Promise.all(
      modes.map(async (item) => {
        const data = await requestTTSTest({
          text: form.text,
          mode: item.mode,
          voice: form.voice,
          emotion: form.emotion,
          intensity: form.intensity,
          instruct: form.instruct || null,
          voice_prompt_path: item.voice_prompt_path,
        })

        if (data.audio_base64) {
          abAudioUrls.value[item.mode] = buildStandaloneAudioUrl(data.audio_base64, data.audio_format)
        }

        return {
          mode: item.mode,
          status: data.status || 'error',
          elapsed_ms: data.elapsed_ms ?? null,
          audio_size: data.audio_size ?? null,
          message: data.message || '',
        }
      })
    )

    abResults.value = settled
    activeABMode.value = settled[0]?.mode || ''
  } catch (error) {
    abResults.value = [{
      mode: 'compare',
      status: 'error',
      elapsed_ms: null,
      audio_size: null,
      message: error instanceof Error ? error.message : 'AB 对比失败',
    }]
  } finally {
    abLoading.value = false
  }
}

const playAudio = async () => {
  if (!audioRef.value) {
    return
  }
  await audioRef.value.play()
}

const stopAudio = () => {
  if (!audioRef.value) {
    return
  }
  audioRef.value.pause()
  audioRef.value.currentTime = 0
}

const playABAudio = async (mode) => {
  await useABResult(mode)
  if (!audioRef.value) {
    return
  }
  await audioRef.value.play()
}

const useABResult = async (mode) => {
  const url = abAudioUrls.value[mode]
  const selected = abResults.value.find((item) => item.mode === mode)
  if (!url || !selected) {
    return
  }
  revokeAudioUrl()
  audioUrl.value = url
  activeABMode.value = mode
  result.status = selected.status
  result.elapsed_ms = selected.elapsed_ms
  result.audio_size = selected.audio_size
  result.mode = selected.mode
  result.voice = form.voice
  result.voice_prompt_path = mode === 'prompt_clone' ? form.voice_prompt_path : ''
  result.message = selected.message || ''
}

onBeforeUnmount(() => {
  stopAudio()
  revokeAudioUrl()
  revokeABAudioUrls()
})

onMounted(() => {
  loadCharacterConfig()
})
</script>

<style scoped>
.tts-lab-page {
  padding: 104px 24px 40px;
}

.tts-lab-shell {
  max-width: 1240px;
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
  background:
    radial-gradient(circle at top left, rgba(255, 241, 212, 0.92), transparent 38%),
    linear-gradient(135deg, rgba(255, 250, 240, 0.95), rgba(244, 231, 214, 0.92));
  border: 1px solid rgba(71, 48, 26, 0.08);
  box-shadow: 0 24px 70px rgba(71, 48, 26, 0.12);
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(104, 72, 40, 0.76);
}

.hero-title {
  margin: 0;
  font-size: clamp(2rem, 3vw, 3rem);
  line-height: 1;
  color: #1f150d;
}

.hero-copy {
  margin: 12px 0 0;
  max-width: 680px;
  color: rgba(31, 21, 13, 0.74);
  font-size: 1rem;
}

.hero-meta {
  display: grid;
  gap: 12px;
  min-width: 250px;
}

.meta-card,
.kpi-card,
.detail-card,
.tip-card {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(71, 48, 26, 0.08);
  box-shadow: 0 12px 30px rgba(71, 48, 26, 0.08);
}

.meta-card {
  padding: 16px 18px;
  display: grid;
  gap: 6px;
}

.meta-label {
  font-size: 0.76rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(95, 69, 45, 0.62);
}

.truncate-path {
  word-break: break-all;
}

.lab-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 24px;
}

.panel-form,
.panel-result {
  padding: 24px;
  border-radius: 28px;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.35rem;
  color: var(--text);
}

.panel-header p {
  margin: 8px 0 0;
  color: var(--muted);
}

.tts-form {
  margin-top: 20px;
}

.inline-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.result-stack {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.result-kpis {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  padding: 16px;
  display: grid;
  gap: 8px;
}

.detail-card {
  padding: 18px;
  display: grid;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--text);
}

.audio-player {
  width: 100%;
}

.tip-card {
  padding: 18px;
  display: grid;
  gap: 6px;
  color: rgba(31, 21, 13, 0.74);
}

.tip-card p {
  margin: 0;
}

.ab-grid {
  display: grid;
  gap: 12px;
}

.ab-card {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(71, 48, 26, 0.08);
  box-shadow: 0 10px 24px rgba(71, 48, 26, 0.08);
}

.ab-card.active {
  border-color: rgba(213, 133, 44, 0.45);
  box-shadow: 0 14px 30px rgba(213, 133, 44, 0.16);
}

.ab-topline,
.ab-meta,
.ab-actions {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.ab-topline {
  margin-bottom: 8px;
  color: var(--text);
}

.ab-meta {
  margin-bottom: 12px;
  color: var(--muted);
  font-size: 0.92rem;
}

.ab-actions {
  justify-content: flex-start;
}

.ab-message {
  margin: 10px 0 0;
  color: #9f3b2f;
  font-size: 0.92rem;
}

@media (max-width: 960px) {
  .tts-lab-page {
    padding: 92px 16px 24px;
  }

  .hero-block,
  .lab-grid,
  .inline-grid,
  .result-kpis {
    grid-template-columns: 1fr;
  }
}
</style>
