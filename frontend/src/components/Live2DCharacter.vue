<template>
  <div class="live2d-wrapper" :class="{ 'hidden': !showCharacter }">
    <div id="live2d-canvas" class="live2d-canvas"></div>
    
    <!-- 情感状态显示 -->
    <div v-if="currentEmotion" class="emotion-indicator" :class="currentEmotion">
      <span class="emotion-icon">{{ getEmotionIcon(currentEmotion) }}</span>
      <span class="emotion-text">{{ getEmotionText(currentEmotion) }}</span>
    </div>
    
    <div class="live2d-controls">
      <el-button circle size="small" @click="toggleCharacter" class="control-btn" title="显示/隐藏">
        <el-icon>
          <View v-if="showCharacter" />
          <Hide v-else />
        </el-icon>
      </el-button>
      <el-button circle size="small" @click="playMotion('mtn_01')" class="control-btn" title="动作1">
        <el-icon>
          <VideoPlay />
        </el-icon>
      </el-button>
      <el-button circle size="small" @click="speak" class="control-btn" title="说话">
        <el-icon>
          <Microphone />
        </el-icon>
      </el-button>
      <el-button circle size="small" @click="resetToNeutral" class="control-btn" title="重置">
        <el-icon>
          <Refresh />
        </el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { View, Hide, Microphone, VideoPlay, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  webSocket: {
    type: Object,
    default: null
  }
})

const showCharacter = ref(true)
const currentEmotion = ref('neutral')
let live2dInstance = null

// 情感图标映射
const emotionIcons = {
  joy: '😊',
  sadness: '😢',
  anger: '😠',
  surprise: '😲',
  fear: '😨',
  disgust: '🤢',
  neutral: '😐'
}

// 情感文本映射
const emotionTexts = {
  joy: '开心',
  sadness: '悲伤',
  anger: '生气',
  surprise: '惊讶',
  fear: '害怕',
  disgust: '厌恶',
  neutral: '平静'
}

const getEmotionIcon = (emotion) => emotionIcons[emotion] || '😐'
const getEmotionText = (emotion) => emotionTexts[emotion] || '平静'

const toggleCharacter = () => {
  showCharacter.value = !showCharacter.value
}

const playMotion = (motionName) => {
  console.log('Playing motion:', motionName)
  if (live2dInstance && live2dInstance.playMotion) {
    live2dInstance.playMotion(motionName)
  }
}

const setExpression = (expressionName) => {
  console.log('Setting expression:', expressionName)
  if (live2dInstance && live2dInstance.setExpression) {
    live2dInstance.setExpression(expressionName)
  }
}

const speak = () => {
  console.log('Character speaking...')
  if (live2dInstance && live2dInstance.startSpeak) {
    live2dInstance.startSpeak()
    setTimeout(() => {
      if (live2dInstance && live2dInstance.endSpeak) {
        live2dInstance.endSpeak()
      }
    }, 2000)
  }
}

const resetToNeutral = () => {
  console.log('Resetting to neutral state')
  currentEmotion.value = 'neutral'
  setExpression('exp_01')
  playMotion('mtn_01')
}

// 处理情感控制指令
const handleEmotionCommand = (command) => {
  console.log('Received emotion command:', command)
  
  if (!command) return
  
  // 更新当前情感
  if (command.emotion) {
    currentEmotion.value = command.emotion
  }
  
  // 设置表情
  if (command.expression) {
    setExpression(command.expression)
  }
  
  // 播放动作
  if (command.motion) {
    playMotion(command.motion)
  }
  
  // 更新参数（如果支持）
  if (command.parameters && live2dInstance && live2dInstance.updateParameters) {
    live2dInstance.updateParameters(command.parameters)
  }
}

// WebSocket消息处理
const handleWebSocketMessage = (event) => {
  try {
    const data = JSON.parse(event.data)
    
    // 处理情感更新消息
    if (data.type === 'emotion_update') {
      console.log('Emotion update received:', data)
      
      // 如果是助手情感更新，处理Live2D指令
      if (data.source === 'assistant' && data.live2d_command) {
        handleEmotionCommand(data.live2d_command)
      }
    }
    
    // 处理聊天响应中的Live2D指令
    if ((data.type === 'chat_response' || data.type === 'full-text') && data.live2d_command) {
      console.log('Live2D command in response:', data.live2d_command)
      handleEmotionCommand(data.live2d_command)
    }
    
  } catch (error) {
    console.error('Error parsing WebSocket message:', error)
  }
}

onMounted(async () => {
  try {
    // 导入 live2d-render 库
    const live2d = await import('live2d-render')

    console.log('Loading Live2D model...')

    // 初始化 Live2D - 按照官方示例配置
    await live2d.initializeLive2D({
      // live2d 所在区域的背景颜色
      BackgroundRGBA: [0.0, 0.0, 0.0, 0.0],

      // live2d 的 model3.json 文件的相对路径
      ResourcesPath: '/live2d_models/Mao/Mao.model3.json',

      // live2d 的大小
      CanvasSize: {
        height: 500,
        width: 400
      },

      // live2d 的位置 ('left' | 'right')
      CanvasPosition: 'left',

      // 展示工具箱（可以控制 live2d 的展出隐藏，使用特定表情）
      ShowToolBox: true,

      // 是否使用 indexDB 进行缓存优化，这样下一次载入就不会再发起网络请求了
      LoadFromCache: true
    })

    live2dInstance = live2d
    console.log('Live2D loaded successfully')
    
    // 注册WebSocket消息监听
    if (props.webSocket) {
      props.webSocket.addEventListener('message', handleWebSocketMessage)
    }
    
  } catch (error) {
    console.error('Live2D initialization failed:', error)
  }
})

onUnmounted(() => {
  // 移除WebSocket消息监听
  if (props.webSocket) {
    props.webSocket.removeEventListener('message', handleWebSocketMessage)
  }
  
  if (live2dInstance && live2dInstance.dispose) {
    live2dInstance.dispose()
  }
})

// 暴露方法供父组件调用
defineExpose({
  handleEmotionCommand,
  playMotion,
  setExpression,
  resetToNeutral
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

/* 情感指示器 */
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

/* 不同情感的颜色主题 */
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
