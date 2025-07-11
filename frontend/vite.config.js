import { defineConfig } from 'vite'
import path from 'path'

export default defineConfig({
  root: path.resolve(__dirname, './'),
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'src/main.js'),
        styles: path.resolve(__dirname, 'css/styles.css') // Asegura que CSS se procese
      }
    }
  },
  css: {
    devSourcemap: true // Para mejor debugging
  },
  base: '/static/' // ¡Muy importante!
})