import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: /api/* được chuyển tới FastAPI (:8000), tránh phải bật CORS khi gọi từ trình duyệt.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
