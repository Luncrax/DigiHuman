<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8 py-5">
      <h1 class="text-4xl font-bold mb-3 text-gray-900">🎭 DigiHuman</h1>
      <p class="text-lg text-gray-600">虚拟数字人助手平台</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <router-link to="/chat" class="glass-card p-6 hover:scale-105 transition-transform cursor-pointer group">
        <div class="text-center">
          <div class="text-4xl mb-3 group-hover:scale-110 transition-transform">💬</div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">智能对话</h3>
          <p class="text-gray-500">与虚拟助手进行自然语言交流</p>
        </div>
      </router-link>

      <router-link to="/voice" class="glass-card p-6 hover:scale-105 transition-transform cursor-pointer group">
        <div class="text-center">
          <div class="text-4xl mb-3 group-hover:scale-110 transition-transform">🎤</div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">语音交互</h3>
          <p class="text-gray-500">语音输入与语音合成输出</p>
        </div>
      </router-link>

      <router-link to="/live2d-view" class="glass-card p-6 hover:scale-105 transition-transform cursor-pointer group">
        <div class="text-center">
          <div class="text-4xl mb-3 group-hover:scale-110 transition-transform">🎭</div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">Live2D 角色</h3>
          <p class="text-gray-500">动态角色表情与动作展示</p>
        </div>
      </router-link>

      <router-link to="/character" class="glass-card p-6 hover:scale-105 transition-transform cursor-pointer group">
        <div class="text-center">
          <div class="text-4xl mb-3 group-hover:scale-110 transition-transform">👤</div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">角色管理</h3>
          <p class="text-gray-500">自定义角色外观与行为</p>
        </div>
      </router-link>

      <router-link to="/dashboard" class="glass-card p-6 hover:scale-105 transition-transform cursor-pointer group">
        <div class="text-center">
          <div class="text-4xl mb-3 group-hover:scale-110 transition-transform">📊</div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">系统监控</h3>
          <p class="text-gray-500">实时监控系统状态与性能</p>
        </div>
      </router-link>

      <router-link to="/settings" class="glass-card p-6 hover:scale-105 transition-transform cursor-pointer group">
        <div class="text-center">
          <div class="text-4xl mb-3 group-hover:scale-110 transition-transform">⚙️</div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">系统设置</h3>
          <p class="text-gray-500">配置 ASR、TTS 和 Live2D 参数</p>
        </div>
      </router-link>
    </div>

    <div class="glass-card p-6">
      <h2 class="text-2xl font-semibold mb-4 text-gray-900">🚀 快速开始</h2>
      <div class="space-y-3 text-gray-600">
        <p>1. 点击上方功能卡片进入对应模块</p>
        <p>2. 在设置中配置您的偏好参数</p>
        <p>3. 开始与虚拟助手进行交互</p>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>
