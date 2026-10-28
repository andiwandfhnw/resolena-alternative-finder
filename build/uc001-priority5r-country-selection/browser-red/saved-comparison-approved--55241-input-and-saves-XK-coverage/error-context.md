# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> approved country selector preserves cleared input and saves XK coverage
- Location: ../tests/e2e/saved-comparison.spec.ts:70:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
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
  70  | test('approved country selector preserves cleared input and saves XK coverage', async ({ page }, testInfo) => {
  71  |   const before = inspectDatabase()
> 72  |   expect(before.counts.search_request > 0).toBe(true)
      |                                            ^ Error: expect(received).toBe(expected) // Object.is equality
  73  |   const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  74  |   const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  75  |   const catalogueResponse = await page.request.get('/api/countries')
  76  |   expect(catalogueResponse.status()).toBe(200)
  77  |   const catalogue = await catalogueResponse.json()
  78  |   expect(typeof catalogue.version === 'string' && catalogue.version.length > 0).toBe(true)
  79  |   expect(catalogue.countries.length).toBe(250)
  80  |   expect(catalogue.countries.some((entry: { code: string }) => entry.code === 'XK')).toBe(true)
  81  |   expect(catalogue.countries.some((entry: { code: string }) => entry.code === 'AN' || entry.code === 'CS')).toBe(false)
  82  |   let submissions = 0
  83  |   page.on('request', request => {
  84  |     if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') submissions += 1
  85  |   })
  86  |   await page.goto('/')
  87  |   const country = page.getByRole('combobox', { name: 'Search country', exact: true })
  88  |   await expect(country).toBeEnabled()
  89  |   await expect(country).toHaveValue('CH')
  90  |   await expect(country.locator('option')).toHaveCount(251)
  91  |   const visibleCountries = await country.locator('option').evaluateAll(options => options
  92  |     .map(option => ({ code: (option as HTMLOptionElement).value, label: option.textContent || '' }))
  93  |     .filter(option => option.code !== '')
  94  |     .map(option => ({ code: option.code, name: option.label.slice(`${option.code} — `.length) })))
  95  |   expect(visibleCountries).toEqual(catalogue.countries)
  96  |   await expect(country.locator('option:checked')).toHaveText('CH — Switzerland')
  97  |   await expect(page.getByRole('link', { name: 'GeoNames', exact: true })).toHaveAttribute('href', catalogue.attribution.source_link)
  98  |   await expect(page.getByRole('link', { name: catalogue.attribution.license, exact: true })).toHaveAttribute('href', catalogue.attribution.license_link)
  99  |   await expect(page.getByText('Approved country reference; interpretation and alternative evidence remain synthetic.', { exact: true })).toBeVisible()
  100 |   await page.getByLabel('Describe your request').fill(example)
  101 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
  102 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
  103 |   await country.selectOption('')
  104 |   await expect(country).toHaveValue('')
  105 |   expect(submissions).toBe(0)
  106 |   await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  107 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  108 |   const emptyValidation = await country.evaluate(element => {
  109 |     const select = element as HTMLSelectElement
  110 |     return { value: select.value, valid: select.validity.valid, value_missing: select.validity.valueMissing,
  111 |       message_present: select.validationMessage.length > 0 }
  112 |   })
  113 |   expect(emptyValidation).toEqual({ value: '', valid: false, value_missing: true, message_present: true })
  114 |   expect(submissions).toBe(0)
  115 |   await expect(country).toHaveValue('')
  116 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  117 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
  118 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
  119 |   await expect(page.getByRole('status')).not.toBeVisible()
  120 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  121 |   for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
  122 |     await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  123 |   }
  124 |   const afterEmpty = inspectDatabase()
  125 |   expect(afterEmpty).toEqual(before)
  126 |   await country.selectOption('XK')
  127 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  128 |   await expect(country).toHaveValue('XK')
  129 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  130 |   expect(submissions).toBe(0)
  131 |   expect(inspectDatabase()).toEqual(before)
  132 |   const pending = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  133 |     && response.request().method() === 'POST')
  134 |   await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  135 |   const response = await pending
  136 |   expect(response.status()).toBe(201)
  137 |   const saved = await response.json()
  138 |   expect(saved.outcome).toBe('insufficient_coverage')
  139 |   expect(saved.persistence.state).toBe('saved')
  140 |   expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  141 |   expect(submissions).toBe(1)
  142 |   await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  143 |   await expect(page.getByText('Research is unavailable in this increment; alternatives may exist.', { exact: false })).toBeVisible()
  144 |   await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  145 |   await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
  146 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  147 |   await expect(page.getByRole('alert')).not.toBeVisible()
  148 |   await expect(page.getByRole('status')).not.toBeVisible()
  149 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  150 |   await expect(country).toHaveValue('XK')
  151 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  152 |   const after = inspectDatabase()
  153 |   expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
  154 |     request_alternative: before.counts.request_alternative,
  155 |     request_alternative_evidence: before.counts.request_alternative_evidence })
  156 |   const added = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  157 |   expect(added.length).toBe(1)
  158 |   expect(added[0].id).toBe(saved.persistence.request_id)
  159 |   expect(added[0].projection).toEqual(saved)
  160 |   await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  161 |   expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  162 |   expect(after.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
  163 |     .toEqual(before.snapshots.request_alternative)
  164 |   expect(after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
  165 |     .toEqual(before.snapshots.request_alternative_evidence)
  166 |   expect(after.snapshots.evidence).toEqual(before.snapshots.evidence)
  167 |   const stored = JSON.parse(execFileSync(python, ['-c', `
  168 | import json,sqlite3,sys
  169 | with sqlite3.connect(sys.argv[1]) as connection:
  170 |     row=connection.execute('SELECT original_text,interpretation,search_location,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  171 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),
  172 |         'search_location':json.loads(row[2]),'language_context':json.loads(row[3])}))
```