import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Configuración separada de `vite.config.ts` (no necesita el plugin de
// Tailwind para correr tests con jsdom). `npm run build`/`dev` siguen
// usando exclusivamente `vite.config.ts`.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: false,
    css: false,
  },
})
