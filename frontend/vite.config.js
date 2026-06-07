import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During dev, proxy API + poster requests to the FastAPI backend on :8000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8787',
    },
  },
})
