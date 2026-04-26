<template>
  <div class="space-y-8">
    <section class="panel-strong rounded-[36px] p-6 md:p-8">
      <div class="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div class="eyebrow">SQLite Debug</div>
          <h1 class="mt-4 text-3xl font-extrabold tracking-[-0.04em] text-[var(--text)]">数据库控制面板</h1>
          <p class="mt-4 max-w-3xl text-sm leading-7 text-[var(--muted)]">
            这里会直接展示当前 SQLite 数据库文件、各张表的记录数量，以及最近的用户、会话、消息和角色配置数据，方便你在浏览器里快速排查历史存储和登录状态。
          </p>
        </div>

        <div class="flex flex-col items-start gap-3 lg:items-end">
          <div class="status-chip">
            <span class="status-dot" :class="loading ? 'warning' : 'healthy'"></span>
            <span>{{ loading ? '读取中' : '已连接' }}</span>
          </div>
          <button class="action-btn primary" type="button" :disabled="loading" @click="fetchSnapshot">
            {{ loading ? '刷新中...' : '刷新数据库快照' }}
          </button>
        </div>
      </div>

      <div
        v-if="errorMessage"
        class="mt-6 rounded-[24px] border border-[rgba(170,61,49,0.2)] bg-[rgba(170,61,49,0.08)] px-4 py-3 text-sm text-[var(--danger)]"
      >
        {{ errorMessage }}
      </div>

      <div
        v-if="successMessage"
        class="mt-6 rounded-[24px] border border-[rgba(41,125,77,0.2)] bg-[rgba(41,125,77,0.08)] px-4 py-3 text-sm text-[var(--success)]"
      >
        {{ successMessage }}
      </div>

      <div class="mt-6 rounded-[24px] border border-[var(--line)] bg-white/25 px-4 py-4 text-sm text-[var(--muted)]">
        <div class="font-semibold text-[var(--text)]">数据库文件</div>
        <div class="mt-2 break-all">{{ snapshot.db_path || '未读取' }}</div>
      </div>

      <div class="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <div v-for="card in statCards" :key="card.key" class="panel rounded-[26px] p-4">
          <div class="feature-kicker">{{ card.label }}</div>
          <div class="mt-3 text-3xl font-extrabold tracking-[-0.04em] text-[var(--text)]">{{ card.value }}</div>
        </div>
      </div>
    </section>

    <section class="grid gap-6 xl:grid-cols-2">
      <div class="panel rounded-[32px] p-5">
        <div class="mb-4">
          <div class="feature-kicker">Users</div>
          <h2 class="text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">用户表</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="row in snapshot.tables.users"
            :key="`user-${row.id}`"
            class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3 text-sm"
          >
            <div class="font-semibold text-[var(--text)]">{{ row.username }}</div>
            <div class="mt-1 text-[var(--muted)]">ID: {{ row.id }}</div>
            <div class="mt-1 text-[var(--muted)]">创建时间: {{ row.created_at }}</div>
          </div>
          <div v-if="!snapshot.tables.users.length" class="text-sm text-[var(--muted)]">暂无用户数据。</div>
        </div>
      </div>

      <div class="panel rounded-[32px] p-5">
        <div class="mb-4">
          <div class="feature-kicker">Tokens</div>
          <h2 class="text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">登录 Token</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="row in snapshot.tables.auth_tokens"
            :key="`${row.user_id}-${row.created_at}`"
            class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3 text-sm"
          >
            <div class="font-semibold text-[var(--text)]">用户 ID: {{ row.user_id }}</div>
            <div class="mt-1 text-[var(--muted)]">Token 预览: {{ row.token_preview }}</div>
            <div class="mt-1 text-[var(--muted)]">创建时间: {{ row.created_at }}</div>
            <div class="mt-1 text-[var(--muted)]">过期时间: {{ row.expires_at || '无' }}</div>
          </div>
          <div v-if="!snapshot.tables.auth_tokens.length" class="text-sm text-[var(--muted)]">暂无登录 token。</div>
        </div>
      </div>

      <div class="panel rounded-[32px] p-5">
        <div class="mb-4">
          <div class="feature-kicker">Histories</div>
          <h2 class="text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">会话表</h2>
          <p class="mt-2 text-sm text-[var(--muted)]">这里只允许删除当前登录账号自己的会话。</p>
        </div>
        <div class="space-y-3">
          <div
            v-for="row in snapshot.tables.histories"
            :key="`${row.owner_uid}-${row.history_uid}`"
            class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3 text-sm"
          >
            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div class="min-w-0 flex-1">
                <div class="font-semibold break-all text-[var(--text)]">{{ row.history_uid }}</div>
                <div class="mt-1 text-[var(--muted)]">Owner: {{ row.owner_uid }}</div>
                <div class="mt-1 text-[var(--muted)]">创建时间: {{ row.created_at }}</div>
                <div class="mt-1 text-[var(--muted)]">更新时间: {{ row.updated_at }}</div>
              </div>
              <button
                v-if="canDeleteHistory(row)"
                class="action-btn secondary shrink-0"
                type="button"
                :disabled="deletingHistoryUid === row.history_uid"
                @click="deleteHistory(row)"
              >
                {{ deletingHistoryUid === row.history_uid ? '删除中...' : '删除会话' }}
              </button>
            </div>
          </div>
          <div v-if="!snapshot.tables.histories.length" class="text-sm text-[var(--muted)]">暂无会话数据。</div>
        </div>
      </div>

      <div class="panel rounded-[32px] p-5">
        <div class="mb-4">
          <div class="feature-kicker">Configs</div>
          <h2 class="text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">角色配置表</h2>
        </div>
        <div class="space-y-3">
          <div
            v-for="row in snapshot.tables.character_configs"
            :key="row.owner_uid"
            class="rounded-[20px] border border-[var(--line)] bg-white/20 px-4 py-3 text-sm"
          >
            <div class="font-semibold text-[var(--text)]">{{ row.owner_uid }}</div>
            <div class="mt-1 text-[var(--muted)]">System Prompt: {{ row.llm_system_prompt || '空' }}</div>
            <div class="mt-1 text-[var(--muted)]">情绪风格: {{ row.emotion_style || '空' }}</div>
            <div class="mt-1 text-[var(--muted)]">更新时间: {{ row.updated_at }}</div>
          </div>
          <div v-if="!snapshot.tables.character_configs.length" class="text-sm text-[var(--muted)]">暂无角色配置数据。</div>
        </div>
      </div>
    </section>

    <section class="panel rounded-[32px] p-5">
      <div class="mb-4">
        <div class="feature-kicker">Messages</div>
        <h2 class="text-xl font-extrabold tracking-[-0.03em] text-[var(--text)]">最近历史消息</h2>
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead>
            <tr class="border-b border-[var(--line)] text-left text-[var(--muted)]">
              <th class="px-3 py-2">ID</th>
              <th class="px-3 py-2">Owner</th>
              <th class="px-3 py-2">History</th>
              <th class="px-3 py-2">Role</th>
              <th class="px-3 py-2">时间</th>
              <th class="px-3 py-2">内容预览</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in snapshot.tables.history_messages"
              :key="`msg-${row.id}`"
              class="border-b border-[var(--line)]/60 align-top"
            >
              <td class="px-3 py-2 text-[var(--text)]">{{ row.id }}</td>
              <td class="px-3 py-2 break-all text-[var(--muted)]">{{ row.owner_uid }}</td>
              <td class="px-3 py-2 break-all text-[var(--muted)]">{{ row.history_uid }}</td>
              <td class="px-3 py-2 text-[var(--text)]">{{ row.role }}</td>
              <td class="px-3 py-2 text-[var(--muted)]">{{ row.timestamp }}</td>
              <td class="px-3 py-2 text-[var(--text)]">{{ row.content_preview }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="!snapshot.tables.history_messages.length" class="py-4 text-sm text-[var(--muted)]">暂无历史消息。</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const { currentUser, getAuthHeaders } = useAuth()

const loading = ref(false)
const deletingHistoryUid = ref('')
const errorMessage = ref('')
const successMessage = ref('')
const snapshot = reactive({
  db_path: '',
  counts: {
    users: 0,
    auth_tokens: 0,
    histories: 0,
    history_messages: 0,
    character_configs: 0,
  },
  tables: {
    users: [],
    auth_tokens: [],
    histories: [],
    history_messages: [],
    character_configs: [],
  },
})

const currentOwnerUid = computed(() => currentUser.value?.client_id || '')

const statCards = computed(() => [
  { key: 'users', label: '用户', value: snapshot.counts.users || 0 },
  { key: 'auth_tokens', label: 'Token', value: snapshot.counts.auth_tokens || 0 },
  { key: 'histories', label: '会话', value: snapshot.counts.histories || 0 },
  { key: 'history_messages', label: '消息', value: snapshot.counts.history_messages || 0 },
  { key: 'character_configs', label: '角色配置', value: snapshot.counts.character_configs || 0 },
])

const canDeleteHistory = (row) => row?.owner_uid && row.owner_uid === currentOwnerUid.value

const fetchSnapshot = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await fetch('/api/debug/db-summary?limit=20', {
      headers: {
        ...getAuthHeaders(),
      },
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '读取数据库快照失败。')
    }
    const payload = data.snapshot || {}
    snapshot.db_path = payload.db_path || ''
    snapshot.counts = payload.counts || snapshot.counts
    snapshot.tables = payload.tables || snapshot.tables
  } catch (error) {
    errorMessage.value = error.message || '读取数据库快照失败。'
  } finally {
    loading.value = false
  }
}

const deleteHistory = async (row) => {
  if (!canDeleteHistory(row)) {
    errorMessage.value = '你只能删除当前登录账号自己的会话。'
    return
  }

  const confirmed = window.confirm(`确认删除会话？\n\n${row.history_uid}`)
  if (!confirmed) {
    return
  }

  deletingHistoryUid.value = row.history_uid
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await fetch(`/api/debug/histories/${encodeURIComponent(row.history_uid)}`, {
      method: 'DELETE',
      headers: {
        ...getAuthHeaders(),
      },
    })
    const data = await response.json()
    if (data.status !== 'ok') {
      throw new Error(data.message || '删除会话失败。')
    }
    successMessage.value = `已删除会话：${row.history_uid}`
    await fetchSnapshot()
  } catch (error) {
    errorMessage.value = error.message || '删除会话失败。'
  } finally {
    deletingHistoryUid.value = ''
  }
}

onMounted(() => {
  fetchSnapshot()
})
</script>
