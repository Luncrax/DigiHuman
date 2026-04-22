import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

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
    path: '/voice',
    name: 'Voice',
    component: () => import('../views/Voice.vue')
  },
  {
    path: '/live2d-view',
    name: 'Live2D',
    component: () => import('../views/Live2D.vue')
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
