import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:8006', changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, '') }
    }
  }
});
// Development proxy doesn't inject API_TOKEN. Use Docker/Nginx for authenticated local testing.
