import { expect, test, type Request } from '../../frontend/node_modules/@playwright/test/index.js'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { writeFileSync } from 'node:fs'
import path from 'node:path'

const example = 'Repair my bicycle without replacing it'
const database = process.env.RESOLENA_E2E_DATABASE!
const python = path.resolve('../.venv/bin/python')

function captureAttempt(request: Request) {
  const proof = request.headers()['x-submission-proof'] || ''
  expect(/^[0-9a-f]{64}$/.test(proof)).toBe(true)
  return { body: request.postData()!, proofDigest: createHash('sha256').update(proof).digest('hex') }
}

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
    snapshots={name:connection.execute('SELECT * FROM '+name+' ORDER BY 1, 2').fetchall() for name in
        ('request_alternative','request_alternative_evidence','evidence')}
    print(json.dumps({'rows':[{'id':row[0],'projection':json.loads(row[1])} for row in rows],
        'counts':counts,'snapshots':snapshots}))
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

test('lost HTTP response after atomic commit requires explicit same-submission recovery', async ({ page }, testInfo) => {
  const before = inspectDatabase()
  const attempts: ReturnType<typeof captureAttempt>[] = []
  let releaseLoss!: () => void
  const lossGate = new Promise<void>(resolve => { releaseLoss = resolve })
  let capture!: (value: { body: any; stored: ReturnType<typeof inspectDatabase> }) => void
  const committed = new Promise<{ body: any; stored: ReturnType<typeof inspectDatabase> }>(resolve => { capture = resolve })
  await page.route('**/api/comparisons', async route => {
    attempts.push(captureAttempt(route.request()))
    if (attempts.length === 1) {
      const response = await route.fetch({ maxRetries: 0 })
      expect(response.status()).toBe(201)
      capture({ body: await response.json(), stored: inspectDatabase() })
      await lossGate
      await route.abort('failed')
    } else {
      await route.continue()
    }
  })
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const { body: saved, stored } = await committed
    expect(stored.counts).toEqual({
      search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2,
    })
    expect(stored.rows.at(-1).projection).toEqual(saved)
    await expect(page.getByRole('status')).toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    releaseLoss()
    await expect(page.getByRole('alert')).toContainText('Delivery status is unknown')
    await expect(page.getByRole('alert')).not.toContainText('could not be saved')
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Recover submission' })).toBeEnabled()
    await expect(page.getByRole('button', { name: 'Start a fresh search' })).toBeEnabled()
    await page.waitForTimeout(300)
    expect(attempts).toHaveLength(1)
    expect(inspectDatabase()).toEqual(stored)

    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Recover submission' }).click()
    const response = await responsePromise
    expect(response.status()).toBe(200)
    const acknowledgement = await response.json()
    expect(acknowledgement).toEqual({
      outcome: 'submission_recovered', persistence: saved.persistence,
      saved_outcome: saved.outcome, assessed_at: saved.assessed_at,
    })
    expect(attempts).toHaveLength(2)
    expect(attempts[1].body === attempts[0].body).toBe(true)
    expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
    const acknowledged = page.getByRole('region', { name: 'Saved submission acknowledged' })
    await expect(acknowledged).toContainText(saved.persistence.request_id)
    await expect(acknowledged).toContainText(`Original outcome: ${saved.outcome}`)
    await expect(acknowledged).toContainText(`Originally assessed at: ${saved.assessed_at}`)
    await expect(acknowledged).toContainText('does not replay a comparison or confirm present-day facts')
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    const after = inspectDatabase()
    expect(after).toEqual(stored)
    await page.getByRole('button', { name: 'Start a fresh search' }).click()
    await expect(page.getByRole('button', { name: 'Find alternatives' })).toBeEnabled()
    await expect(acknowledged).not.toBeVisible()
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    await page.waitForTimeout(300)
    expect(attempts).toHaveLength(2)
    expect(inspectDatabase()).toEqual(after)
    const evidencePath = testInfo.outputPath('committed-recovery-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before_counts: before.counts, committed: stored, recovered: after,
        acknowledgement, requests: attempts.length, same_key_payload_and_proof: true,
        fault: 'Real API 201 verified in SQLite, then browser delivery aborted before presentation',
        no_automatic_retry_observed_ms: 300, fresh_action_sends_request: false }, null, 2))
    await testInfo.attach('committed-recovery-evidence', {
      path: evidencePath,
      contentType: 'application/json',
    })
  } finally {
    releaseLoss()
  }
})

test('explicit fresh search after recovered acknowledgement reassesses expired evidence', async ({ page }, testInfo) => {
  const clockFile = process.env.RESOLENA_E2E_CLOCK_FILE!
  expect(Boolean(clockFile)).toBe(true)
  const originalTime = '2026-10-15T10:00:00+00:00'
  const freshTime = '2027-10-16T10:00:00+00:00'
  writeFileSync(clockFile, JSON.stringify({ now: originalTime }))
  const before = inspectDatabase()
  const attempts: ReturnType<typeof captureAttempt>[] = []
  type Capture = { body: any; status: number; stored: ReturnType<typeof inspectDatabase> }
  let captureOriginal!: (value: Capture) => void
  let captureFresh!: (value: Capture) => void
  let releaseFresh!: () => void
  const originalCommit = new Promise<Capture>(resolve => { captureOriginal = resolve })
  const freshCommit = new Promise<Capture>(resolve => { captureFresh = resolve })
  const freshGate = new Promise<void>(resolve => { releaseFresh = resolve })
  await page.route('**/api/comparisons', async route => {
    attempts.push(captureAttempt(route.request()))
    const response = await route.fetch({ maxRetries: 0 })
    const capture = { body: await response.json(), status: response.status(), stored: inspectDatabase() }
    if (attempts.length === 1) {
      captureOriginal(capture)
      await route.abort('failed')
    } else {
      if (attempts.length === 3) {
        captureFresh(capture)
        await freshGate
      }
      await route.fulfill({ response })
    }
  })
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const { body: original, status: originalStatus, stored: originalStored } = await originalCommit
    expect(originalStatus).toBe(201)
    expect(original.outcome).toBe('comparison')
    expect(original.assessed_at).toBe(originalTime)
    expect(originalStored.rows.at(-1).projection).toEqual(original)
    await expect(page.getByRole('alert')).toContainText('Delivery status is unknown')
    await expect(page.getByRole('status')).not.toBeVisible()
    const recoveryResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Recover submission' }).click()
    const recovered = await recoveryResponse
    expect(recovered.status()).toBe(200)
    const acknowledgement = await recovered.json()
    expect(acknowledgement).toEqual({ outcome: 'submission_recovered', persistence: original.persistence,
      saved_outcome: 'comparison', assessed_at: originalTime })
    expect(attempts[1].body === attempts[0].body).toBe(true)
    expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
    await expect(page.getByRole('region', { name: 'Saved submission acknowledged' })).toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    const recoveredStored = inspectDatabase()
    expect(recoveredStored).toEqual(originalStored)

    writeFileSync(clockFile, JSON.stringify({ now: freshTime }))
    await page.getByRole('button', { name: 'Start a fresh search' }).click()
    await expect(page.getByRole('button', { name: 'Find alternatives' })).toBeEnabled()
    await expect(page.getByRole('region', { name: 'Saved submission acknowledged' })).not.toBeVisible()
    await page.waitForTimeout(300)
    expect(attempts.length).toBe(2)
    expect(inspectDatabase()).toEqual(originalStored)
    await page.getByLabel('Describe your request').fill('Velo')
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const { body: fresh, status: freshStatus, stored: freshStored } = await freshCommit
    expect(freshStatus).toBe(201)
    expect(fresh.outcome).toBe('insufficient_coverage')
    expect(fresh.assessed_at).toBe(freshTime)
    expect(fresh.coverage.limitation_codes).toContain('essential_evidence_expired')
    expect('comparison' in fresh).toBe(false)
    expect(fresh.persistence.request_id === original.persistence.request_id).toBe(false)
    expect(attempts.length).toBe(3)
    const currentPayload = JSON.parse(attempts[2].body)
    expect(currentPayload.submission_key === JSON.parse(attempts[0].body).submission_key).toBe(false)
    expect(attempts[2].proofDigest === attempts[0].proofDigest).toBe(false)
    expect(currentPayload.text).toBe('Velo')
    expect(currentPayload.search_location).toEqual({ country_code: 'CH' })
    expect(currentPayload.location_choice).toBe('provided')
    expect(currentPayload.language_context).toEqual({ browser_language: 'en' })
    expect(freshStored.counts).toEqual({ search_request: before.counts.search_request + 2,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2 })
    expect(freshStored.rows.slice(0, -1)).toEqual(originalStored.rows)
    expect(freshStored.rows.at(-1).projection).toEqual(fresh)
    expect(freshStored.snapshots).toEqual(originalStored.snapshots)
    await expect(page.getByRole('status')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    releaseFresh()
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).toBeVisible()
    await expect(page.getByText(fresh.persistence.request_id, { exact: true })).toBeVisible()
    await expect(page.getByText('Required evidence has expired;', { exact: false })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByLabel('Describe your request')).toHaveValue('Velo')
    expect(inspectDatabase()).toEqual(freshStored)
    const evidencePath = testInfo.outputPath('fresh-search-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before_counts: before.counts, original: originalStored,
      recovered: recoveredStored, fresh: freshStored, acknowledgement, requests: attempts.length,
      recovery_same_body_key_and_proof: true, fresh_new_key_and_proof: true,
      fresh_uses_current_text: currentPayload.text, original_assessed_at: originalTime,
      fresh_assessed_at: freshTime, fresh_action_requests: 0, idle_observation_ms: 300,
      raw_originating_proofs_recorded: false }, null, 2))
    await testInfo.attach('fresh-search-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    releaseFresh()
    writeFileSync(clockFile, JSON.stringify({ now: originalTime }))
  }
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

test('shared input with unsupported browser language requests an explicit choice before saving', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'es-ES' })
  const page = await context.newPage()
  const before = inspectDatabase()
  try {
    await page.goto('/')
    await expect(page.getByLabel('Explanation language', { exact: true })).not.toBeVisible()
    await page.getByLabel('Describe your request').fill('Velo')
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    await expect(page.getByText('Sprache wählen / Choisir la langue / Scegli la lingua / Choose a language.')).toBeVisible()
    await expect(page.getByLabel('Explanation language', { exact: true })).toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    expect(inspectDatabase().counts).toEqual(before.counts)
    await page.getByLabel('Explanation language', { exact: true }).selectOption('en')
    await page.getByRole('button', { name: 'Try again' }).click()
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
    await expect(page.getByTestId('language-context')).toContainText('en; user choice')
    const stored = inspectDatabase()
    expect(stored.rows.at(-1).projection.language.recognition.status).toBe('unknown')
    expect(stored.rows.at(-1).projection.language.explanation_language).toBe('en')
  } finally {
    await context.close()
  }
})

test('language correction is a new explicit submission and does not fake a missing translation', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Describe your request').fill(example)
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  const before = inspectDatabase()
  await page.getByRole('button', { name: 'Change explanation language' }).click()
  await page.getByLabel('Explanation language', { exact: true }).selectOption('fr')
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  await expect(page.getByRole('alert')).toContainText('Only the English synthetic rendering is configured')
  await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  expect(inspectDatabase().counts).toEqual(before.counts)
  await page.getByLabel('Describe your request').fill('')
  await page.getByLabel('Describe your request').fill(example)
  const pending = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  const response = await pending
  expect(response.status()).toBe(201)
  expect((await response.json()).language.explanation_language).toBe('en')
})

test('capability limitation and meaning clarification preserve fields without search records', async ({ page }) => {
  const before = inspectDatabase()
  await page.goto('/')
  await page.getByLabel('Describe your request').fill('Synthetic unsupported input')
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  await expect(page.getByRole('alert')).toContainText('Synthetic capability limitation')
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.getByLabel('Describe your request')).toHaveValue('Synthetic unsupported input')
  await page.getByLabel('Describe your request').fill('Synthetic unclear clause')
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  await expect(page.getByText('Clarify the synthetic clause before continuing.')).toBeVisible()
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  expect(inspectDatabase().counts).toEqual(before.counts)
})

test('an unavailable browser-preferred rendering still allows explicit correction', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'fr-CH' })
  const page = await context.newPage()
  const before = inspectDatabase()
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill('Velo')
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    await expect(page.getByRole('alert')).toContainText('Only the English synthetic rendering is configured')
    expect(inspectDatabase().counts).toEqual(before.counts)
    await page.getByRole('button', { name: 'Change explanation language' }).click()
    await page.getByLabel('Explanation language', { exact: true }).selectOption('en')
    await page.getByRole('button', { name: 'Try again' }).click()
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByTestId('language-context')).toContainText('en; user choice')
  } finally {
    await context.close()
  }
})

for (const language of ['de', 'fr', 'it', 'en']) {
  test(`source-bound synthetic ${language} wording is displayed only after commit`, async ({ browser }) => {
    const context = await browser.newContext({ locale: `${language}-CH` })
    const page = await context.newPage()
    let release!: () => void
    const gate = new Promise<void>(resolve => { release = resolve })
    let committed!: (body: unknown) => void
    const saved = new Promise<any>(resolve => { committed = resolve })
    await page.route('**/api/comparisons', async route => {
      const response = await route.fetch()
      committed(await response.json())
      await gate
      await route.fulfill({ response })
    })
    try {
      await page.goto('/')
      await page.getByLabel('Describe your request').fill('Synthetic hourly bicycle repair')
      await page.getByRole('button', { name: 'Find alternatives' }).click()
      const body = await saved
      const option = body.comparison.options[0]
      expect(inspectDatabase().rows.at(-1).projection).toEqual(body)
      await expect(page.getByRole('status')).toBeVisible()
      await expect(page.getByTestId('saved-option')).toHaveCount(0)
      release()
      const shown = page.getByTestId('saved-option')
      await expect(shown).toHaveCount(1)
      await expect(shown.getByText(option.presentation.financial, { exact: true })).toBeVisible()
      await expect(shown.getByText(option.presentation.environmental, { exact: true })).toBeVisible()
      await expect(shown.getByText(option.presentation.total_cost, { exact: true })).toBeVisible()
      await expect(shown.getByText(option.presentation.conditions, { exact: true })).toBeVisible()
      await expect(shown.getByText(option.presentation.financial, { exact: true })).toHaveAttribute('lang', language)
      expect(option.rendering.review.synthetic).toBe(true)
      await shown.getByText('Evidence: Synthetic hourly provider').click()
      await expect(shown.getByRole('link', { name: 'https://synthetic.example.invalid/hourly-repair-v1' })).toHaveAttribute('href', 'https://synthetic.example.invalid/hourly-repair-v1')
      await expect(shown.locator('blockquote')).toHaveText(option.evidence[0].supporting_quote)
      await expect(page.getByLabel('Search country')).toHaveValue('CH')
    } finally {
      release()
      await context.close()
    }
  })
}

test('pending source-bound wording is an unsaved rendering limitation', async ({ page }) => {
  const before = inspectDatabase()
  await page.goto('/')
  await page.getByLabel('Describe your request').fill('Synthetic pending bicycle repair')
  await page.getByRole('button', { name: 'Find alternatives' }).click()
  await expect(page.getByRole('alert')).toContainText('Reviewed wording is unavailable')
  await expect(page.getByTestId('saved-option')).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  await expect(page.getByLabel('Describe your request')).toHaveValue('Synthetic pending bicycle repair')
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await expect(page.getByRole('status')).not.toBeVisible()
  expect(inspectDatabase().counts).toEqual(before.counts)
})
