import { fileURLToPath, URL } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
// 开发时把 /api 转发给本地后端，和线上 Nginx 行为一致
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8010',
    },
  },
})

