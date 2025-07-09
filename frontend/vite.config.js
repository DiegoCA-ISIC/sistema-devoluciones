import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  root: path.resolve(__dirname, './'),
  server: {
    proxy: {
      '/api': {
        target: 'https://sistema-devoluciones.onrender.com',  // ¡URL de tu backend en Render!
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/main.js')
      }
    }
  },
  base: '/frontend/'  // Esto es crucial para las rutas en producción

})