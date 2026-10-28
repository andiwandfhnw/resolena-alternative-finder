import { expect, test } from '../../frontend/node_modules/@playwright/test/index.js'
import { execFileSync } from 'node:child_process'
import path from 'node:path'

const example = 'Repair my bicycle without replacing it'
const database = process.env.RESOLENA_E2E_DATABASE!
const python = path.resolve('../.venv/bin/python')

function inspectDatabase(action = 'read') {
  return JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    if sys.argv[2] == 'fail':
        connection.execute("""CREATE TRIGGER browser_save_failure BEFORE INSERT ON request_alternative_evidence
            BEGIN SELECT RAISE(ABORT, 'synthetic browser save failure'); END""")
    elif sys.argv[2] == 'failcoverage':
        connection.execute("""CREATE TRIGGER browser_save_failure BEFORE INSERT ON search_request
            BEGIN SELECT RAISE(ABORT, 'synthetic coverage save failure'); END""")
    elif sys.argv[2] == 'restore':
        connection.execute('DROP TRIGGER browser_save_failure')
    rows=connection.execute('SELECT id, projection FROM search_request ORDER BY rowid').fetchall()
    counts={name:connection.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in
        ('search_request','request_alternative','request_alternative_evidence')}
    print(json.dumps({'rows':[{'id':row[0],'projection':json.loads(row[1])} for row in rows],'counts':counts}))
`, database, action], { encoding: 'utf8' }))
}

test('browser displays exactly the committed API comparison and stable database identities', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Synthetic demonstration', { exact: true })).toBeVisible()
  await page.getByLabel('Describe your request').fill(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  const response = await responsePromise
  expect(response.status()).toBe(201)
  const saved = await response.json()
  await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  await expect(page.getByTestId('request-id')).toHaveText(saved.persistence.request_id)
  const options = page.getByTestId('saved-option')
  await expect(options).toHaveCount(2)
  await expect(options.first()).toContainText('CHF 45.00')
  await expect(options.first()).toContainText('unknown charges are not zero')
  await expect(options.first()).toContainText('No supported environmental/resource information.')
  await expect(options.first()).toContainText('Availability')
  for (const [index, option] of saved.comparison.options.entries()) {
    await expect(options.nth(index)).toHaveAttribute('data-option-id', option.option_id)
    await expect(options.nth(index).getByRole('heading')).toHaveText(option.display_name)
  }
  const stored = inspectDatabase()
  expect(stored.counts).toEqual({ search_request: 1, request_alternative: 2, request_alternative_evidence: 2 })
  expect(stored.rows[0].projection).toEqual(saved)
  await expect(page.getByRole('status')).not.toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  expect(inspectDatabase().rows[0].id).toBe(saved.persistence.request_id)
})

test('real SQLite write failure preserves fields and never presents a completed comparison', async ({ page }) => {
  const before = inspectDatabase('fail')
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const response = await responsePromise
    expect(response.status()).toBe(503)
    expect((await response.json()).persistence.state).toBe('failed')
    await expect(page.getByRole('alert')).toContainText('The comparison could not be saved')
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByRole('button', { name: 'Try again' })).toBeEnabled()
    expect(inspectDatabase().counts).toEqual(before.counts)
  } finally {
    inspectDatabase('restore')
  }
})

test('changed-country request saves coverage without invented matches or global absence claims', async ({ page }) => {
  const before = inspectDatabase()
  await page.goto('/')
  await page.getByLabel('Describe your request').fill(example)
  await page.getByLabel('Search country').fill('DE')
  const pending = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  const response = await pending
  expect(response.status()).toBe(201)
  const body = await response.json()
  expect(body.outcome).toBe('insufficient_coverage')
  await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).toBeVisible()
  await expect(page.getByText('Research is unavailable in this increment; alternatives may exist.', { exact: false })).toBeVisible()
  await expect(page.getByTestId('saved-option')).toHaveCount(0)
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Search country')).toHaveValue('DE')
  await expect(page.getByRole('status')).not.toBeVisible()
  const stored = inspectDatabase()
  expect(stored.counts.search_request).toBe(before.counts.search_request + 1)
  expect(stored.counts.request_alternative).toBe(before.counts.request_alternative)
  expect(stored.rows.at(-1).projection).toEqual(body)
})

test('coverage-save failure is distinct from saved coverage and retains fields', async ({ page }) => {
  const before = inspectDatabase('failcoverage')
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await page.getByLabel('Search country').fill('DE')
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    await expect(page.getByRole('alert')).toContainText('coverage outcome could not be saved')
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).not.toBeVisible()
    await expect(page.getByLabel('Search country')).toHaveValue('DE')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByRole('status')).not.toBeVisible()
    expect(inspectDatabase().counts).toEqual(before.counts)
  } finally {
    inspectDatabase('restore')
  }
})
