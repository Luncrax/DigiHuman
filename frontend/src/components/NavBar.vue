<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 transition-colors duration-300">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center gap-2">
          <el-icon class="text-2xl text-blue-500"><ChatDotRound /></el-icon>
          <span class="text-xl font-bold text-gray-900 dark:text-white transition-colors duration-300">DigiHuman</span>
        </div>
        
        <div class="hidden md:flex items-center gap-1">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            :class="{ active: $route.path === item.path }"
          >
            <el-icon class="mr-1"><component :is="item.icon" /></el-icon>
            {{ item.title }}
          </router-link>
        </div>

        <div class="flex items-center gap-2">
          <el-button circle class="glass-btn" @click="toggleTheme">
            <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
          </el-button>
          <el-button circle class="glass-btn" @click="showSettings">
            <el-icon><Setting /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { 
  ChatDotRound, 
  Moon, 
  Sunny, 
  Setting,
  HomeFilled,
  ChatLineRound,
  Microphone,
  VideoPlay,
  User,
  DataLine,
  Setting as SettingIcon
} from '@element-plus/icons-vue'
import { useTheme } from '../composables/useTheme'

const { isDark, toggleTheme } = useTheme()

const menuItems = [
  { path: '/', title: '首页', icon: 'HomeFilled' },
  { path: '/chat', title: '聊天', icon: 'ChatLineRound' },
  { path: '/voice', title: '语音', icon: 'Microphone' },
  { path: '/live2d-view', title: 'Live2D', icon: 'VideoPlay' },
  { path: '/character', title: '角色', icon: 'User' },
  { path: '/dashboard', title: '仪表板', icon: 'DataLine' },
]

const showSettings = () => {
  console.log('Show settings')
}
</script>

<style scoped>
.nav-link {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 20px;
  color: #6b7280;
  text-decoration: none;
  transition: all 0.2s ease;
  font-weight: 500;
}

.nav-link:hover,
.nav-link.active {
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
}

.dark .nav-link {
  color: #9ca3af;
}

.dark .nav-link:hover,
.dark .nav-link.active {
  background: rgba(0, 122, 255, 0.2);
  color: #60a5fa;
}

.glass-btn {
  background: rgba(120, 120, 128, 0.12) !important;
  border: none !important;
  color: #6b7280 !important;
}

.glass-btn:hover {
  background: rgba(120, 120, 128, 0.2) !important;
  color: #007aff !important;
}

.dark .glass-btn {
  background: rgba(120, 120, 128, 0.2) !important;
  color: #9ca3af !important;
}

.dark .glass-btn:hover {
  background: rgba(120, 120, 128, 0.3) !important;
  color: #60a5fa !important;
}
</style>
