import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy sang backend FastAPI để FE và BE dùng chung origin khi dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
