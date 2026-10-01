import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// In development the client proxies Socket.IO to the local game server so
// everything runs on one origin, exactly like the single-service deployment.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/socket.io': { target: 'http://localhost:3001', ws: true },
      '/health': { target: 'http://localhost:3001' },
    },
  },
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 900,
  },
});
