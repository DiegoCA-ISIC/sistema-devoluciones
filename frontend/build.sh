#!/bin/bash

# Da permisos de ejecución a vite
chmod +x ./node_modules/.bin/vite

# Ejecuta el build
npx vite build
