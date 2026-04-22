<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-gray-900 dark:text-white">🎭 Live2D 角色</h1>
      <p class="text-lg text-gray-600 dark:text-gray-400">Mao - 动态角色展示</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Live2D 画布区域 -->
      <div class="lg:col-span-2">
        <div class="glass-card p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">角色展示</h2>
            <div class="flex gap-2">
              <el-tag v-if="modelLoaded" type="success">已加载</el-tag>
              <el-tag v-else-if="loading" type="warning">加载中...</el-tag>
              <el-tag v-else type="danger">未加载</el-tag>
            </div>
          </div>
          
          <!-- Live2D 画布容器 -->
          <div 
            id="live2d-canvas-container" 
            class="w-full h-[500px] bg-gradient-to-b from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-2xl flex items-center justify-center overflow-hidden relative"
          >
            <div v-if="!modelLoaded && !loading" class="text-center text-gray-500">
              <div class="text-6xl mb-4">🎭</div>
              <p>点击"加载模型"按钮显示 Live2D 角色</p>
            </div>
            <div v-if="loading" class="text-center text-gray-500">
              <el-icon class="text-4xl animate-spin"><Loading /></el-icon>
              <p class="mt-4">正在加载模型...</p>
            </div>
            <!-- Live2D 画布将在这里渲染 -->
          </div>

          <!-- 控制按钮 -->
          <div class="flex gap-3 mt-4">
            <el-button type="primary" @click="loadModel" :loading="loading" :disabled="modelLoaded">
              <el-icon class="mr-1"><Download /></el-icon>
              {{ modelLoaded ? '已加载' : '加载模型' }}
            </el-button>
            <el-button @click="unloadModel" :disabled="!modelLoaded">
              <el-icon class="mr-1"><Close /></el-icon>
              卸载
            </el-button>
          </div>
        </div>
      </div>

      <!-- 控制面板 -->
      <div class="space-y-6">
        <!-- 动作控制 -->
        <div class="glass-card p-6">
          <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-white">动作控制</h3>
          <div class="grid grid-cols-2 gap-3">
            <el-button 
              v-for="motion in motions" 
              :key="motion.name"
              @click="playMotion(motion.file)" 
              :disabled="!modelLoaded"
              class="w-full"
            >
              {{ motion.label }}
            </el-button>
          </div>
        </div>

        <!-- 表情控制 -->
        <div class="glass-card p-6">
          <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-white">表情控制</h3>
          <div class="grid grid-cols-2 gap-3">
            <el-button 
              v-for="expr in expressions" 
              :key="expr"
              @click="setExpression(expr)" 
              :disabled="!modelLoaded"
              class="w-full"
            >
              {{ expr }}
            </el-button>
          </div>
        </div>

        <!-- 模型信息 -->
        <div class="glass-card p-6">
          <h3 class="text-lg font-semibold mb-4 text-gray-900 dark:text-white">模型信息</h3>
          <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <p><span class="font-medium">名称:</span> Mao</p>
            <p><span class="font-medium">路径:</span> /live2d_models/Mao/</p>
            <p><span class="font-medium">格式:</span> Live2D Cubism 3</p>
            <p><span class="font-medium">动作数:</span> {{ motions.length }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Loading, Download, Close } from '@element-plus/icons-vue'

const modelLoaded = ref(false)
const loading = ref(false)
let live2dInstance = null

// 动作列表 (Mao 模型)
const motions = [
  { name: 'mtn_01', label: '动作1', file: 'mtn_01.motion3.json' },
  { name: 'mtn_02', label: '动作2', file: 'mtn_02.motion3.json' },
  { name: 'mtn_03', label: '动作3', file: 'mtn_03.motion3.json' },
  { name: 'mtn_04', label: '动作4', file: 'mtn_04.motion3.json' },
  { name: 'sample', label: '示例', file: 'sample_01.motion3.json' },
  { name: 'special1', label: '特殊1', file: 'special_01.motion3.json' },
  { name: 'special2', label: '特殊2', file: 'special_02.motion3.json' },
  { name: 'special3', label: '特殊3', file: 'special_03.motion3.json' },
]

// 表情列表
const expressions = ['开心', '伤心', '惊讶', '生气', '默认']

// 加载模型
const loadModel = async () => {
  if (modelLoaded.value) return
  
  loading.value = true
  console.log('开始加载 Live2D 模型...')
  
  try {
    const live2d = await import('live2d-render')
    
    await live2d.initializeLive2D({
      BackgroundRGBA: [0.0, 0.0, 0.0, 0.0],
      ResourcesPath: '/live2d_models/Mao/Mao.model3.json',
      CanvasSize: {
        height: 500,
        width: 700
      },
      CanvasPosition: 'center',
      ShowToolBox: false,
      LoadFromCache: true
    })
    
    live2dInstance = live2d
    modelLoaded.value = true
    console.log('Live2D 模型加载成功')
  } catch (error) {
    console.error('Live2D 模型加载失败:', error)
    alert('模型加载失败，请检查控制台错误信息')
  } finally {
    loading.value = false
  }
}

// 卸载模型
const unloadModel = () => {
  if (live2dInstance && live2dInstance.dispose) {
    live2dInstance.dispose()
  }
  live2dInstance = null
  modelLoaded.value = false
  console.log('Live2D 模型已卸载')
}

// 播放动作
const playMotion = (motionFile) => {
  console.log('播放动作:', motionFile)
  if (live2dInstance && live2dInstance.playMotion) {
    live2dInstance.playMotion(motionFile)
  }
}

// 设置表情
const setExpression = (expression) => {
  console.log('设置表情:', expression)
  if (live2dInstance && live2dInstance.setExpression) {
    live2dInstance.setExpression(expression)
  }
}

onUnmounted(() => {
  unloadModel()
})
</script>

<style scoped>
#live2d-canvas-container {
  position: relative;
}

:deep(canvas) {
  max-width: 100% !important;
  max-height: 100% !important;
}
</style>
