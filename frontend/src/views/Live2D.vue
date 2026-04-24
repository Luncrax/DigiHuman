<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-gray-900 dark:text-white">Live2D 角色</h1>
      <p class="text-lg text-gray-600 dark:text-gray-400">Pixi + pixi-live2d-display 驱动的 Mao 模型预览</p>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <div class="glass-card p-6">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">角色展示</h2>
            <div class="flex gap-2">
              <el-tag v-if="modelLoaded" type="success">已加载</el-tag>
              <el-tag v-else-if="loading" type="warning">加载中</el-tag>
              <el-tag v-else type="danger">未加载</el-tag>
            </div>
          </div>

          <div
            ref="canvasRef"
            class="relative flex h-[500px] w-full items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-b from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900"
          >
            <div v-if="!modelLoaded && !loading" class="text-center text-gray-500">
              <div class="mb-4 text-6xl">🎭</div>
              <p>点击“加载模型”开始预览 Pixi Live2D</p>
            </div>
            <div v-if="loading" class="text-center text-gray-500">
              <el-icon class="text-4xl animate-spin"><Loading /></el-icon>
              <p class="mt-4">正在加载模型...</p>
            </div>
          </div>

          <div class="mt-4 flex gap-3">
            <el-button type="primary" :loading="loading" :disabled="modelLoaded" @click="loadModel">
              <el-icon class="mr-1"><Download /></el-icon>
              {{ modelLoaded ? '已加载' : '加载模型' }}
            </el-button>
            <el-button :disabled="!modelLoaded" @click="unloadModel">
              <el-icon class="mr-1"><Close /></el-icon>
              卸载
            </el-button>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="glass-card p-6">
          <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">动作控制</h3>
          <div class="grid grid-cols-2 gap-3">
            <el-button
              v-for="motion in motions"
              :key="motion.name"
              :disabled="!modelLoaded"
              class="w-full"
              @click="playMotion(motion.name)"
            >
              {{ motion.label }}
            </el-button>
          </div>
        </div>

        <div class="glass-card p-6">
          <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">表情控制</h3>
          <div class="grid grid-cols-2 gap-3">
            <el-button
              v-for="expression in expressions"
              :key="expression.name"
              :disabled="!modelLoaded"
              class="w-full"
              @click="setExpression(expression.name)"
            >
              {{ expression.label }}
            </el-button>
          </div>
        </div>

        <div class="glass-card p-6">
          <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">模型信息</h3>
          <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
            <p><span class="font-medium">名称:</span> Mao</p>
            <p><span class="font-medium">路径:</span> /live2d_models/Mao/Mao.model3.json</p>
            <p><span class="font-medium">渲染:</span> PixiJS 6 + pixi-live2d-display</p>
            <p><span class="font-medium">动作数:</span> {{ motions.length }}</p>
            <p><span class="font-medium">表情数:</span> {{ expressions.length }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import { Loading, Download, Close } from '@element-plus/icons-vue'
import { createPixiLive2d } from '@/lib/live2d/pixiLive2d'

const canvasRef = ref(null)
const modelLoaded = ref(false)
const loading = ref(false)

let live2dRuntime = null

const motions = [
  { name: 'mtn_01', label: '待机1' },
  { name: 'sample_01', label: '待机2' },
  { name: 'mtn_02', label: '动作1' },
  { name: 'mtn_03', label: '动作2' },
  { name: 'mtn_04', label: '动作3' },
  { name: 'special_01', label: '特效1' },
  { name: 'special_02', label: '特效2' },
  { name: 'special_03', label: '特效3' },
]

const expressions = [
  { name: 'exp_01', label: '默认' },
  { name: 'exp_02', label: '开心' },
  { name: 'exp_03', label: '难过' },
  { name: 'exp_04', label: '委屈' },
  { name: 'exp_05', label: '认真' },
  { name: 'exp_06', label: '生气' },
  { name: 'exp_07', label: '惊讶' },
  { name: 'exp_08', label: '震惊' },
]

const loadModel = async () => {
  if (modelLoaded.value || !canvasRef.value) {
    return
  }

  loading.value = true

  try {
    live2dRuntime = await createPixiLive2d(canvasRef.value, {
      modelPath: '/live2d_models/Mao/Mao.model3.json',
      scaleMultiplier: 0.24,
    })

    modelLoaded.value = true
  } catch (error) {
    console.error('Failed to load Pixi Live2D model:', error)
    alert('模型加载失败，请检查控制台和 Cubism Core 脚本加载状态。')
  } finally {
    loading.value = false
  }
}

const unloadModel = () => {
  live2dRuntime?.destroy()
  live2dRuntime = null
  modelLoaded.value = false
}

const playMotion = async (motionName) => {
  if (!live2dRuntime) {
    return
  }

  try {
    await live2dRuntime.playMotion(motionName)
  } catch (error) {
    console.error('Failed to play motion:', error)
  }
}

const setExpression = async (expressionName) => {
  if (!live2dRuntime) {
    return
  }

  try {
    await live2dRuntime.setExpression(expressionName)
  } catch (error) {
    console.error('Failed to set expression:', error)
  }
}

onUnmounted(() => {
  unloadModel()
})
</script>

<style scoped>
:deep(canvas) {
  display: block;
  width: 100% !important;
  height: 100% !important;
}
</style>
