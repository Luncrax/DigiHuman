<template>
  <div
    class="live2d-wrapper"
    :class="{ hidden: !showCharacter, dragging: dragState.isDragging }"
    :style="wrapperStyle"
  >
    <div ref="canvasRef" class="live2d-canvas"></div>

    <div
      class="drag-handle"
      title="拖动 Live2D"
      @pointerdown="startDrag"
    >
      <span class="drag-dot"></span>
      <span class="drag-dot"></span>
      <span class="drag-dot"></span>
      <span class="drag-label">拖动舞台</span>
    </div>

    <div
      v-if="currentEmotion"
      class="emotion-indicator"
      :class="[currentEmotion, `state-${currentState}`]"
    >
      <span class="emotion-icon">{{ getEmotionIcon(currentEmotion) }}</span>
      <span class="emotion-text">{{ getEmotionText(currentEmotion) }}</span>
      <span class="state-badge">{{ currentState }}</span>
    </div>

    <div class="live2d-controls">
      <el-button circle size="small" class="control-btn" title="显示/隐藏" @click="toggleCharacter">
        <el-icon>
          <View v-if="showCharacter" />
          <Hide v-else />
        </el-icon>
      </el-button>
      <el-button circle size="small" class="control-btn" title="动作演示" @click="playMotion('mtn_01')">
        <el-icon><VideoPlay /></el-icon>
      </el-button>
      <el-button circle size="small" class="control-btn" title="说话演示" @click="simulateTalk">
        <el-icon><Microphone /></el-icon>
      </el-button>
      <el-button circle size="small" class="control-btn" title="重置" @click="resetToNeutral">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { View, Hide, Microphone, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { createPixiLive2d } from '@/lib/live2d/pixiLive2d'

const showCharacter = ref(true)
const currentEmotion = ref('neutral')
const currentState = ref('idle')
const canvasRef = ref(null)

let live2dRuntime = null
let currentProfile = null
let activeCommand = null
let speechContext = null
let speechActive = false
let reactTimer = null
let talkFallbackTimer = null
let tweenFrame = null
let lipSyncValue = 0
const DEFAULT_POSITION = { x: 0, y: 48 }
const dragState = ref({
  isDragging: false,
  startX: 0,
  startY: 0,
  offsetX: DEFAULT_POSITION.x,
  offsetY: DEFAULT_POSITION.y,
})
let parameterState = {
  angle_x: 0,
  angle_y: 0,
  angle_z: 0,
  eye_l_open: 1,
  eye_r_open: 1,
  eye_ball_x: 0,
  eye_ball_y: 0,
  mouth_open: 0,
  breath: 0.4,
}

const wrapperStyle = computed(() => ({
  left: `${dragState.value.offsetX}px`,
  bottom: 'auto',
  top: `${dragState.value.offsetY}px`,
}))

const STATE_PRIORITY = {
  idle: 0,
  talk: 1,
  react: 2,
}

const emotionAliases = {
  happy: 'joy',
  sad: 'sadness',
  angry: 'anger',
  surprised: 'surprise',
  scared: 'fear',
  shy: 'shy',
}

const emotionIcons = {
  joy: '😊',
  sadness: '😢',
  anger: '😠',
  surprise: '😮',
  fear: '😰',
  disgust: '😒',
  shy: '☺️',
  neutral: '😌',
}

const emotionTexts = {
  joy: '开心',
  sadness: '难过',
  anger: '生气',
  surprise: '惊讶',
  fear: '紧张',
  disgust: '嫌弃',
  shy: '害羞',
  neutral: '平静',
}

const normalizeEmotion = (emotion) => {
  if (!emotion) {
    return 'neutral'
  }

  return emotionAliases[emotion] || emotion
}

const getEmotionIcon = (emotion) => emotionIcons[normalizeEmotion(emotion)] || emotionIcons.neutral
const getEmotionText = (emotion) => emotionTexts[normalizeEmotion(emotion)] || emotionTexts.neutral

const clearTimer = (timer) => {
  if (timer) {
    window.clearTimeout(timer)
  }
  return null
}

const persistDragPosition = () => {
  localStorage.setItem(
    'digihuman_live2d_position',
    JSON.stringify({
      x: dragState.value.offsetX,
      y: dragState.value.offsetY,
    })
  )
}

const clampDragPosition = (x, y) => {
  const canvasWidth = canvasRef.value?.clientWidth || 560
  const canvasHeight = canvasRef.value?.clientHeight || 760
  const maxX = Math.max(0, window.innerWidth - canvasWidth + 80)
  const maxY = Math.max(0, window.innerHeight - canvasHeight + 120)

  return {
    x: Math.min(Math.max(x, -160), maxX),
    y: Math.min(Math.max(y, 24), maxY),
  }
}

const handleDragMove = (event) => {
  if (!dragState.value.isDragging) {
    return
  }

  const nextPosition = clampDragPosition(
    event.clientX - dragState.value.startX,
    event.clientY - dragState.value.startY
  )

  dragState.value = {
    ...dragState.value,
    offsetX: nextPosition.x,
    offsetY: nextPosition.y,
  }
}

const stopDrag = () => {
  if (!dragState.value.isDragging) {
    return
  }

  dragState.value = {
    ...dragState.value,
    isDragging: false,
  }
  persistDragPosition()
}

const startDrag = (event) => {
  event.preventDefault()

  dragState.value = {
    ...dragState.value,
    isDragging: true,
    startX: event.clientX - dragState.value.offsetX,
    startY: event.clientY - dragState.value.offsetY,
  }
}

const mergeParameters = (...parameterSets) => {
  return parameterSets.reduce((acc, item) => {
    Object.entries(item || {}).forEach(([key, value]) => {
      const numeric = Number(value)
      if (!Number.isNaN(numeric)) {
        acc[key] = numeric
      }
    })
    return acc
  }, {})
}

const tweenParameters = (target = {}, duration = 320) => {
  if (!live2dRuntime) {
    return
  }

  const to = mergeParameters(parameterState, target)
  const from = { ...parameterState }
  const startAt = performance.now()

  if (tweenFrame) {
    cancelAnimationFrame(tweenFrame)
  }

  const step = (now) => {
    const progress = Math.min(1, (now - startAt) / Math.max(duration, 1))
    const eased = 1 - Math.pow(1 - progress, 3)
    const frame = {}

    Object.keys(to).forEach((key) => {
      const start = Number(from[key] ?? 0)
      const end = Number(to[key] ?? 0)
      frame[key] = start + (end - start) * eased
    })

    if (speechActive) {
      frame.mouth_open = Math.max(frame.mouth_open ?? 0, lipSyncValue)
    }

    parameterState = frame
    live2dRuntime.updateParameters(frame)

    if (progress < 1) {
      tweenFrame = requestAnimationFrame(step)
    } else {
      tweenFrame = null
    }
  }

  tweenFrame = requestAnimationFrame(step)
}

const applyLipSync = (mouthOpen = 0) => {
  lipSyncValue = Math.max(0, Math.min(1, Number(mouthOpen) || 0))
  if (!live2dRuntime || !speechActive) {
    return
  }

  const frame = {
    ...parameterState,
    mouth_open: Math.max(parameterState.mouth_open ?? 0, lipSyncValue),
  }
  live2dRuntime.updateParameters(frame)
}

const deriveProfile = (command = {}) => {
  const emotion = normalizeEmotion(command.emotion)
  const expression = command.expression || 'exp_01'
  const durationMs = Math.max(900, Number(command.duration ? command.duration * 1000 : command.speech_duration_ms || 2200))
  const transitionMs = Math.max(160, Number(command.transition_ms || 320))
  const baseParameters = mergeParameters(command.parameters)
  const idleParameters = mergeParameters(baseParameters, command.idle_parameters, { mouth_open: 0, breath: baseParameters.breath ?? 0.4 })
  const talkParameters = mergeParameters(baseParameters, command.talk_parameters)
  const reactParameters = mergeParameters(baseParameters, command.react_parameters)

  return {
    emotion,
    priority: Number(command.priority ?? STATE_PRIORITY[command.state || 'react'] ?? 0),
    durationMs,
    transitionMs,
    recoverTo: command.recover_to || 'idle',
    idle: {
      motion: command.idle_motion || 'idle',
      expression: command.idle_expression || expression,
      parameters: idleParameters,
    },
    talk: {
      motion: command.talk_motion || 'talk',
      expression: command.talk_expression || expression,
      parameters: talkParameters,
      durationMs: Number(command.speech_duration_ms || durationMs),
    },
    react: {
      motion: command.react_motion || command.motion || 'idle',
      expression,
      parameters: reactParameters,
    },
  }
}

const applyStateProfile = async (stateName, profile) => {
  if (!live2dRuntime || !profile) {
    return
  }

  const target = profile[stateName]
  if (!target) {
    return
  }

  currentState.value = stateName
  currentEmotion.value = profile.emotion || 'neutral'

  if (target.expression) {
    await live2dRuntime.setExpression(target.expression).catch((error) => {
      console.error('Failed to set expression:', error)
    })
  }

  if (target.motion) {
    await live2dRuntime.playMotion(target.motion).catch((error) => {
      console.error('Failed to play motion:', error)
    })
  }

  tweenParameters(target.parameters, profile.transitionMs)
}

const enterIdleState = async (profile = currentProfile) => {
  if (!profile) {
    return
  }

  reactTimer = clearTimer(reactTimer)
  talkFallbackTimer = clearTimer(talkFallbackTimer)
  await applyStateProfile('idle', profile)
}

const enterTalkState = async (profile = speechContext || currentProfile) => {
  if (!profile) {
    return
  }

  if (currentState.value === 'react') {
    speechContext = profile
    return
  }

  await applyStateProfile('talk', profile)
  talkFallbackTimer = clearTimer(talkFallbackTimer)
  talkFallbackTimer = window.setTimeout(() => {
    if (!speechActive) {
      enterIdleState(profile)
    }
  }, profile.talk.durationMs)
}

const enterReactState = async (profile) => {
  if (!profile) {
    return
  }

  currentProfile = profile
  reactTimer = clearTimer(reactTimer)
  await applyStateProfile('react', profile)

  reactTimer = window.setTimeout(() => {
    reactTimer = null
    if (speechActive) {
      enterTalkState(speechContext || profile)
      return
    }

    if (profile.recoverTo === 'idle') {
      enterIdleState(profile)
    }
  }, profile.durationMs)
}

const handleTalkStart = async (detail = {}) => {
  speechActive = true
  if (detail?.emotion || detail?.motion || detail?.talk_motion) {
    speechContext = deriveProfile(detail)
  } else if (!speechContext) {
    speechContext = currentProfile
  }

  if (currentState.value !== 'react') {
    await enterTalkState(speechContext || currentProfile)
  }
}

const handleTalkEnd = async () => {
  speechActive = false
  lipSyncValue = 0
  talkFallbackTimer = clearTimer(talkFallbackTimer)

  if (currentState.value === 'talk') {
    await enterIdleState(currentProfile)
  }
}

const initLive2D = async () => {
  if (!canvasRef.value || live2dRuntime) {
    return
  }

  try {
    live2dRuntime = await createPixiLive2d(canvasRef.value, {
      modelPath: '/live2d_models/Mao/Mao.model3.json',
      scaleMultiplier: 0.74,
    })

    currentProfile = deriveProfile({
      emotion: 'neutral',
      state: 'idle',
      expression: 'exp_01',
      idle_motion: 'idle',
      talk_motion: 'talk',
      react_motion: 'idle',
      parameters: parameterState,
      idle_parameters: parameterState,
      talk_parameters: { ...parameterState, mouth_open: 0.22, breath: 0.45 },
      react_parameters: parameterState,
      duration: 1.2,
    })
    await enterIdleState(currentProfile)

    window.live2dApp = {
      handleCommand: handleEmotionCommand,
      playMotion,
      setExpression,
      resetToNeutral,
      talkStart: handleTalkStart,
      talkEnd: handleTalkEnd,
    }
  } catch (error) {
    console.error('Pixi Live2D initialization failed:', error)
  }
}

const destroyLive2D = () => {
  reactTimer = clearTimer(reactTimer)
  talkFallbackTimer = clearTimer(talkFallbackTimer)
  if (tweenFrame) {
    cancelAnimationFrame(tweenFrame)
    tweenFrame = null
  }

  live2dRuntime?.destroy()
  live2dRuntime = null

  if (window.live2dApp?.handleCommand === handleEmotionCommand) {
    delete window.live2dApp
  }
}

const toggleCharacter = async () => {
  showCharacter.value = !showCharacter.value

  if (showCharacter.value) {
    await nextTick()
    await initLive2D()
    live2dRuntime?.resize()
  }
}

const playMotion = async (motionName) => {
  if (!live2dRuntime) {
    return false
  }

  try {
    await live2dRuntime.playMotion(motionName)
    return true
  } catch (error) {
    console.error('Failed to play motion:', error)
    return false
  }
}

const setExpression = async (expressionName) => {
  if (!live2dRuntime) {
    return false
  }

  try {
    await live2dRuntime.setExpression(expressionName)
    return true
  } catch (error) {
    console.error('Failed to set expression:', error)
    return false
  }
}

const simulateTalk = async () => {
  await handleTalkStart({
    emotion: currentEmotion.value,
    talk_motion: currentProfile?.talk?.motion || 'talk',
    talk_parameters: currentProfile?.talk?.parameters || { mouth_open: 0.3, breath: 0.45 },
    speech_duration_ms: 1200,
  })
  window.setTimeout(() => {
    handleTalkEnd()
  }, 1200)
}

const resetToNeutral = async () => {
  speechActive = false
  speechContext = null
  currentProfile = deriveProfile({
    emotion: 'neutral',
    state: 'idle',
    expression: 'exp_01',
    idle_motion: 'idle',
    talk_motion: 'talk',
    react_motion: 'idle',
    parameters: {
      angle_x: 0,
      angle_y: 0,
      angle_z: 0,
      eye_l_open: 1,
      eye_r_open: 1,
      eye_ball_x: 0,
      eye_ball_y: 0,
      mouth_open: 0,
      breath: 0.4,
    },
    idle_parameters: {
      angle_x: 0,
      angle_y: 0,
      angle_z: 0,
      eye_l_open: 1,
      eye_r_open: 1,
      eye_ball_x: 0,
      eye_ball_y: 0,
      mouth_open: 0,
      breath: 0.4,
    },
    talk_parameters: {
      angle_x: 0,
      angle_y: 0,
      angle_z: 0,
      eye_l_open: 1,
      eye_r_open: 1,
      eye_ball_x: 0,
      eye_ball_y: 0,
      mouth_open: 0.22,
      breath: 0.45,
    },
    react_parameters: {
      angle_x: 0,
      angle_y: 0,
      angle_z: 0,
      eye_l_open: 1,
      eye_r_open: 1,
      eye_ball_x: 0,
      eye_ball_y: 0,
      mouth_open: 0,
      breath: 0.4,
    },
  })
  await enterIdleState(currentProfile)
}

const handleEmotionCommand = async (command) => {
  if (!command) {
    return
  }

  const profile = deriveProfile(command)
  speechContext = profile

  if (profile.priority < STATE_PRIORITY[currentState.value] && currentState.value === 'react') {
    return
  }

  if ((command.state || 'react') === 'idle') {
    currentProfile = profile
    await enterIdleState(profile)
    return
  }

  if ((command.state || 'react') === 'talk') {
    currentProfile = profile
    await enterTalkState(profile)
    return
  }

  await enterReactState(profile)
}

const handleCommandEvent = (event) => {
  handleEmotionCommand(event.detail)
}

const handleTalkStartEvent = (event) => {
  handleTalkStart(event.detail)
}

const handleTalkEndEvent = () => {
  handleTalkEnd()
}

const handleLipSyncEvent = (event) => {
  applyLipSync(event.detail?.mouth_open)
}

onMounted(async () => {
  const savedPosition = localStorage.getItem('digihuman_live2d_position')
  if (savedPosition) {
    try {
      const parsed = JSON.parse(savedPosition)
      const nextPosition = clampDragPosition(
        Number(parsed.x ?? DEFAULT_POSITION.x),
        Number(parsed.y ?? DEFAULT_POSITION.y)
      )
      dragState.value = {
        ...dragState.value,
        offsetX: nextPosition.x,
        offsetY: nextPosition.y,
      }
    } catch (error) {
      console.warn('Failed to restore Live2D position:', error)
    }
  }

  await initLive2D()
  window.addEventListener('digihuman-live2d-command', handleCommandEvent)
  window.addEventListener('digihuman-live2d-talk-start', handleTalkStartEvent)
  window.addEventListener('digihuman-live2d-talk-end', handleTalkEndEvent)
  window.addEventListener('digihuman-live2d-lipsync', handleLipSyncEvent)
  window.addEventListener('pointermove', handleDragMove)
  window.addEventListener('pointerup', stopDrag)
})

onUnmounted(() => {
  window.removeEventListener('digihuman-live2d-command', handleCommandEvent)
  window.removeEventListener('digihuman-live2d-talk-start', handleTalkStartEvent)
  window.removeEventListener('digihuman-live2d-talk-end', handleTalkEndEvent)
  window.removeEventListener('digihuman-live2d-lipsync', handleLipSyncEvent)
  window.removeEventListener('pointermove', handleDragMove)
  window.removeEventListener('pointerup', stopDrag)
  destroyLive2D()
})

defineExpose({
  handleEmotionCommand,
  playMotion,
  setExpression,
  resetToNeutral,
})
</script>

<style scoped>
.live2d-wrapper {
  position: fixed;
  left: 0;
  top: 48px;
  z-index: 1000;
  transition: all 0.3s ease;
  pointer-events: none;
}

.live2d-wrapper.dragging {
  transition: none;
}

.live2d-wrapper.hidden {
  transform: translateX(-120%);
  opacity: 0;
  pointer-events: none;
}

.live2d-canvas {
  width: min(44vw, 680px);
  height: min(76vh, 980px);
  min-width: 460px;
  min-height: 620px;
  border-radius: 18px;
  overflow: hidden;
  pointer-events: none;
}

.drag-handle {
  position: absolute;
  top: 12px;
  left: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 248, 234, 0.94);
  border: 1px solid rgba(37, 23, 13, 0.12);
  box-shadow: 0 8px 18px rgba(37, 23, 13, 0.1);
  color: #25170d;
  cursor: grab;
  pointer-events: auto;
  user-select: none;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(37, 23, 13, 0.62);
}

.drag-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.live2d-controls {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  gap: 4px;
  flex-direction: column;
  pointer-events: auto;
}

.control-btn {
  background: rgba(255, 255, 255, 0.9) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  color: #333 !important;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.control-btn:hover {
  background: rgba(255, 255, 255, 1) !important;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.emotion-indicator {
  position: absolute;
  top: 54px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  animation: emotionPulse 0.5s ease;
}

@media (max-width: 960px) {
  .live2d-wrapper {
    top: 72px;
  }

  .live2d-canvas {
    width: min(64vw, 520px);
    height: min(66vh, 760px);
    min-width: 320px;
    min-height: 480px;
  }

  .drag-handle {
    top: 12px;
    left: 12px;
  }
}

.emotion-icon {
  font-size: 16px;
}

.emotion-text {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.state-badge {
  font-size: 10px;
  text-transform: uppercase;
  padding: 2px 5px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.62);
}

.emotion-indicator.state-react .state-badge {
  background: rgba(255, 255, 255, 0.45);
}

.emotion-indicator.state-talk .state-badge {
  background: rgba(255, 255, 255, 0.55);
}

.emotion-indicator.joy {
  background: linear-gradient(135deg, rgba(255, 223, 128, 0.95), rgba(255, 200, 100, 0.95));
  border-color: rgba(255, 180, 0, 0.3);
}

.emotion-indicator.sadness {
  background: linear-gradient(135deg, rgba(128, 179, 255, 0.95), rgba(100, 149, 237, 0.95));
  border-color: rgba(70, 130, 180, 0.3);
}

.emotion-indicator.anger {
  background: linear-gradient(135deg, rgba(255, 128, 128, 0.95), rgba(255, 100, 100, 0.95));
  border-color: rgba(255, 80, 80, 0.3);
}

.emotion-indicator.surprise {
  background: linear-gradient(135deg, rgba(255, 200, 128, 0.95), rgba(255, 165, 0, 0.95));
  border-color: rgba(255, 140, 0, 0.3);
}

.emotion-indicator.fear {
  background: linear-gradient(135deg, rgba(200, 162, 200, 0.95), rgba(186, 85, 211, 0.95));
  border-color: rgba(147, 112, 219, 0.3);
}

.emotion-indicator.disgust {
  background: linear-gradient(135deg, rgba(144, 238, 144, 0.95), rgba(60, 179, 113, 0.95));
  border-color: rgba(34, 139, 34, 0.3);
}

.emotion-indicator.shy {
  background: linear-gradient(135deg, rgba(255, 227, 196, 0.95), rgba(255, 182, 193, 0.95));
  border-color: rgba(255, 160, 180, 0.35);
}

.emotion-indicator.neutral {
  background: linear-gradient(135deg, rgba(220, 220, 220, 0.95), rgba(192, 192, 192, 0.95));
  border-color: rgba(169, 169, 169, 0.3);
}

@keyframes emotionPulse {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }

  50% {
    transform: scale(1.05);
  }

  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
