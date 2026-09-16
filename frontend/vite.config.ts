import { fileURLToPath, URL } from 'node:url';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // Lets every .module.scss write `@use '@/styles/abstracts' as a;`
        loadPaths: [fileURLToPath(new URL('./src', import.meta.url))],
      },
    },
  },
  server: {
    port: 5173,
  },
});
