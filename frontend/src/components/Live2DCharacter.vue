<template>
  <div class="live2d-wrapper" :class="{ 'hidden': !showCharacter }">
    <div id="live2d-canvas" class="live2d-canvas"></div>
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { View, Hide, Microphone, VideoPlay } from '@element-plus/icons-vue'

const showCharacter = ref(true)
let live2dInstance = null

const toggleCharacter = () => {
  showCharacter.value = !showCharacter.value
}

const playMotion = (motionName) => {
  console.log('Playing motion:', motionName)
  if (live2dInstance && live2dInstance.playMotion) {
    live2dInstance.playMotion(motionName)
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
    console.log('finish loading')
  } catch (error) {
    console.error('Live2D initialization failed:', error)
  }
})

onUnmounted(() => {
  if (live2dInstance && live2dInstance.dispose) {
    live2dInstance.dispose()
  }
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
</style>
