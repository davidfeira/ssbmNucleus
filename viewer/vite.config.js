import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  // Use relative base path for Electron compatibility
  base: './',
  server: {
    port: 3000,
    open: false, // Don't auto-open browser in Electron mode
    fs: {
      // Allow serving files from the parent directory
      allow: ['..']
    }
  },
  build: {
    outDir: 'dist',
    // Generate sourcemaps for easier debugging
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  },
  resolve: {
    alias: {
      '@storage': path.resolve(__dirname, '../storage')
    }
  },
  publicDir: 'public'
})
