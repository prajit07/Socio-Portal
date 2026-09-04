import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Allow access from other devices on the same network (e.g. testing on a phone).
    host: true,
  },
  build: {
    rolldownOptions: {
      output: {
        // Split heavy third-party libs into their own chunks so the
        // initial bundle stays small and shared deps are cached.
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('recharts')) return 'vendor-recharts';
            if (id.includes('@vis.gl') || id.includes('@googlemaps')) return 'vendor-maps';
            if (id.includes('leaflet')) return 'vendor-leaflet';
            if (id.includes('i18next') || id.includes('react-i18next')) return 'vendor-i18n';
            if (id.includes('react-router')) return 'vendor-router';
            if (id.includes('axios')) return 'vendor-axios';
            if (id.includes('/react-dom/') || id.includes('/react/') || id.includes('scheduler'))
              return 'vendor-react';
            return 'vendor';
          }
        },
      },
    },
  },
})
