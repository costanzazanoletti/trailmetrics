/// <reference types="node" />
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  // Load only variables prefixed with VITE_
  const env = loadEnv(mode, process.cwd(), 'VITE_');

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 3000,
      strictPort: true,
    },
    define: {
      'process.env': env, // Assicura che tutte le variabili VITE_ siano accessibili
      VITE_STRAVA_CLIENT_ID: JSON.stringify(env.VITE_STRAVA_CLIENT_ID),
      VITE_API_AUTH__BASE_URL: JSON.stringify(env.VITE_API_AUTH__BASE_URL),
      VITE_API_ACTIVITY_BASE_URL: JSON.stringify(
        env.VITE_API_ACTIVITY_BASE_URL
      ),
    },
  };
});
