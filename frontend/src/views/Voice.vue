<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-white drop-shadow-lg">🎤 语音交互</h1>
      <p class="text-lg text-white/90 drop-shadow">语音输入与语音合成输出</p>
    </div>

    <div class="glass-card p-6 max-w-2xl mx-auto text-center">
      <div class="text-6xl mb-6">🎙️</div>
      <p class="text-white/80 mb-6">点击按钮开始语音输入</p>
      <el-button type="primary" size="large" @click="toggleRecording">
        {{ isRecording ? '停止录音' : '开始录音' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const isRecording = ref(false)

const toggleRecording = () => {
  isRecording.value = !isRecording.value
}
</script>
