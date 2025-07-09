import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
   build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: '/src/main.js'
    }
  },
  base: '/static/'  // ¡Esta línea es crucial!
})