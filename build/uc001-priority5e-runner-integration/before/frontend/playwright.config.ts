import { defineConfig } from '@playwright/test'
import { randomUUID } from 'node:crypto'
import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
process.env.RESOLENA_E2E_DATABASE ??= path.join(root, 'build/test-only', `browser-${randomUUID()}.sqlite3`)
process.env.PLAYWRIGHT_BROWSERS_PATH ??= path.join(root, 'build/playwright')
if (!process.env.RESOLENA_E2E_CLOCK_FILE) {
  process.env.RESOLENA_E2E_CLOCK_FILE = path.join(root, 'build/test-only', `browser-clock-${randomUUID()}.json`)
  mkdirSync(path.dirname(process.env.RESOLENA_E2E_CLOCK_FILE), { recursive: true })
  writeFileSync(process.env.RESOLENA_E2E_CLOCK_FILE, JSON.stringify({ now: '2026-10-15T10:00:00+00:00' }))
}

export default defineConfig({
  testDir: '../tests/e2e',
  workers: 1,
  retries: 0,
  outputDir: '../build/uc001-slice1/browser',
  reporter: [['list'], ['json', { outputFile: '../build/uc001-slice1/playwright.json' }]],
  use: { baseURL: 'http://127.0.0.1:5175', trace: 'off' },
  webServer: [
    {
      command: '.venv/bin/python -m tests.support.demo --port 8011',
      cwd: root,
      env: { PYTHONPATH: 'src:.', RESOLENA_TEST_DATABASE: process.env.RESOLENA_E2E_DATABASE,
        RESOLENA_TEST_CLOCK_FILE: process.env.RESOLENA_E2E_CLOCK_FILE || '' },
      url: 'http://127.0.0.1:8011/health',
      reuseExistingServer: false,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5175 --strictPort',
      env: { RESOLENA_API_TARGET: 'http://127.0.0.1:8011' },
      url: 'http://127.0.0.1:5175',
      reuseExistingServer: false,
      gracefulShutdown: { signal: 'SIGTERM', timeout: 5000 },
    },
  ],
})
