<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-white drop-shadow-lg">📊 系统监控</h1>
      <p class="text-lg text-white/90 drop-shadow">实时监控系统状态与性能</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="glass-card p-6 text-center">
        <div class="text-3xl font-bold text-white mb-2">0</div>
        <div class="text-white/70">活跃用户</div>
      </div>
      <div class="glass-card p-6 text-center">
        <div class="text-3xl font-bold text-white mb-2">0</div>
        <div class="text-white/70">总请求数</div>
      </div>
      <div class="glass-card p-6 text-center">
        <div class="text-3xl font-bold text-white mb-2">0ms</div>
        <div class="text-white/70">响应时间</div>
      </div>
      <div class="glass-card p-6 text-center">
        <div class="text-3xl font-bold text-white mb-2">0%</div>
        <div class="text-white/70">成功率</div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>
