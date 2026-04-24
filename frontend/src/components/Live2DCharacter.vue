<template>
  <div class="live2d-wrapper" :class="{ hidden: !showCharacter }">
    <div ref="canvasRef" class="live2d-canvas"></div>

    <div v-if="currentEmotion" class="emotion-indicator" :class="currentEmotion">
      <span class="emotion-icon">{{ getEmotionIcon(currentEmotion) }}</span>
      <span class="emotion-text">{{ getEmotionText(currentEmotion) }}</span>
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
      <el-button circle size="small" class="control-btn" title="说话演示" @click="speak">
        <el-icon><Microphone /></el-icon>
      </el-button>
      <el-button circle size="small" class="control-btn" title="重置" @click="resetToNeutral">
        <el-icon><Refresh /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { View, Hide, Microphone, VideoPlay, Refresh } from '@element-plus/icons-vue'
import { createPixiLive2d } from '@/lib/live2d/pixiLive2d'

const showCharacter = ref(true)
const currentEmotion = ref('neutral')
const canvasRef = ref(null)

let live2dRuntime = null

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

const initLive2D = async () => {
  if (!canvasRef.value || live2dRuntime) {
    return
  }

  try {
    live2dRuntime = await createPixiLive2d(canvasRef.value, {
      modelPath: '/live2d_models/Mao/Mao.model3.json',
      scaleMultiplier: 0.2,
    })

    window.live2dApp = {
      handleCommand: handleEmotionCommand,
      playMotion,
      setExpression,
      resetToNeutral,
    }
  } catch (error) {
    console.error('Pixi Live2D initialization failed:', error)
  }
}

const destroyLive2D = () => {
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

const speak = () => {
  if (!live2dRuntime) {
    return
  }

  live2dRuntime.updateParameters({ mouth_open: 0.8 })
  window.setTimeout(() => {
    live2dRuntime?.updateParameters({ mouth_open: 0.0 })
  }, 1200)
}

const resetToNeutral = async () => {
  currentEmotion.value = 'neutral'
  await setExpression('exp_01')
  await playMotion('idle')
  live2dRuntime?.updateParameters({
    angle_x: 0,
    angle_y: 0,
    angle_z: 0,
    mouth_open: 0,
    breath: 0.4,
  })
}

const handleEmotionCommand = async (command) => {
  if (!command) {
    return
  }

  if (command.emotion) {
    currentEmotion.value = normalizeEmotion(command.emotion)
  }

  if (command.expression) {
    await setExpression(command.expression)
  }

  if (command.motion) {
    await playMotion(command.motion)
  }

  if (command.parameters) {
    live2dRuntime?.updateParameters(command.parameters)
  }
}

const handleCommandEvent = (event) => {
  handleEmotionCommand(event.detail)
}

onMounted(async () => {
  await initLive2D()
  window.addEventListener('digihuman-live2d-command', handleCommandEvent)
})

onUnmounted(() => {
  window.removeEventListener('digihuman-live2d-command', handleCommandEvent)
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
  bottom: 80px;
  left: 20px;
  z-index: 1000;
  transition: all 0.3s ease;
}

.live2d-wrapper.hidden {
  transform: translateX(-120%);
  opacity: 0;
  pointer-events: none;
}

.live2d-canvas {
  width: 400px;
  height: 500px;
  border-radius: 16px;
  overflow: hidden;
}

.live2d-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 6px;
  flex-direction: column;
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
  top: 10px;
  left: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  animation: emotionPulse 0.5s ease;
}

.emotion-icon {
  font-size: 20px;
}

.emotion-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
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
