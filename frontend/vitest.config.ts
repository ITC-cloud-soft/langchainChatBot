import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/services': path.resolve(__dirname, './src/services'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    globals: true,
    css: true,
    testTimeout: 5000,
    isolate: true,
    threads: false,
    maxWorkers: 1,
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: [
      'src/**/*.d.ts',
      'src/index.tsx',
      'src/setupTests.ts',
      'src/reportWebVitals.ts',
      'node_modules/**',
    ],
    mockReset: true,
    restoreMocks: true,
    clearMocks: true,
    pool: 'forks',
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    environmentOptions: {
      jsdom: {
        resources: 'usable',
      },
    },
  },
  define: {
    global: 'globalThis',
  },
});