<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-white drop-shadow-lg">🧠 记忆系统</h1>
      <p class="text-lg text-white/90 drop-shadow">上下文感知记忆管理</p>
    </div>

    <div class="glass-card p-6 max-w-4xl mx-auto">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center border border-white/20">
          <div class="text-2xl font-bold text-white mb-1">0</div>
          <div class="text-sm text-white/70">总记忆数</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center border border-white/20">
          <div class="text-2xl font-bold text-white mb-1">0</div>
          <div class="text-sm text-white/70">活跃会话</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center border border-white/20">
          <div class="text-2xl font-bold text-white mb-1">0%</div>
          <div class="text-sm text-white/70">内存使用</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center border border-white/20">
          <div class="text-2xl font-bold text-white mb-1">0%</div>
          <div class="text-sm text-white/70">回忆率</div>
        </div>
      </div>

      <el-button type="primary" @click="refreshStats">刷新统计</el-button>
    </div>
  </div>
</template>

<script setup>
const refreshStats = () => {
  console.log('Refreshing stats...')
}
</script>
