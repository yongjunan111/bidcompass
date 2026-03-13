import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  base: '/static/frontend/',
  build: {
    outDir: path.resolve(__dirname, '../static/frontend'),
    emptyOutDir: true,
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        entryFileNames: 'assets/app.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: (assetInfo) => {
          const extension = path.extname(assetInfo.name ?? '');
          if (extension === '.css') {
            return 'assets/app.css';
          }
          return 'assets/[name][extname]';
        },
      },
    },
  },
});
