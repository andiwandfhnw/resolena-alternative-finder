# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> unavailable locality requires explicit country-only continuation before saving
- Location: ../tests/e2e/saved-comparison.spec.ts:290:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByLabel('Town (optional)', { exact: true })
Expected: visible
Timeout: 3000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByLabel('Town (optional)', { exact: true }) with timeout 3000ms
  - waiting for getByLabel('Town (optional)', { exact: true })

```

```yaml
- main:
  - paragraph: Resolena Alternative Finder
  - heading "Explore practical alternatives" [level=1]
  - complementary:
    - strong: Synthetic demonstration
    - paragraph: Test-only interpreter and evidence. No real providers, multilingual support or verified savings.
    - paragraph: Use “Repair my bicycle without replacing it” with CH for a comparison or DE for a synthetic coverage limitation.
    - paragraph: “Velo” exercises explanation-language preferences. Only English synthetic rendering is configured.
    - paragraph: “Synthetic hourly bicycle repair” exercises source-bound test wording in DE/FR/IT/EN. “Synthetic pending bicycle repair” exercises a missing-review limitation. These fixtures do not verify linguistic fidelity.
  - text: Describe your request
  - textbox "Describe your request": Repair my bicycle without replacing it
  - text: Search country
  - textbox "Search country": CH
  - paragraph: CH — Switzerland is the editable default, not a detected location.
  - button "Find alternatives"
```

# Test source

```ts
  212 |       .toEqual(before.snapshots.request_alternative_evidence)
  213 |     expect(saved.outcome).toBe('comparison')
  214 |     expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  215 |     expect(addedRequest.id).toBe(saved.persistence.request_id)
  216 |     expect(stored.snapshots.evidence).toEqual(before.snapshots.evidence)
  217 |     expect(existsSync(controlFile)).toBe(false)
  218 |     const fault = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
  219 |     expect(fault.fault_counts).toEqual({ real_commits: 1, confirmation_losses: 1, read_failures: 1 })
  220 |     expect(fault.independent_after_commit).toEqual(stored)
  221 |     expect(fault.after_fault).toEqual(stored)
  222 |     expect(fault.dialect_methods_restored).toBe(true)
  223 |     expect(fault.observer_rows_supplied_to_application).toBe(false)
  224 |     await expect(page.getByRole('status')).toBeVisible()
  225 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'true')
  226 |     await expect(page.getByRole('button', { name: 'Processing…' })).toBeDisabled()
  227 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  228 |     await expect(page.getByRole('alert')).not.toBeVisible()
  229 |     const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  230 |     releaseError()
  231 |     const errorResponse = await responsePromise
  232 |     expect(errorResponse.status()).toBe(delivered.status)
  233 |     expect(await errorResponse.json()).toEqual(delivered.body)
  234 |     await expect(page.getByRole('alert')).toContainText('Saving could not be confirmed')
  235 |     await expect(page.getByRole('alert')).toContainText('may already be saved')
  236 |     await expect(page.getByRole('alert')).not.toContainText('could not be saved')
  237 |     await expect(page.getByRole('status')).not.toBeVisible()
  238 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  239 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  240 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  241 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  242 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  243 |     await expect(page.getByText('Existing knowledge could not support', { exact: false })).not.toBeVisible()
  244 |     await expect(page.getByRole('button', { name: 'Recover submission' })).toBeEnabled()
  245 |     await expect(page.getByRole('button', { name: 'Start a fresh search' })).toBeEnabled()
  246 |     await page.waitForTimeout(300)
  247 |     expect(attempts.length).toBe(1)
  248 |     expect(inspectDatabase()).toEqual(stored)
  249 | 
  250 |     const recoveryResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  251 |     await page.getByRole('button', { name: 'Recover submission' }).click()
  252 |     const response = await recoveryResponse
  253 |     expect(response.status()).toBe(200)
  254 |     const acknowledgement = await response.json()
  255 |     expect(acknowledgement).toEqual({ outcome: 'submission_recovered', persistence: saved.persistence,
  256 |       saved_outcome: 'comparison', assessed_at: saved.assessed_at })
  257 |     expect(attempts.length).toBe(2)
  258 |     expect(attempts[1].body === attempts[0].body).toBe(true)
  259 |     expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
  260 |     const acknowledged = page.getByRole('region', { name: 'Saved submission acknowledged' })
  261 |     await expect(acknowledged).toContainText(saved.persistence.request_id)
  262 |     await expect(acknowledged).toContainText('Original outcome: comparison')
  263 |     await expect(acknowledged).toContainText(`Originally assessed at: ${saved.assessed_at}`)
  264 |     await expect(acknowledged).toContainText('does not replay a comparison or confirm present-day facts')
  265 |     await expect(page.getByRole('alert')).not.toBeVisible()
  266 |     await expect(page.getByRole('status')).not.toBeVisible()
  267 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  268 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  269 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  270 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  271 |     const after = inspectDatabase()
  272 |     expect(after).toEqual(stored)
  273 |     const evidencePath = testInfo.outputPath('delivered-unknown-recovery-evidence.json')
  274 |     writeFileSync(evidencePath, JSON.stringify({ before, committed: stored, recovered: after, fault,
  275 |       added_request_id: addedRequest.id, new_identity_selected_by_baseline_difference: true,
  276 |       preexisting_records_and_source_evidence_preserved: true,
  277 |       runner_control: { path: controlFile, initially_absent: true, consumed_after_error: true },
  278 |       error_response: { status: errorResponse.status(), body: delivered.body },
  279 |       recovery_response: { status: response.status(), body: acknowledgement },
  280 |       browser_submissions: attempts.length, same_serialized_body_key_and_proof: true,
  281 |       loading_held_until_actual_error_delivered: true, fields_preserved_after_error_and_recovery: true,
  282 |       no_comparison_or_coverage_presented: true, no_automatic_retry_observed_ms: 300,
  283 |       fresh_search_action_unchanged_and_not_exercised: true, raw_originating_proofs_recorded: false }, null, 2))
  284 |     await testInfo.attach('delivered-unknown-recovery-evidence', { path: evidencePath, contentType: 'application/json' })
  285 |   } finally {
  286 |     releaseError()
  287 |   }
  288 | })
  289 | 
  290 | test('unavailable locality requires explicit country-only continuation before saving', async ({ page }, testInfo) => {
  291 |   const before = inspectDatabase()
  292 |   const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  293 |   const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  294 |   const attempts: ReturnType<typeof captureAttempt>[] = []
  295 |   let releaseSaved!: () => void
  296 |   const savedGate = new Promise<void>(resolve => { releaseSaved = resolve })
  297 |   type Capture = { status: number; body: any; stored: ReturnType<typeof inspectDatabase> }
  298 |   let captureSaved!: (value: Capture) => void
  299 |   const committed = new Promise<Capture>(resolve => { captureSaved = resolve })
  300 |   await page.route('**/api/comparisons', async route => {
  301 |     attempts.push(captureAttempt(route.request()))
  302 |     const response = await route.fetch({ maxRetries: 0 })
  303 |     if (attempts.length === 2) {
  304 |       captureSaved({ status: response.status(), body: await response.json(), stored: inspectDatabase() })
  305 |       await savedGate
  306 |     }
  307 |     await route.fulfill({ response })
  308 |   })
  309 |   try {
  310 |     await page.goto('/')
  311 |     await page.getByLabel('Describe your request').fill(example)
> 312 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toBeVisible({ timeout: 3000 })
      |                                                                       ^ Error: expect(locator).toBeVisible() failed
  313 |     await page.getByLabel('Town (optional)', { exact: true }).fill('Synthetic optional town')
  314 |     await page.getByLabel('Postcode (optional)', { exact: true }).fill('0123')
  315 |     const clarificationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  316 |     await page.getByRole('button', { name: 'Find alternatives' }).click()
  317 |     const clarification = await clarificationResponse
  318 |     expect(clarification.status()).toBe(200)
  319 |     const clarificationBody = await clarification.json()
  320 |     expect(clarificationBody.outcome).toBe('clarification_required')
  321 |     expect(clarificationBody.persistence).toEqual({ state: 'not_attempted' })
  322 |     expect(clarificationBody.issues).toEqual([{ code: 'locality_reference_unavailable' }])
  323 |     await expect(page.getByRole('region', { name: 'Clarification' })).toContainText('cannot currently be verified')
  324 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  325 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  326 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('Synthetic optional town')
  327 |     await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('0123')
  328 |     await expect(page.getByRole('status')).not.toBeVisible()
  329 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  330 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  331 |     await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).not.toBeVisible()
  332 |     await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
  333 |     expect(inspectDatabase()).toEqual(before)
  334 |     await page.waitForTimeout(300)
  335 |     expect(attempts.length).toBe(1)
  336 |     expect(inspectDatabase()).toEqual(before)
  337 | 
  338 |     const savedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  339 |     await page.getByRole('button', { name: 'Continue with country only', exact: true }).click()
  340 |     const saved = await committed
  341 |     expect(saved.status).toBe(201)
  342 |     expect(saved.body.outcome).toBe('comparison')
  343 |     expect(saved.stored.counts).toEqual({
  344 |       search_request: before.counts.search_request + 1,
  345 |       request_alternative: before.counts.request_alternative + 2,
  346 |       request_alternative_evidence: before.counts.request_alternative_evidence + 2,
  347 |     })
  348 |     const addedRequests = saved.stored.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  349 |     expect(addedRequests.length).toBe(1)
  350 |     const addedRequest = addedRequests[0]
  351 |     expect(addedRequest.id).toBe(saved.body.persistence.request_id)
  352 |     expect(addedRequest.projection).toEqual(saved.body)
  353 |     expect(saved.stored.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  354 |     expect(saved.stored.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
  355 |       .toEqual(before.snapshots.request_alternative)
  356 |     expect(saved.stored.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
  357 |       .toEqual(before.snapshots.request_alternative_evidence)
  358 |     expect(saved.stored.snapshots.evidence).toEqual(before.snapshots.evidence)
  359 |     expect(attempts.length).toBe(2)
  360 |     const original = JSON.parse(attempts[0].body)
  361 |     const continuation = JSON.parse(attempts[1].body)
  362 |     expect(original.search_location).toEqual({ country_code: 'CH', town: 'Synthetic optional town', postcode: '0123' })
  363 |     expect(original.location_choice).toBe('provided')
  364 |     expect(continuation.search_location).toEqual({ country_code: 'CH' })
  365 |     expect(continuation.location_choice).toBe('country_only')
  366 |     expect(continuation.text === original.text && continuation.text === example).toBe(true)
  367 |     expect(continuation.language_context).toEqual(original.language_context)
  368 |     expect(continuation.submission_key !== original.submission_key).toBe(true)
  369 |     expect(attempts[1].proofDigest !== attempts[0].proofDigest).toBe(true)
  370 |     const storedRequest = JSON.parse(execFileSync(python, ['-c', `
  371 | import json,sqlite3,sys
  372 | with sqlite3.connect(sys.argv[1]) as connection:
  373 |     row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context,assessed_at,outcome FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  374 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
  375 |         'location_choice':row[3],'language_context':json.loads(row[4]),'assessed_at':row[5],'outcome':row[6]}))
  376 | `, database, addedRequest.id], { encoding: 'utf8' }))
  377 |     expect(storedRequest.original_text).toBe(example)
  378 |     expect(storedRequest.search_location).toEqual({ country_code: 'CH' })
  379 |     expect(storedRequest.location_choice).toBe('country_only')
  380 |     expect(storedRequest.language_context).toEqual(original.language_context)
  381 |     expect(storedRequest.interpretation.constraints).toEqual([{ value: 'no_replacement', quote: 'without replacing it' }])
  382 |     expect(storedRequest.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  383 |     await expect(page.getByRole('status')).toBeVisible()
  384 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  385 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  386 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
  387 |     await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
  388 |     await expect(page.getByText('Search scope: country only (CH).', { exact: true })).toBeVisible()
  389 |     releaseSaved()
  390 |     const delivered = await savedResponse
  391 |     expect(delivered.status()).toBe(201)
  392 |     expect(await delivered.json()).toEqual(saved.body)
  393 |     await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
  394 |     await expect(page.getByTestId('saved-option')).toHaveCount(2)
  395 |     await expect(page.getByRole('status')).not.toBeVisible()
  396 |     await expect(page.getByRole('alert')).not.toBeVisible()
  397 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  398 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  399 |     expect(inspectDatabase()).toEqual(saved.stored)
  400 |     const evidencePath = testInfo.outputPath('country-only-continuation-evidence.json')
  401 |     writeFileSync(evidencePath, JSON.stringify({ before, clarification_response: { status: clarification.status(), body: clarificationBody },
  402 |       clarification_saved_no_search: true, fields_retained_until_explicit_choice: true, bounded_no_automatic_continuation_ms: 300,
  403 |       committed: saved.stored, saved_request_id: addedRequest.id, saved_request: storedRequest,
  404 |       saved_response: { status: delivered.status(), body: saved.body }, browser_submissions: attempts.length,
  405 |       explicit_choice_uses_new_key_and_proof: true, original_text_country_language_preserved: true,
  406 |       prior_records_and_source_evidence_preserved: true, saved_before_presentation: true,
  407 |       delayed_save_t12_exercised: false, raw_originating_proofs_recorded: false }, null, 2))
  408 |     await testInfo.attach('country-only-continuation-evidence', { path: evidencePath, contentType: 'application/json' })
  409 |   } finally {
  410 |     releaseSaved()
  411 |   }
  412 | })
```