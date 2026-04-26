import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import { useAuth } from '../composables/useAuth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/Chat.vue')
  },
  {
    path: '/character',
    name: 'Character',
    component: () => import('../views/Character.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue')
  },
  {
    path: '/memory',
    name: 'Memory',
    component: () => import('../views/Memory.vue')
  },
  {
    path: '/database',
    name: 'Database',
    component: () => import('../views/Database.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const { isAuthenticated } = useAuth()
  const protectedRoutes = ['/chat', '/character', '/dashboard', '/memory', '/database']

  if (protectedRoutes.includes(to.path) && !isAuthenticated.value) {
    return '/login'
  }

  if (to.path === '/login' && isAuthenticated.value) {
    return '/chat'
  }

  return true
})

export default router
