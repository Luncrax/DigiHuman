<template>
  <div class="container mx-auto px-4 py-5 pt-20">
    <div class="text-center mb-8">
      <h1 class="text-4xl font-bold mb-3 text-black drop-shadow-lg">💬 智能对话</h1>
      <p class="text-lg text-black/90 drop-shadow">与虚拟助手进行自然语言交流</p>
      <p v-if="!connected" class="text-sm text-red-400">正在连接服务器...</p>
      <p v-else class="text-sm text-green-400">已连接到服务器</p>
    </div>

    <div class="max-w-6xl mx-auto flex gap-6">
      <!-- History Sidebar -->
      <div class="w-72 flex-shrink-0">
        <div class="glass-card p-4 mb-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-black font-semibold">对话历史</h3>
            <el-button 
              type="primary" 
              size="small" 
              @click="createNewHistory"
              :disabled="!connected"
            >
              + 新建
            </el-button>
          </div>
          
          <!-- 搜索框 -->
          <el-input
            v-model="searchKeyword"
            placeholder="搜索历史记录..."
            prefix-icon="Search"
            size="small"
            class="mb-3"
            clearable
            @input="filterHistories"
          />
          
          <!-- 筛选选项 -->
          <div class="mb-3">
            <el-select
              v-model="filterType"
              placeholder="筛选方式"
              size="small"
              class="w-full"
              @change="filterHistories"
            >
              <el-option label="全部" value="all" />
              <el-option label="今天" value="today" />
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
            </el-select>
          </div>
          
          <!-- 历史记录列表 -->
          <div class="space-y-2 max-h-96 overflow-y-auto">
            <div
              v-for="history in filteredHistories"
              :key="history.uid"
              class="history-item-container"
            >
              <div
                @click="switchHistory(history.uid)"
                :class="['history-item p-3 rounded cursor-pointer transition-colors', 
                  currentHistoryUid === history.uid ? 'bg-blue-500/50' : 'hover:bg-white/10']"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <div class="text-black text-sm font-medium truncate">
                      {{ getHistoryTitle(history) }}
                    </div>
                    <div class="text-black/70 text-xs mt-1 truncate">
                      {{ getHistoryPreview(history) }}
                    </div>
                    <div class="text-black/50 text-xs mt-2">
                      {{ formatTime(history.timestamp) }}
                    </div>
                  </div>
                  <el-dropdown @command="(cmd) => handleHistoryAction(cmd, history.uid)" trigger="click">
                    <el-button
                      type="text"
                      :icon="MoreFilled"
                      size="small"
                      class="text-black/60 hover:text-black"
                    />
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="preview">
                          <el-icon><View /></el-icon>
                          预览
                        </el-dropdown-item>
                        <el-dropdown-item command="rename">
                          <el-icon><Edit /></el-icon>
                          重命名
                        </el-dropdown-item>
                        <el-dropdown-item command="delete" divided>
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </div>
            <div v-if="filteredHistories.length === 0" class="text-black/50 text-sm text-center py-8">
              {{ historyList.length === 0 ? '暂无历史记录' : '未找到匹配的历史记录' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Area -->
      <div class="flex-1 glass-card p-6">
        <div class="h-96 overflow-y-auto mb-4 space-y-4" id="chatContainer">
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            :class="['message', msg.role === 'assistant' ? 'assistant-message' : 'user-message']"
          >
            <p>{{ msg.content }}</p>
          </div>
        </div>

        <div class="flex gap-3">
          <el-input
            v-model="inputMessage"
            placeholder="输入消息..."
            @keyup.enter="sendMessage"
            class="flex-1"
            :disabled="!connected"
          />
          <el-button 
            type="primary" 
            @click="sendMessage" 
            :disabled="!connected"
          >
            发送
          </el-button>
          <el-button 
            :type="isRecording ? 'danger' : 'default'" 
            @click="toggleVoiceRecording"
            :disabled="!connected"
            :icon="Microphone"
            circle
            :title="isRecording ? '停止录音' : '开始语音输入'"
          />
        </div>
        
        <!-- 录音状态显示 -->
        <div v-if="isRecording" class="mt-3 flex items-center gap-2">
          <div class="recording-indicator flex items-center gap-2 px-3 py-1 bg-red-50 rounded-full">
            <span class="recording-dot w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            <span class="text-sm text-red-600">正在录音...</span>
          </div>
          <div class="audio-level flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              class="h-full bg-red-500 transition-all duration-100"
              :style="{ width: audioLevel + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 历史记录预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="历史记录预览"
      width="600px"
    >
      <div v-if="previewHistory" class="max-h-96 overflow-y-auto">
        <div
          v-for="(msg, index) in previewHistory.messages"
          :key="index"
          :class="['preview-message p-3 mb-2 rounded', 
            msg.role === 'human' ? 'bg-blue-50' : 'bg-gray-50']"
        >
          <div class="text-xs text-gray-500 mb-1">
            {{ msg.role === 'human' ? '用户' : '助手' }}
          </div>
          <div class="text-sm text-gray-800">
            {{ msg.content }}
          </div>
        </div>
      </div>
      <div v-else class="text-center py-8 text-gray-500">
        暂无消息记录
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="loadPreviewHistory">加载此对话</el-button>
      </template>
    </el-dialog>
    
    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialogVisible"
      title="重命名对话"
      width="400px"
    >
      <el-input
        v-model="newHistoryName"
        placeholder="输入新的对话名称"
        maxlength="50"
        show-word-limit
      />
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename" :disabled="!newHistoryName.trim()">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, MoreFilled, View, Edit, Delete, Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAudioRecorder } from '@/composables/useAudioRecorder'
import { useAudioPlayer } from '@/composables/useAudioPlayer'

const inputMessage = ref('')
const messages = ref([
  { role: 'assistant', content: '你好！我是你的虚拟助手。有什么我可以帮助你的吗？' }
])
const connected = ref(false)
const historyList = ref([])
const currentHistoryUid = ref(null)
const searchKeyword = ref('')
const filterType = ref('all')
const previewDialogVisible = ref(false)
const renameDialogVisible = ref(false)
const previewHistory = ref(null)
const newHistoryName = ref('')
const selectedHistoryUid = ref(null)

// 语音相关状态
const isRecording = ref(false)
const isPlayingAudio = ref(false)
let ws = null
let clientId = localStorage.getItem('digiHuman_clientId') || null

// 语音录制和播放
const { 
  isRecording: recorderIsRecording, 
  audioLevel, 
  hasPermission: recorderHasPermission,
  errorMessage: recorderError,
  requestPermission,
  startRecording,
  stopRecording,
  cancelRecording
} = useAudioRecorder()

const {
  isPlaying: playerIsPlaying,
  isLoading: playerIsLoading,
  playBase64Audio,
  stopPlayback
} = useAudioPlayer()

// 从localStorage恢复会话数据
const restoreSession = () => {
  const savedMessages = localStorage.getItem('digiHuman_messages')
  const savedHistoryUid = localStorage.getItem('digiHuman_currentHistoryUid')
  
  if (savedMessages) {
    try {
      const parsed = JSON.parse(savedMessages)
      if (Array.isArray(parsed) && parsed.length > 0) {
        messages.value = parsed
      }
    } catch (e) {
      console.error('Failed to restore messages:', e)
    }
  }
  
  if (savedHistoryUid) {
    currentHistoryUid.value = savedHistoryUid
  }
}

// 保存会话数据到localStorage
const saveSession = () => {
  localStorage.setItem('digiHuman_messages', JSON.stringify(messages.value))
  if (currentHistoryUid.value) {
    localStorage.setItem('digiHuman_currentHistoryUid', currentHistoryUid.value)
  }
}

// 保存clientId到localStorage
const saveClientId = (id) => {
  clientId = id
  localStorage.setItem('digiHuman_clientId', id)
}

// 定期保存会话数据
let saveInterval = null
const startAutoSave = () => {
  saveInterval = setInterval(() => {
    if (messages.value.length > 0) {
      saveSession()
    }
  }, 5000) // 每5秒自动保存一次
}

const stopAutoSave = () => {
  if (saveInterval) {
    clearInterval(saveInterval)
    saveInterval = null
  }
}

// 同步本地消息到后端
const syncLocalMessagesToBackend = () => {
  if (!ws || !connected.value || !currentHistoryUid.value) return
  
  const localMessages = messages.value
  if (localMessages.length === 0) return
  
  // 过滤掉系统欢迎消息
  const messagesToSync = localMessages.filter(msg => 
    msg.role !== 'assistant' || 
    !msg.content.includes('你好！我是你的虚拟助手。有什么我可以帮助你的吗？')
  )
  
  if (messagesToSync.length === 0) return
  
  console.log('Syncing local messages to backend:', messagesToSync.length, 'messages')
  
  // 发送同步请求到后端
  ws.send(JSON.stringify({
    type: 'sync-local-messages',
    history_uid: currentHistoryUid.value,
    messages: messagesToSync.map(msg => ({
      role: msg.role === 'user' ? 'human' : 'ai',
      content: msg.content,
      timestamp: new Date().toISOString()
    }))
  }))
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 获取历史记录标题
const getHistoryTitle = (history) => {
  if (!history) return '新对话'
  if (history.is_new) return '新对话'
  const content = history.latest_message?.content || ''
  return content.length > 20 ? content.substring(0, 20) + '...' : content || '新对话'
}

// 获取历史记录预览
const getHistoryPreview = (history) => {
  if (!history || !history.latest_message) return '暂无消息'
  if (history.is_new) return '暂无消息'
  return history.latest_message.content
}

// 筛选历史记录
const filteredHistories = computed(() => {
  let filtered = [...historyList.value]
  
  // 关键词搜索
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(history => {
      const content = history.latest_message?.content || ''
      return content.toLowerCase().includes(keyword)
    })
  }
  
  // 时间筛选
  const now = new Date()
  if (filterType.value === 'today') {
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    filtered = filtered.filter(history => {
      const historyDate = new Date(history.timestamp)
      return historyDate >= today
    })
  } else if (filterType.value === 'week') {
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    filtered = filtered.filter(history => {
      const historyDate = new Date(history.timestamp)
      return historyDate >= weekAgo
    })
  } else if (filterType.value === 'month') {
    const monthAgo = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate())
    filtered = filtered.filter(history => {
      const historyDate = new Date(history.timestamp)
      return historyDate >= monthAgo
    })
  }
  
  return filtered
})

// 连接WebSocket
const connectWebSocket = () => {
  try {
    // 连接到后端WebSocket服务
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // 使用固定的后端端口8001
    const wsHost = window.location.hostname + ':8001'
    ws = new WebSocket(`${wsProtocol}//${wsHost}/ws`)
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      connected.value = true
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleWebSocketMessage(data)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      connected.value = false
      setTimeout(connectWebSocket, 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      connected.value = false
    }
  } catch (error) {
    console.error('Failed to connect WebSocket:', error)
    connected.value = false
    setTimeout(connectWebSocket, 3000)
  }
}

// 处理WebSocket消息
const handleWebSocketMessage = (data) => {
  switch (data.type) {
    case 'connection_established':
      saveClientId(data.client_id)
      console.log('Connection established with client ID:', clientId)
      fetchHistoryList()
      // 检查是否有本地恢复的消息需要同步到后端
      if (currentHistoryUid.value && messages.value.length > 0) {
        // 延迟一下确保历史列表已加载
        setTimeout(() => {
          syncLocalMessagesToBackend()
        }, 500)
      }
      break
      
    case 'chat_response':
    case 'full-text':
      const content = data.message || data.text
      if (content) {
        // 检查是否有语音识别的文本
        if (data.user_text) {
          // 添加用户的语音输入
          messages.value.push({ role: 'user', content: data.user_text })
        }
        // 添加助手的响应
        messages.value.push({ role: 'assistant', content })
        saveSession() // 保存会话
        scrollToBottom()
        
        // 如果有音频数据，播放TTS音频
        if (data.audio) {
          isPlayingAudio.value = true
          playBase64Audio(data.audio, 'audio/mpeg').catch(err => {
            console.error('TTS playback error:', err)
          }).finally(() => {
            isPlayingAudio.value = false
          })
        }
      }
      break
      
    case 'error':
      const errorMessage = '错误: ' + data.message
      messages.value.push({ role: 'assistant', content: errorMessage })
      ElMessage.error(data.message || '处理失败，请重试')
      scrollToBottom()
      break
      
    case 'history-list':
      historyList.value = data.histories || []
      break
      
    case 'history-data':
      const historyMessages = data.messages || []
      messages.value = historyMessages.map(msg => ({
        role: msg.role === 'human' ? 'user' : 'assistant',
        content: msg.content
      }))
      if (messages.value.length === 0) {
        messages.value.push({
          role: 'assistant',
          content: '你好！我是你的虚拟助手。有什么我可以帮助你的吗？'
        })
      }
      scrollToBottom()
      break
      
    case 'new-history-created':
      currentHistoryUid.value = data.history_uid
      messages.value = [{
        role: 'assistant',
        content: '你好！我是你的虚拟助手。有什么我可以帮助你的吗？'
      }]
      fetchHistoryList()
      break
      
    case 'local-messages-synced':
      console.log('Local messages synced successfully:', data.message_count, 'messages')
      // 同步成功后重新获取历史列表，确保历史记录显示最新状态
      fetchHistoryList()
      break
      
    case 'history-deleted':
      fetchHistoryList()
      break
  }
}

// 获取历史列表
const fetchHistoryList = () => {
  if (!ws || !connected.value) return
  ws.send(JSON.stringify({
    type: 'fetch-history-list'
  }))
}

// 创建新历史
const createNewHistory = () => {
  if (!ws || !connected.value) return
  saveSession() // 创建新历史前保存当前会话
  ws.send(JSON.stringify({
    type: 'create-new-history'
  }))
}

// 切换历史
const switchHistory = (historyUid) => {
  if (!ws || !connected.value || historyUid === currentHistoryUid.value) return
  saveSession() // 切换前保存当前会话
  currentHistoryUid.value = historyUid
  localStorage.removeItem('digiHuman_messages') // 清除本地保存的当前对话
  localStorage.setItem('digiHuman_currentHistoryUid', historyUid) // 更新当前历史ID
  ws.send(JSON.stringify({
    type: 'fetch-and-set-history',
    history_uid: historyUid
  }))
}

// 筛选历史记录
const filterHistories = () => {
  // 使用 computed 属性自动更新
}

// 处理历史记录操作
const handleHistoryAction = (command, historyUid) => {
  selectedHistoryUid.value = historyUid
  
  switch (command) {
    case 'preview':
      previewHistory.value = historyList.value.find(h => h.uid === historyUid)
      previewDialogVisible.value = true
      break
    case 'rename':
      newHistoryName.value = getHistoryTitle(historyList.value.find(h => h.uid === historyUid))
      renameDialogVisible.value = true
      break
    case 'delete':
      deleteHistory(historyUid)
      break
  }
}

// 加载预览的历史记录
const loadPreviewHistory = () => {
  if (!selectedHistoryUid.value || !ws || !connected.value) return
  previewDialogVisible.value = false
  switchHistory(selectedHistoryUid.value)
}

// 确认重命名
const confirmRename = () => {
  if (!newHistoryName.value.trim() || !selectedHistoryUid.value || !ws || !connected.value) return
  
  // 这里可以添加重命名功能，如果后端支持的话
  console.log('Rename history:', selectedHistoryUid.value, 'to:', newHistoryName.value)
  renameDialogVisible.value = false
  newHistoryName.value = ''
}

// 删除历史记录
const deleteHistory = (historyUid) => {
  if (!ws || !connected.value) return
  
  if (confirm('确定要删除这条历史记录吗？')) {
    ws.send(JSON.stringify({
      type: 'delete-history',
      history_uid: historyUid
    }))
    
    if (historyUid === currentHistoryUid.value) {
      currentHistoryUid.value = null
      messages.value = [{
        role: 'assistant',
        content: '你好！我是你的虚拟助手。有什么我可以帮助你的吗？'
      }]
    }
  }
}

// 发送消息
const sendMessage = () => {
  if (!inputMessage.value.trim() || !connected.value || !ws) return
  
  const message = inputMessage.value.trim()
  messages.value.push({ role: 'user', content: message })
  saveSession() // 保存会话
  inputMessage.value = ''
  scrollToBottom()
  
  ws.send(JSON.stringify({
    type: 'text-input',
    text: message,
    client_id: clientId
  }))
}

// 切换语音录制状态
const toggleVoiceRecording = async () => {
  if (isRecording.value) {
    // 停止录音并发送
    const audioBase64 = await stopRecording()
    isRecording.value = false
    
    if (audioBase64) {
      // 显示处理中提示
      ElMessage.info('正在处理语音，请稍候...')
      
      // 发送音频数据到后端
      ws.send(JSON.stringify({
        type: 'mic-audio-data',
        audio: audioBase64,
        client_id: clientId
      }))
      
      // 发送结束标记
      ws.send(JSON.stringify({
        type: 'mic-audio-end',
        client_id: clientId
      }))
    } else {
      ElMessage.warning('录音失败，请重试')
    }
  } else {
    // 请求权限并开始录音
    const hasPermission = await requestPermission()
    if (!hasPermission) {
      ElMessage.error(recorderError.value || '无法获取麦克风权限')
      return
    }
    
    const started = await startRecording()
    if (started) {
      isRecording.value = true
    } else {
      ElMessage.error('启动录音失败，请检查麦克风权限')
    }
  }
}

// 滚动到底部
const scrollToBottom = () => {
  setTimeout(() => {
    const chatContainer = document.getElementById('chatContainer')
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight
    }
  }, 100)
}

// 组件挂载时连接WebSocket
onMounted(() => {
  restoreSession() // 先尝试恢复本地会话
  connectWebSocket()
  scrollToBottom()
  startAutoSave() // 启动自动保存
})

// 组件卸载时关闭WebSocket
onUnmounted(() => {
  saveSession() // 保存当前会话
  stopAutoSave() // 停止自动保存
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.message {
  padding: 12px 16px;
  border-radius: 18px;
  max-width: 80%;
  word-wrap: break-word;
}

.user-message {
  background-color: #3b82f6;
  color: white;
  align-self: flex-end;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.assistant-message {
  background-color: #f3f4f6;
  color: #374151;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.history-item {
  background-color: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(0, 0, 0, 0.15);
  transition: all 0.2s ease;
}

.history-item:hover {
  background-color: rgba(255, 255, 255, 1);
  border-color: rgba(0, 0, 0, 0.25);
}

.history-item-container {
  position: relative;
}

.preview-message {
  border-radius: 8px;
  margin-bottom: 12px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 12px;
}

.drop-shadow-lg {
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}
</style>
