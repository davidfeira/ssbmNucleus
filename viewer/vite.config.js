import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    fs: {
      // Allow serving files from the parent directory
      allow: ['..']
    }
  },
  resolve: {
    alias: {
      '@storage': path.resolve(__dirname, '../storage')
    }
  },
  publicDir: 'public'
})
