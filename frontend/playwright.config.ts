import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  webServer: {
    command: 'DEMO_OFFLINE=1 ../start-demo.sh',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
    gracefulShutdown: { signal: 'SIGINT', timeout: 10000 },
  },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    headless: true,
    channel: 'chrome',
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
  },
  reporter: 'list',
})
