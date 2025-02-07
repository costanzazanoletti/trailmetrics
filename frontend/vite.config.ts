import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    sourcemap: true, // Ensure source maps are generated
  },
  esbuild: {
    sourcemap: 'inline', // Inline source maps to prevent missing files
  },
  server: {
    port: 5173,
    strictPort: true,
  },
});
