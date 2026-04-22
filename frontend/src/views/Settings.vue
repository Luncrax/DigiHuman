<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-white drop-shadow-lg">⚙️ 系统设置</h1>
      <p class="text-lg text-white/90 drop-shadow">配置 ASR、TTS 和 Live2D 参数</p>
    </div>

    <div class="glass-card p-6 max-w-4xl mx-auto">
      <el-tabs type="border-card">
        <el-tab-pane label="ASR 设置">
          <el-form label-position="top">
            <el-form-item label="ASR 模型">
              <el-select v-model="settings.asrModel" class="w-full">
                <el-option label="Whisper Tiny" value="whisper-tiny" />
                <el-option label="Whisper Base" value="whisper-base" />
                <el-option label="Whisper Medium" value="whisper-medium" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="TTS 设置">
          <el-form label-position="top">
            <el-form-item label="TTS 模型">
              <el-select v-model="settings.ttsModel" class="w-full">
                <el-option label="TTS-1" value="tts-1" />
                <el-option label="TTS-1 HD" value="tts-1-hd" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="mt-6">
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const settings = reactive({
  asrModel: 'whisper-medium',
  ttsModel: 'tts-1'
})

const saveSettings = () => {
  console.log('Saving settings:', settings)
}
</script>
