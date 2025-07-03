import { defineConfig } from 'vite'
import path from 'path'

export default defineConfig({
  // Configuración base
  root: path.resolve(__dirname, './'),
  base: '/',
  publicDir: 'public',
  
  // Configuración del servidor de desarrollo
  server: {
    port: 3000,
    open: true // Abre el navegador automáticamente
  },

  // Configuración de compilación
  build: {
    outDir: '../backend/static',
    rollupOptions: {
      input: {
        main: './src/index.html'
      }
    }
  }
})