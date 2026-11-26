import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Proxy de /api al backend FastAPI.
// - Si corres `npm run dev` en tu PC: http://localhost:8001 (por defecto;
//   el compose publica el backend del contenedor en el 8001 del host).
// - En Docker (docker-compose.yml): BACKEND_TARGET=http://backend:8000,
//   porque dentro del contenedor "localhost" NO es el backend.
const objetivoBackend = process.env.BACKEND_TARGET ?? 'http://localhost:8001';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: objetivoBackend,
        changeOrigin: true,
      },
    },
  },
});
