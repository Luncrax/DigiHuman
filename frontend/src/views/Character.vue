<template>
  <div class="tts-lab-page">
    <section class="tts-lab-shell">
      <div class="hero-block">
        <div>
          <p class="eyebrow">Character Studio</p>
          <h1 class="hero-title">角色配置与 EdgeTTS 测试台</h1>
          <p class="hero-copy">
            在这里保存角色的 system prompt 和情绪表达风格，并直接测试 EdgeTTS 的声音、语速、音调和音量。
          </p>
        </div>

        <div class="hero-meta">
          <div class="meta-card">
            <span class="meta-label">当前主 TTS</span>
            <strong>EdgeTTS</strong>
          </div>
          <div class="meta-card">
            <span class="meta-label">默认音色</span>
            <strong class="truncate-path">{{ form.voice }}</strong>
          </div>
        </div>
      </div>

      <div class="panel-strong panel-form">
        <div class="panel-header">
          <h2>角色配置</h2>
          <p>保存后，聊天页下一轮对话会自动使用新的角色设定。</p>
        </div>

        <el-form label-position="top" class="tts-form">
          <el-form-item label="LLM system prompt">
            <el-input
              v-model="characterConfig.llm_system_prompt"
              type="textarea"
              :rows="6"
              placeholder="例如：你是一位温柔、可靠、带一点成熟幽默感的虚拟人助手。"
            />
          </el-form-item>

          <el-form-item label="情绪表达风格">
            <el-input
              v-model="characterConfig.emotion_style"
              type="textarea"
              :rows="4"
              placeholder="例如：表达情绪时更自然、克制、偏陪伴感，不要过度夸张。"
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
            <h2>EdgeTTS 参数</h2>
            <p>直接测试不同音色和语音参数，优先追求低延迟和稳定播放。</p>
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
              <el-form-item label="中文音色">
                <el-select v-model="form.voice">
                  <el-option label="zh-CN-YunxiNeural" value="zh-CN-YunxiNeural" />
                  <el-option label="zh-CN-XiaoxiaoNeural" value="zh-CN-XiaoxiaoNeural" />
                  <el-option label="zh-CN-YunjianNeural" value="zh-CN-YunjianNeural" />
                  <el-option label="zh-CN-XiaoyiNeural" value="zh-CN-XiaoyiNeural" />
                </el-select>
              </el-form-item>

              <el-form-item label="模式">
                <el-input :model-value="'edge_tts'" disabled />
              </el-form-item>
            </div>

            <div class="inline-grid">
              <el-form-item label="语速">
                <el-input v-model="form.rate" placeholder="例如：+0% / -15% / +20%" />
              </el-form-item>

              <el-form-item label="音调">
                <el-input v-model="form.pitch" placeholder="例如：+0Hz / -30Hz / +40Hz" />
              </el-form-item>
            </div>

            <div class="inline-grid">
              <el-form-item label="音量">
                <el-input v-model="form.volume" placeholder="例如：+0% / -10% / +20%" />
              </el-form-item>

              <el-form-item label="情绪标签（仅展示）">
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
            </div>

            <div class="action-row">
              <el-button type="primary" :loading="loading" @click="runTest">开始测试</el-button>
              <el-button :loading="abLoading" @click="runABTest">AB 对比音色</el-button>
              <el-button :disabled="!audioUrl" @click="playAudio">播放结果</el-button>
              <el-button :disabled="!audioUrl" @click="stopAudio">停止播放</el-button>
            </div>
          </el-form>
        </div>

        <div class="panel-strong panel-result">
          <div class="panel-header">
            <h2>测试结果</h2>
            <p>重点关注耗时、音色和音频大小。</p>
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
                <span>音色</span>
                <strong>{{ result.voice || '--' }}</strong>
              </div>
              <div class="detail-row">
                <span>语速</span>
                <strong>{{ result.rate || '--' }}</strong>
              </div>
              <div class="detail-row">
                <span>音调</span>
                <strong>{{ result.pitch || '--' }}</strong>
              </div>
              <div class="detail-row">
                <span>音量</span>
                <strong>{{ result.volume || '--' }}</strong>
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
                :key="item.voice"
                class="ab-card"
                :class="{ active: activeABVoice === item.voice }"
              >
                <div class="ab-topline">
                  <strong>{{ item.voice }}</strong>
                  <span>{{ item.elapsed_ms ? `${item.elapsed_ms} ms` : '--' }}</span>
                </div>
                <div class="ab-meta">
                  <span>状态：{{ item.status }}</span>
                  <span>大小：{{ item.audio_size ? `${item.audio_size} bytes` : '--' }}</span>
                </div>
                <div class="ab-actions">
                  <el-button size="small" @click="playABAudio(item.voice)">播放</el-button>
                  <el-button size="small" @click="useABResult(item.voice)">设为主结果</el-button>
                </div>
                <p v-if="item.message" class="ab-message">{{ item.message }}</p>
              </div>
            </div>

            <div class="tip-card">
              <p>说明：</p>
              <p>EdgeTTS 更适合你现在的实时聊天场景，延迟通常会明显低于 Qwen3-TTS。</p>
              <p>如果后面你还想做更强的情绪表达，我们可以再用 rate / pitch / volume 做一层轻量情绪映射。</p>
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
  text: '你好，我现在在做 EdgeTTS 测试。',
  mode: 'edge_tts',
  voice: 'zh-CN-XiaoxiaoNeural',
  emotion: 'neutral',
  intensity: 'low',
  rate: '+0%',
  pitch: '+0Hz',
  volume: '+0%',
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
  rate: '',
  pitch: '',
  volume: '',
  message: '',
})
const abResults = ref([])
const activeABVoice = ref('')

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
  result.rate = ''
  result.pitch = ''
  result.volume = ''
  result.message = ''
}

const buildAudioUrl = async (audioBase64, audioFormat = 'audio/mpeg') => {
  const mime = audioFormat || 'audio/mpeg'
  const binary = atob(audioBase64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  revokeAudioUrl()
  audioUrl.value = URL.createObjectURL(new Blob([bytes], { type: mime }))
}

const buildStandaloneAudioUrl = (audioBase64, audioFormat = 'audio/mpeg') => {
  const mime = audioFormat || 'audio/mpeg'
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
    ElMessage.success('角色配置已保存，聊天页下一轮会自动生效')
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
      mode: 'edge_tts',
      voice: form.voice,
      emotion: form.emotion,
      intensity: form.intensity,
      rate: form.rate,
      pitch: form.pitch,
      volume: form.volume,
    })
    result.status = data.status || 'error'
    result.elapsed_ms = data.elapsed_ms ?? null
    result.audio_size = data.audio_size ?? null
    result.mode = data.mode || 'edge_tts'
    result.voice = data.voice || form.voice
    result.rate = data.rate || form.rate
    result.pitch = data.pitch || form.pitch
    result.volume = data.volume || form.volume
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
  activeABVoice.value = ''
  revokeABAudioUrls()

  const voices = ['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural']

  try {
    const settled = await Promise.all(
      voices.map(async (voice) => {
        const data = await requestTTSTest({
          text: form.text,
          mode: 'edge_tts',
          voice,
          emotion: form.emotion,
          intensity: form.intensity,
          rate: form.rate,
          pitch: form.pitch,
          volume: form.volume,
        })

        if (data.audio_base64) {
          abAudioUrls.value[voice] = buildStandaloneAudioUrl(data.audio_base64, data.audio_format)
        }

        return {
          voice,
          status: data.status || 'error',
          elapsed_ms: data.elapsed_ms ?? null,
          audio_size: data.audio_size ?? null,
          message: data.message || '',
          rate: data.rate || form.rate,
          pitch: data.pitch || form.pitch,
          volume: data.volume || form.volume,
        }
      })
    )

    abResults.value = settled
    activeABVoice.value = settled[0]?.voice || ''
  } catch (error) {
    abResults.value = [{
      voice: 'compare',
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

const playABAudio = async (voice) => {
  await useABResult(voice)
  if (!audioRef.value) {
    return
  }
  await audioRef.value.play()
}

const useABResult = async (voice) => {
  const url = abAudioUrls.value[voice]
  const selected = abResults.value.find((item) => item.voice === voice)
  if (!url || !selected) {
    return
  }
  revokeAudioUrl()
  audioUrl.value = url
  activeABVoice.value = voice
  result.status = selected.status
  result.elapsed_ms = selected.elapsed_ms
  result.audio_size = selected.audio_size
  result.mode = 'edge_tts'
  result.voice = selected.voice
  result.rate = selected.rate || form.rate
  result.pitch = selected.pitch || form.pitch
  result.volume = selected.volume || form.volume
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
