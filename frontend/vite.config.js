import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      '/ws': {
        target: 'ws://10.0.8.13:8001',
        ws: true,
      },
      '/api': {
        target: 'http://10.0.8.13:8001',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://10.0.8.13:8001',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
