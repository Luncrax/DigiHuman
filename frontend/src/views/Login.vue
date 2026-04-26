<template>
  <div class="mx-auto max-w-[720px]">
    <section class="panel-strong rounded-[34px] p-6 md:p-8">
      <div class="eyebrow">Account</div>
      <h1 class="mt-3 text-3xl font-extrabold tracking-[-0.04em] text-[var(--text)]">账户登录</h1>
      <p class="mt-3 text-sm leading-7 text-[var(--muted)]">
        登录后会使用稳定账户来绑定对话历史，SQLite 会继续保存你的会话记录。
      </p>

      <div class="mt-6 flex gap-3">
        <button class="action-btn" :class="mode === 'login' ? 'primary' : 'secondary'" type="button" @click="mode = 'login'">登录</button>
        <button class="action-btn" :class="mode === 'register' ? 'primary' : 'secondary'" type="button" @click="mode = 'register'">注册</button>
      </div>

      <div class="mt-6 grid gap-4">
        <label class="block">
          <div class="mb-2 text-sm font-semibold text-[var(--text)]">用户名</div>
          <input v-model="form.username" class="w-full rounded-2xl border border-[var(--line)] bg-white/25 px-4 py-3 text-[var(--text)] outline-none" />
        </label>

        <label class="block">
          <div class="mb-2 text-sm font-semibold text-[var(--text)]">密码</div>
          <input v-model="form.password" type="password" class="w-full rounded-2xl border border-[var(--line)] bg-white/25 px-4 py-3 text-[var(--text)] outline-none" />
        </label>
      </div>

      <div v-if="message" class="mt-5 rounded-[20px] border border-[var(--line)] bg-white/30 px-4 py-3 text-sm text-[var(--muted)]">
        {{ message }}
      </div>

      <div class="mt-6 flex gap-3">
        <button class="action-btn primary" type="button" :disabled="loading" @click="submit">
          {{ loading ? '提交中...' : (mode === 'login' ? '登录并进入控制台' : '注册并进入控制台') }}
        </button>
        <router-link to="/" class="action-btn secondary no-underline">返回首页</router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { setAuthSession } = useAuth()

const mode = ref('login')
const loading = ref(false)
const message = ref('')
const form = reactive({
  username: '',
  password: '',
})

const parseJsonResponse = async (response) => {
  const raw = await response.text()
  if (!raw.trim()) {
    throw new Error('后端没有返回有效内容，请检查服务是否正常启动。')
  }

  try {
    return JSON.parse(raw)
  } catch (error) {
    const short = raw.slice(0, 120)
    throw new Error(`后端返回了非 JSON 内容：${short}`)
  }
}

const submit = async () => {
  if (!form.username.trim() || !form.password.trim()) {
    ElMessage.warning('请输入用户名和密码。')
    return
  }

  loading.value = true
  message.value = ''

  try {
    const response = await fetch(`/api/auth/${mode.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: form.username.trim(),
        password: form.password,
      }),
    })

    const data = await parseJsonResponse(response)
    if (data.status !== 'ok') {
      throw new Error(data.message || '认证失败。')
    }

    setAuthSession({
      token: data.token,
      user: data.user,
    })
    localStorage.setItem('digiHuman_clientId', data.user.client_id)
    message.value = `${mode.value === 'login' ? '登录' : '注册'}成功，正在进入对话控制台。`
    ElMessage.success(message.value)
    router.push('/chat')
  } catch (error) {
    message.value = error.message || '认证失败。'
    ElMessage.error(message.value)
  } finally {
    loading.value = false
  }
}
</script>
