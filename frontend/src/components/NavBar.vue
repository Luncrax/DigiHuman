<template>
  <header class="fixed inset-x-0 top-0 z-50 px-4 pt-4">
    <div class="panel-strong mx-auto flex w-full max-w-[1280px] items-center justify-between rounded-[28px] px-4 py-3 md:px-6">
      <router-link to="/" class="flex items-center gap-3 no-underline">
        <div class="flex h-12 w-12 items-center justify-center rounded-2xl border border-[var(--line)] bg-white/25 text-[var(--accent)] shadow-sm">
          <el-icon size="26"><VideoPlay /></el-icon>
        </div>
        <div>
          <div class="text-[0.72rem] font-bold uppercase tracking-[0.18em] text-[var(--muted)]">Emotion AI Avatar</div>
          <div class="text-lg font-extrabold tracking-[-0.03em] text-[var(--text)]">DigiHuman Console</div>
        </div>
      </router-link>

      <nav class="hidden items-center gap-1 xl:flex">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-pill"
          :class="{ active: route.path === item.path }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="flex items-center gap-2">
        <div
          v-if="currentUser"
          class="hidden rounded-2xl border border-[var(--line)] bg-white/25 px-3 py-2 text-xs font-semibold text-[var(--text)] lg:block"
        >
          {{ currentUser.username }}
        </div>

        <router-link v-if="!currentUser" to="/login" class="action-btn secondary hidden md:inline-flex no-underline">
          <el-icon><User /></el-icon>
          <span>登录</span>
        </router-link>

        <button v-else class="action-btn secondary hidden md:inline-flex" type="button" @click="logout">
          <el-icon><User /></el-icon>
          <span>退出</span>
        </button>

        <router-link to="/settings" class="action-btn secondary hidden md:inline-flex no-underline">
          <el-icon><Setting /></el-icon>
          <span>启动自检</span>
        </router-link>

        <button class="action-btn secondary" type="button" @click="toggleTheme">
          <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
          <span class="hidden sm:inline">{{ isDark ? '深色' : '浅色' }}</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import {
  ChatLineRound,
  Collection,
  DataAnalysis,
  DataLine,
  HomeFilled,
  Moon,
  Reading,
  Setting,
  Sunny,
  User,
  VideoPlay,
} from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useTheme } from '../composables/useTheme'

const route = useRoute()
const router = useRouter()
const { isDark, toggleTheme } = useTheme()
const { currentUser, authToken, clearAuthSession } = useAuth()

const navItems = [
  { path: '/', label: '总览', icon: HomeFilled },
  { path: '/chat', label: '对话控制台', icon: ChatLineRound },
  { path: '/study-assistant', label: '学习助手', icon: Reading },
  { path: '/dashboard', label: '运行看板', icon: DataLine },
  { path: '/memory', label: '会话总览', icon: Collection },
  { path: '/character', label: '角色配置', icon: User },
  { path: '/database', label: '数据库', icon: DataAnalysis },
]

const logout = async () => {
  try {
    if (authToken.value) {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${authToken.value}`,
        },
      })
    }
  } catch (error) {
    console.warn('Logout request failed:', error)
  } finally {
    clearAuthSession()
    localStorage.removeItem('digiHuman_clientId')
    localStorage.removeItem('digiHuman_messages_v2')
    localStorage.removeItem('digiHuman_currentHistoryUid')
    router.push('/login')
  }
}
</script>
