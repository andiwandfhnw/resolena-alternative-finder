# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> explicit locality confirmation saves reference-unverified intent without unsupported coverage
- Location: ../tests/e2e/saved-comparison.spec.ts:70:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByRole('region', { name: 'Clarification', exact: true })
Expected substring: "Confirmation establishes intended scope only."
Received string:    "The locality cannot currently be verified because locality reference data is unavailable. Correct the fields or explicitly continue country-only. This does not establish local applicability."
Timeout: 5000ms

Call log:
  - Expect "toContainText" getByRole('region', { name: 'Clarification', exact: true }) with timeout 5000ms
  - waiting for getByRole('region', { name: 'Clarification', exact: true })
    14 × locator resolved to <section aria-label="Clarification">…</section>
       - unexpected value "The locality cannot currently be verified because locality reference data is unavailable. Correct the fields or explicitly continue country-only. This does not establish local applicability."

```

```yaml
- region "Clarification":
  - paragraph: The locality cannot currently be verified because locality reference data is unavailable. Correct the fields or explicitly continue country-only. This does not establish local applicability.
```

# Test source

```ts
  1   | import { expect, test, type Request } from '../../frontend/node_modules/@playwright/test/index.js'
  2   | import { execFileSync } from 'node:child_process'
  3   | import { createHash } from 'node:crypto'
  4   | import { existsSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs'
  5   | import path from 'node:path'
  6   | 
  7   | const example = 'Repair my bicycle without replacing it'
  8   | const database = process.env.RESOLENA_E2E_DATABASE!
  9   | const python = path.resolve('../.venv/bin/python')
  10  | 
  11  | function captureAttempt(request: Request) {
  12  |   const proof = request.headers()['x-submission-proof'] || ''
  13  |   expect(/^[0-9a-f]{64}$/.test(proof)).toBe(true)
  14  |   return { body: request.postData()!, proofDigest: createHash('sha256').update(proof).digest('hex') }
  15  | }
  16  | 
  17  | function inspectDatabase(action = 'read') {
  18  |   return JSON.parse(execFileSync(python, ['-c', `
  19  | import json,sqlite3,sys
  20  | with sqlite3.connect(sys.argv[1]) as connection:
  21  |     if sys.argv[2] == 'fail':
  22  |         connection.execute("""CREATE TRIGGER browser_save_failure BEFORE INSERT ON request_alternative_evidence
  23  |             BEGIN SELECT RAISE(ABORT, 'synthetic browser save failure'); END""")
  24  |     elif sys.argv[2] == 'failcoverage':
  25  |         connection.execute("""CREATE TRIGGER browser_save_failure BEFORE INSERT ON search_request
  26  |             BEGIN SELECT RAISE(ABORT, 'synthetic coverage save failure'); END""")
  27  |     elif sys.argv[2] == 'restore':
  28  |         connection.execute('DROP TRIGGER browser_save_failure')
  29  |     rows=connection.execute('SELECT id, projection FROM search_request ORDER BY rowid').fetchall()
  30  |     counts={name:connection.execute('SELECT count(*) FROM '+name).fetchone()[0] for name in
  31  |         ('search_request','request_alternative','request_alternative_evidence')}
  32  |     snapshots={name:connection.execute('SELECT * FROM '+name+' ORDER BY 1, 2').fetchall() for name in
  33  |         ('request_alternative','request_alternative_evidence','evidence')}
  34  |     print(json.dumps({'rows':[{'id':row[0],'projection':json.loads(row[1])} for row in rows],
  35  |         'counts':counts,'snapshots':snapshots}))
  36  | `, database, action], { encoding: 'utf8' }))
  37  | }
  38  | 
  39  | test('browser displays exactly the committed API comparison and stable database identities', async ({ page }) => {
  40  |   await page.goto('/')
  41  |   await expect(page.getByText('Development demonstration', { exact: true })).toBeVisible()
  42  |   await page.getByLabel('Describe your request').fill(example)
  43  |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  44  |   const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons') && response.request().method() === 'POST')
  45  |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  46  |   const response = await responsePromise
  47  |   expect(response.status()).toBe(201)
  48  |   const saved = await response.json()
  49  |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  50  |   await expect(page.getByTestId('request-id')).toHaveText(saved.persistence.request_id)
  51  |   const options = page.getByTestId('saved-option')
  52  |   await expect(options).toHaveCount(2)
  53  |   await expect(options.first()).toContainText('CHF 45.00')
  54  |   await expect(options.first()).toContainText('unknown charges are not zero')
  55  |   await expect(options.first()).toContainText('No supported environmental/resource information.')
  56  |   await expect(options.first()).toContainText('Availability')
  57  |   for (const [index, option] of saved.comparison.options.entries()) {
  58  |     await expect(options.nth(index)).toHaveAttribute('data-option-id', option.option_id)
  59  |     await expect(options.nth(index).getByRole('heading')).toHaveText(option.display_name)
  60  |   }
  61  |   const stored = inspectDatabase()
  62  |   expect(stored.counts).toEqual({ search_request: 1, request_alternative: 2, request_alternative_evidence: 2 })
  63  |   expect(stored.rows[0].projection).toEqual(saved)
  64  |   await expect(page.getByRole('status')).not.toBeVisible()
  65  |   await page.reload()
  66  |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  67  |   expect(inspectDatabase().rows[0].id).toBe(saved.persistence.request_id)
  68  | })
  69  | 
  70  | test('explicit locality confirmation saves reference-unverified intent without unsupported coverage', async ({ page }, testInfo) => {
  71  |   const rawTown = '  Synthetic optional town  '
  72  |   const rawPostcode = ' 0123 '
  73  |   const before = inspectDatabase()
  74  |   expect(before.counts.search_request > 0).toBe(true)
  75  |   const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  76  |   const attempts: ReturnType<typeof captureAttempt>[] = []
  77  |   page.on('request', request => {
  78  |     if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
  79  |   })
  80  |   await page.goto('/')
  81  |   await page.getByLabel('Describe your request').fill(example)
  82  |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  83  |   await page.getByLabel('Town (optional)', { exact: true }).fill(rawTown)
  84  |   await page.getByLabel('Postcode (optional)', { exact: true }).fill(rawPostcode)
  85  |   const clarificationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  86  |     && response.request().method() === 'POST')
  87  |   await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  88  |   const clarification = await clarificationResponse
  89  |   expect(clarification.status()).toBe(200)
  90  |   const clarificationBody = await clarification.json()
  91  |   expect(clarificationBody.outcome).toBe('clarification_required')
  92  |   expect(clarificationBody.persistence).toEqual({ state: 'not_attempted' })
  93  |   expect(clarificationBody.issues).toEqual([{ code: 'locality_reference_unavailable' }])
  94  |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('cannot currently be verified')
> 95  |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('Confirmation establishes intended scope only.')
      |                                                                                  ^ Error: expect(locator).toContainText(expected) failed
  96  |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability')
  97  |   const confirm = page.getByRole('button', { name: 'Confirm entered locality as intended scope', exact: true })
  98  |   await expect(confirm).toBeEnabled()
  99  |   await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
  100 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  101 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  102 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(rawTown)
  103 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(rawPostcode)
  104 |   await expect(page.getByRole('status')).not.toBeVisible()
  105 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  106 |   for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
  107 |     await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  108 |   }
  109 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  110 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  111 |   expect(attempts.length).toBe(1)
  112 |   const afterClarification = inspectDatabase()
  113 |   expect(afterClarification).toEqual(before)
  114 |   const confirmationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  115 |     && response.request().method() === 'POST')
  116 |   await confirm.click()
  117 |   const response = await confirmationResponse
  118 |   expect(response.status()).toBe(201)
  119 |   const saved = await response.json()
  120 |   expect(saved.outcome).toBe('insufficient_coverage')
  121 |   expect(saved.persistence.state).toBe('saved')
  122 |   expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  123 |   expect(saved.coverage.limitation_codes).toContain('geographic_applicability_unverified')
  124 |   const expectedScope = { country_code: 'CH', town: rawTown, postcode: rawPostcode,
  125 |     locality: { confirmation: 'user_confirmed', verification: 'reference_unverified',
  126 |       normalized: { town: 'synthetic optional town', postcode: '0123' } } }
  127 |   expect(saved.search_scope).toEqual(expectedScope)
  128 |   expect(attempts.length).toBe(2)
  129 |   const initial = JSON.parse(attempts[0].body)
  130 |   const confirmed = JSON.parse(attempts[1].body)
  131 |   expect(initial.location_choice === 'provided' && confirmed.location_choice === 'confirmed_unverified').toBe(true)
  132 |   expect(initial.submission_key !== confirmed.submission_key).toBe(true)
  133 |   expect(attempts[0].proofDigest !== attempts[1].proofDigest).toBe(true)
  134 |   expect(confirmed.text === initial.text && confirmed.text === example).toBe(true)
  135 |   expect(JSON.stringify(confirmed.search_location) === JSON.stringify(initial.search_location)).toBe(true)
  136 |   expect(JSON.stringify(confirmed.search_location) === JSON.stringify({ country_code: 'CH', town: rawTown, postcode: rawPostcode })).toBe(true)
  137 |   expect(JSON.stringify(confirmed.language_context) === JSON.stringify(initial.language_context)).toBe(true)
  138 |   const after = inspectDatabase()
  139 |   expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
  140 |     request_alternative: before.counts.request_alternative,
  141 |     request_alternative_evidence: before.counts.request_alternative_evidence })
  142 |   const added = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  143 |   expect(added.length).toBe(1)
  144 |   expect(added[0].id).toBe(saved.persistence.request_id)
  145 |   expect(added[0].projection).toEqual(saved)
  146 |   expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  147 |   expect(after.snapshots).toEqual(before.snapshots)
  148 |   const stored = JSON.parse(execFileSync(python, ['-c', `
  149 | import json,sqlite3,sys
  150 | with sqlite3.connect(sys.argv[1]) as connection:
  151 |     row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  152 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
  153 |         'location_choice':row[3],'language_context':json.loads(row[4])}))
  154 | `, database, added[0].id], { encoding: 'utf8' }))
  155 |   expect(stored.original_text === example).toBe(true)
  156 |   expect(stored.location_choice).toBe('confirmed_unverified')
  157 |   expect(stored.search_location).toEqual(expectedScope)
  158 |   expect(JSON.stringify(stored.language_context) === JSON.stringify(initial.language_context)).toBe(true)
  159 |   expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement' && item.quote === 'without replacing it')).toBe(true)
  160 |   const constraintSpan = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint' && item.normalized === 'no_replacement')
  161 |   expect(constraintSpan.span.start === 18 && constraintSpan.span.end === 38 && constraintSpan.span.quote === 'without replacing it').toBe(true)
  162 |   expect(stored.interpretation.provenance.reference_versions.country.release).toBe('geonames-countryInfo-2026-10-23-v1')
  163 |   await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  164 |   await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  165 |   const scope = page.getByRole('region', { name: 'Confirmed intended locality', exact: true })
  166 |   await expect(scope).toContainText('User-confirmed intended locality; reference-unverified.')
  167 |   await expect(scope).toContainText('does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability')
  168 |   await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  169 |   await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
  170 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  171 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  172 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  173 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(rawTown)
  174 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(rawPostcode)
  175 |   await expect(page.getByRole('status')).not.toBeVisible()
  176 |   await expect(page.getByRole('alert')).not.toBeVisible()
  177 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  178 |   await page.getByLabel('Town (optional)', { exact: true }).fill('Changed synthetic town')
  179 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  180 |   await expect(scope).not.toBeVisible()
  181 |   await expect(confirm).not.toBeVisible()
  182 |   await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
  183 |   expect(attempts.length).toBe(2)
  184 |   expect(inspectDatabase()).toEqual(after)
  185 |   const evidencePath = testInfo.outputPath('confirmed-locality-evidence.json')
  186 |   writeFileSync(evidencePath, JSON.stringify({
  187 |     scope: 'One explicit O-1 locality-intent confirmation with real approved country reference and synthetic meaning/evidence.',
  188 |     expected_fixture_outcome: 'insufficient_coverage; ordinary in-CH support does not establish applicability for the entered locality',
  189 |     before, after_clarification: afterClarification, after,
  190 |     clarification_response: { status: clarification.status(), body: clarificationBody },
  191 |     confirmed_response: { status: response.status(), body: saved },
  192 |     saved_request_id: added[0].id, saved_scope: stored.search_location,
  193 |     country_reference: stored.interpretation.provenance.reference_versions.country,
  194 |     posts_after_clarification: 1, posts_after_explicit_confirmation: 2, posts_after_non_submitting_edit: attempts.length,
  195 |     no_saved_rows_before_explicit_confirmation: true,
```