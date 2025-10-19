import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';

export default defineConfig({
  root: '.',
  plugins: [legacy({ targets: ['defaults', 'not IE 11'] })],
  build: {
    outDir: 'static-build',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: 'static/js/main.js'
      }
    }
  }
});