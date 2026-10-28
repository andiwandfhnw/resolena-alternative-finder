# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> delivered unknown persistence error requires explicit same-submission recovery
- Location: ../tests/e2e/saved-comparison.spec.ts:163:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Test source

```ts
  65  |   await page.reload()
  66  |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  67  |   expect(inspectDatabase().rows[0].id).toBe(saved.persistence.request_id)
  68  | })
  69  | 
  70  | test('lost HTTP response after atomic commit requires explicit same-submission recovery', async ({ page }, testInfo) => {
  71  |   const before = inspectDatabase()
  72  |   const attempts: ReturnType<typeof captureAttempt>[] = []
  73  |   let releaseLoss!: () => void
  74  |   const lossGate = new Promise<void>(resolve => { releaseLoss = resolve })
  75  |   let capture!: (value: { body: any; stored: ReturnType<typeof inspectDatabase> }) => void
  76  |   const committed = new Promise<{ body: any; stored: ReturnType<typeof inspectDatabase> }>(resolve => { capture = resolve })
  77  |   await page.route('**/api/comparisons', async route => {
  78  |     attempts.push(captureAttempt(route.request()))
  79  |     if (attempts.length === 1) {
  80  |       const response = await route.fetch({ maxRetries: 0 })
  81  |       expect(response.status()).toBe(201)
  82  |       capture({ body: await response.json(), stored: inspectDatabase() })
  83  |       await lossGate
  84  |       await route.abort('failed')
  85  |     } else {
  86  |       await route.continue()
  87  |     }
  88  |   })
  89  |   try {
  90  |     await page.goto('/')
  91  |     await page.getByLabel('Describe your request').fill(example)
  92  |     await page.getByRole('button', { name: 'Find alternatives' }).click()
  93  |     const { body: saved, stored } = await committed
  94  |     expect(stored.counts).toEqual({
  95  |       search_request: before.counts.search_request + 1,
  96  |       request_alternative: before.counts.request_alternative + 2,
  97  |       request_alternative_evidence: before.counts.request_alternative_evidence + 2,
  98  |     })
  99  |     expect(stored.rows.at(-1).projection).toEqual(saved)
  100 |     await expect(page.getByRole('status')).toBeVisible()
  101 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  102 |     releaseLoss()
  103 |     await expect(page.getByRole('alert')).toContainText('Delivery status is unknown')
  104 |     await expect(page.getByRole('alert')).not.toContainText('could not be saved')
  105 |     await expect(page.getByRole('status')).not.toBeVisible()
  106 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  107 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  108 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  109 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  110 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  111 |     await expect(page.getByRole('button', { name: 'Recover submission' })).toBeEnabled()
  112 |     await expect(page.getByRole('button', { name: 'Start a fresh search' })).toBeEnabled()
  113 |     await page.waitForTimeout(300)
  114 |     expect(attempts).toHaveLength(1)
  115 |     expect(inspectDatabase()).toEqual(stored)
  116 | 
  117 |     const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  118 |     await page.getByRole('button', { name: 'Recover submission' }).click()
  119 |     const response = await responsePromise
  120 |     expect(response.status()).toBe(200)
  121 |     const acknowledgement = await response.json()
  122 |     expect(acknowledgement).toEqual({
  123 |       outcome: 'submission_recovered', persistence: saved.persistence,
  124 |       saved_outcome: saved.outcome, assessed_at: saved.assessed_at,
  125 |     })
  126 |     expect(attempts).toHaveLength(2)
  127 |     expect(attempts[1].body === attempts[0].body).toBe(true)
  128 |     expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
  129 |     const acknowledged = page.getByRole('region', { name: 'Saved submission acknowledged' })
  130 |     await expect(acknowledged).toContainText(saved.persistence.request_id)
  131 |     await expect(acknowledged).toContainText(`Original outcome: ${saved.outcome}`)
  132 |     await expect(acknowledged).toContainText(`Originally assessed at: ${saved.assessed_at}`)
  133 |     await expect(acknowledged).toContainText('does not replay a comparison or confirm present-day facts')
  134 |     await expect(page.getByRole('alert')).not.toBeVisible()
  135 |     await expect(page.getByRole('status')).not.toBeVisible()
  136 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  137 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  138 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  139 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  140 |     const after = inspectDatabase()
  141 |     expect(after).toEqual(stored)
  142 |     await page.getByRole('button', { name: 'Start a fresh search' }).click()
  143 |     await expect(page.getByRole('button', { name: 'Find alternatives' })).toBeEnabled()
  144 |     await expect(acknowledged).not.toBeVisible()
  145 |     await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
  146 |     await page.waitForTimeout(300)
  147 |     expect(attempts).toHaveLength(2)
  148 |     expect(inspectDatabase()).toEqual(after)
  149 |     const evidencePath = testInfo.outputPath('committed-recovery-evidence.json')
  150 |     writeFileSync(evidencePath, JSON.stringify({ before_counts: before.counts, committed: stored, recovered: after,
  151 |         acknowledgement, requests: attempts.length, same_key_payload_and_proof: true,
  152 |         fault: 'Real API 201 verified in SQLite, then browser delivery aborted before presentation',
  153 |         no_automatic_retry_observed_ms: 300, fresh_action_sends_request: false }, null, 2))
  154 |     await testInfo.attach('committed-recovery-evidence', {
  155 |       path: evidencePath,
  156 |       contentType: 'application/json',
  157 |     })
  158 |   } finally {
  159 |     releaseLoss()
  160 |   }
  161 | })
  162 | 
  163 | test('delivered unknown persistence error requires explicit same-submission recovery', async ({ page }, testInfo) => {
  164 |   const controlFile = process.env.RESOLENA_TEST_UNCERTAIN_SAVE_FILE!
> 165 |   expect(Boolean(controlFile)).toBe(true)
      |                                ^ Error: expect(received).toBe(expected) // Object.is equality
  166 |   const faultEvidenceFile = controlFile.replace(/\.json$/, '.evidence.json')
  167 |   const before = inspectDatabase()
  168 |   expect(before.counts).toEqual({ search_request: 0, request_alternative: 0, request_alternative_evidence: 0 })
  169 |   const attempts: ReturnType<typeof captureAttempt>[] = []
  170 |   let releaseError!: () => void
  171 |   const errorGate = new Promise<void>(resolve => { releaseError = resolve })
  172 |   type Capture = { status: number; body: any; stored: ReturnType<typeof inspectDatabase> }
  173 |   let captureError!: (value: Capture) => void
  174 |   const backendError = new Promise<Capture>(resolve => { captureError = resolve })
  175 |   await page.route('**/api/comparisons', async route => {
  176 |     attempts.push(captureAttempt(route.request()))
  177 |     if (attempts.length === 1) {
  178 |       const key = JSON.parse(attempts[0].body).submission_key
  179 |       writeFileSync(controlFile, JSON.stringify({ submission_key_digest: createHash('sha256').update(JSON.stringify(key)).digest('hex') }))
  180 |       const response = await route.fetch({ maxRetries: 0 })
  181 |       captureError({ status: response.status(), body: await response.json(), stored: inspectDatabase() })
  182 |       await errorGate
  183 |       await route.fulfill({ response })
  184 |     } else {
  185 |       await route.continue()
  186 |     }
  187 |   })
  188 |   try {
  189 |     await page.goto('/')
  190 |     await page.getByLabel('Describe your request').fill(example)
  191 |     await page.getByRole('button', { name: 'Find alternatives' }).click()
  192 |     const delivered = await backendError
  193 |     expect(delivered.status).toBe(503)
  194 |     expect(delivered.body).toEqual({ outcome: 'persistence_error', persistence: { state: 'unknown' },
  195 |       issues: [{ code: 'comparison_save_failed' }], assessed_outcome: 'comparison' })
  196 |     const stored = delivered.stored
  197 |     expect(stored.counts).toEqual({ search_request: 1, request_alternative: 2, request_alternative_evidence: 2 })
  198 |     const saved = stored.rows[0].projection
  199 |     expect(saved.outcome).toBe('comparison')
  200 |     expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  201 |     expect(stored.rows[0].id).toBe(saved.persistence.request_id)
  202 |     expect(stored.snapshots.evidence).toEqual(before.snapshots.evidence)
  203 |     expect(existsSync(controlFile)).toBe(false)
  204 |     const fault = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
  205 |     expect(fault.fault_counts).toEqual({ real_commits: 1, confirmation_losses: 1, read_failures: 1 })
  206 |     expect(fault.independent_after_commit).toEqual(stored)
  207 |     expect(fault.after_fault).toEqual(stored)
  208 |     expect(fault.dialect_methods_restored).toBe(true)
  209 |     expect(fault.observer_rows_supplied_to_application).toBe(false)
  210 |     await expect(page.getByRole('status')).toBeVisible()
  211 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'true')
  212 |     await expect(page.getByRole('button', { name: 'Processing…' })).toBeDisabled()
  213 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  214 |     await expect(page.getByRole('alert')).not.toBeVisible()
  215 |     const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  216 |     releaseError()
  217 |     const errorResponse = await responsePromise
  218 |     expect(errorResponse.status()).toBe(delivered.status)
  219 |     expect(await errorResponse.json()).toEqual(delivered.body)
  220 |     await expect(page.getByRole('alert')).toContainText('Saving could not be confirmed')
  221 |     await expect(page.getByRole('alert')).toContainText('may already be saved')
  222 |     await expect(page.getByRole('alert')).not.toContainText('could not be saved')
  223 |     await expect(page.getByRole('status')).not.toBeVisible()
  224 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  225 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  226 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  227 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  228 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  229 |     await expect(page.getByText('Existing knowledge could not support', { exact: false })).not.toBeVisible()
  230 |     await expect(page.getByRole('button', { name: 'Recover submission' })).toBeEnabled()
  231 |     await expect(page.getByRole('button', { name: 'Start a fresh search' })).toBeEnabled()
  232 |     await page.waitForTimeout(300)
  233 |     expect(attempts.length).toBe(1)
  234 |     expect(inspectDatabase()).toEqual(stored)
  235 | 
  236 |     const recoveryResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  237 |     await page.getByRole('button', { name: 'Recover submission' }).click()
  238 |     const response = await recoveryResponse
  239 |     expect(response.status()).toBe(200)
  240 |     const acknowledgement = await response.json()
  241 |     expect(acknowledgement).toEqual({ outcome: 'submission_recovered', persistence: saved.persistence,
  242 |       saved_outcome: 'comparison', assessed_at: saved.assessed_at })
  243 |     expect(attempts.length).toBe(2)
  244 |     expect(attempts[1].body === attempts[0].body).toBe(true)
  245 |     expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
  246 |     const acknowledged = page.getByRole('region', { name: 'Saved submission acknowledged' })
  247 |     await expect(acknowledged).toContainText(saved.persistence.request_id)
  248 |     await expect(acknowledged).toContainText('Original outcome: comparison')
  249 |     await expect(acknowledged).toContainText(`Originally assessed at: ${saved.assessed_at}`)
  250 |     await expect(acknowledged).toContainText('does not replay a comparison or confirm present-day facts')
  251 |     await expect(page.getByRole('alert')).not.toBeVisible()
  252 |     await expect(page.getByRole('status')).not.toBeVisible()
  253 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  254 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  255 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  256 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  257 |     const after = inspectDatabase()
  258 |     expect(after).toEqual(stored)
  259 |     const evidencePath = testInfo.outputPath('delivered-unknown-recovery-evidence.json')
  260 |     writeFileSync(evidencePath, JSON.stringify({ before, committed: stored, recovered: after, fault,
  261 |       error_response: { status: errorResponse.status(), body: delivered.body },
  262 |       recovery_response: { status: response.status(), body: acknowledgement },
  263 |       browser_submissions: attempts.length, same_serialized_body_key_and_proof: true,
  264 |       loading_held_until_actual_error_delivered: true, fields_preserved_after_error_and_recovery: true,
  265 |       no_comparison_or_coverage_presented: true, no_automatic_retry_observed_ms: 300,
```