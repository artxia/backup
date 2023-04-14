/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'miniflare',
    environmentOptions: {
      script: '',
      kvNamespaces: ['TEST_NAMESPACE'],
    },
    include: ['tests/**/*.test.ts'],
  },
});
