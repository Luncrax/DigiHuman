import { computed, ref } from 'vue'

const AUTH_TOKEN_KEY = 'digiHuman_authToken'
const AUTH_USER_KEY = 'digiHuman_authUser'

const authToken = ref(localStorage.getItem(AUTH_TOKEN_KEY) || '')

let parsedUser = null
try {
  parsedUser = JSON.parse(localStorage.getItem(AUTH_USER_KEY) || 'null')
} catch (error) {
  parsedUser = null
}

const currentUser = ref(parsedUser)

const setAuthSession = ({ token, user }) => {
  authToken.value = token || ''
  currentUser.value = user || null

  if (authToken.value) {
    localStorage.setItem(AUTH_TOKEN_KEY, authToken.value)
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY)
  }

  if (currentUser.value) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(currentUser.value))
  } else {
    localStorage.removeItem(AUTH_USER_KEY)
  }
}

const clearAuthSession = () => {
  setAuthSession({ token: '', user: null })
}

const getAuthHeaders = () => {
  if (!authToken.value) {
    return {}
  }
  return {
    Authorization: `Bearer ${authToken.value}`,
  }
}

export function useAuth() {
  return {
    authToken,
    currentUser,
    isAuthenticated: computed(() => Boolean(authToken.value && currentUser.value)),
    setAuthSession,
    clearAuthSession,
    getAuthHeaders,
  }
}
