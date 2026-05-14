import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy API requests to Flask
      '/api': {
        target: 'http://00.00.00.0:3000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy WebSocket requests (Socket.IO) to Flask
      '/socket.io': {
        target: 'http://00.00.00.0:3000',
        changeOrigin: true,
        ws: true, // Important for WebSockets!
      }
    }
  }
})
