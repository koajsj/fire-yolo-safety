import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前端开发服务器配置
// 通过代理把 /api、/results、/uploads 请求转发到后端 FastAPI（默认 8000 端口）
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/results': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
