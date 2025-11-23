import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy login endpoint to proxy server (port 8080) for cookie session
      // Only proxy POST requests, GET requests should be handled by React Router (SPA)
      '/login': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
        bypass: (req) => {
          // Bypass proxy for GET requests (let React Router handle them)
          if (req.method === 'GET') {
            return '/index.html'
          }
        }
      },
      // Proxy logout endpoint to proxy server (port 8080) for cookie session
      '/logout': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      // Proxy API endpoints to tracker server (port 8001)
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})

