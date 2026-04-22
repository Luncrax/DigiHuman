<template>
  <div class="fixed bottom-0 left-0 right-0 bg-white/70 backdrop-blur-xl py-3 px-5 flex justify-between items-center z-50 border-t border-gray-200/50 rounded-t-xl mx-5 shadow-sm mb-4">
    <div class="flex items-center gap-2 font-medium text-gray-700">
      <div class="status-dot" :class="{ connected: isConnected }"></div>
      <span>{{ statusText }}</span>
    </div>
    <div class="flex gap-3">
      <el-button v-if="!isConnected" size="small" type="primary" @click="connect">
        连接
      </el-button>
      <el-button v-else size="small" type="danger" @click="disconnect">
        断开
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isConnected = ref(false)
const statusText = ref('等待连接...')
let ws = null

const connect = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws`
  
  try {
    ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      isConnected.value = true
      statusText.value = '已连接'
    }
    
    ws.onclose = () => {
      isConnected.value = false
      statusText.value = '已断开'
    }
    
    ws.onerror = () => {
      isConnected.value = false
      statusText.value = '连接错误'
    }
  } catch (error) {
    statusText.value = '连接失败'
  }
}

const disconnect = () => {
  if (ws) {
    ws.close()
  }
}

onMounted(() => {
  setTimeout(connect, 1000)
})
</script>

<style scoped>
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #ff3b30;
  transition: background-color 0.3s ease;
}

.status-dot.connected {
  background-color: #34c759;
}
</style>
