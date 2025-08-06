import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',  // 让前端支持局域网访问
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',  // 或改成 http://192.168.1.103:5000
        changeOrigin: true,
      }
    }
  }
})
