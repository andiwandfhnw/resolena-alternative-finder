import { expect, test, type Request } from '../../frontend/node_modules/@playwright/test/index.js'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs'
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

test.beforeEach(({}, testInfo) => {
  const controlFile = process.env.RESOLENA_TEST_LOCALITY_REFERENCE_FILE!
  expect(Boolean(controlFile)).toBe(true)
  rmSync(controlFile, { force: true })
  if (['explicit locality confirmation saves reference-unverified intent without unsupported coverage',
    'unavailable locality requires explicit country-only continuation before saving'].includes(testInfo.title)) {
    writeFileSync(controlFile, JSON.stringify({ unavailable: true }))
  }
})

test.afterEach(() => {
  const controlFile = process.env.RESOLENA_TEST_LOCALITY_REFERENCE_FILE
  if (controlFile) rmSync(controlFile, { force: true })
})

test('browser displays exactly the committed API comparison and stable database identities', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Development demonstration', { exact: true })).toBeVisible()
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

test('malformed CH postcode requires correction before explicit saved assessment', async ({ page }, testInfo) => {
  const town = 'Jouxtens-Mézery'
  const before = inspectDatabase()
  expect(before.counts.search_request > 0).toBe(true)
  const priorIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const attempts: ReturnType<typeof captureAttempt>[] = []
  page.on('request', request => {
    if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
  })
  await page.goto('/')
  await page.getByLabel('Describe your request').fill(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await page.getByLabel('Town (optional)', { exact: true }).fill(town)
  await page.getByLabel('Postcode (optional)', { exact: true }).fill('10A8')
  const invalidResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
    && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  const invalid = await invalidResponse
  expect(invalid.status()).toBe(422)
  const invalidBody = await invalid.json()
  expect(invalidBody.outcome).toBe('invalid_input')
  expect(invalidBody.persistence).toEqual({ state: 'not_attempted' })
  expect(invalidBody.issues).toEqual([{ code: 'postcode_format_invalid' }])
  await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText(/four-digit postcode/i)
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(town)
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('10A8')
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
    await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
  }
  for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
    await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  }
  await expect(page.getByTestId('saved-option')).toHaveCount(0)
  expect(attempts.length).toBe(1)
  const afterInvalid = inspectDatabase()
  expect(afterInvalid).toEqual(before)
  await page.getByLabel('Postcode (optional)', { exact: true }).fill('1008')
  await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  await expect(page.getByRole('region', { name: 'Clarification', exact: true })).not.toBeVisible()
  await expect(page.getByRole('alert')).not.toBeVisible()
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(town)
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('1008')
  expect(attempts.length).toBe(1)
  const afterCorrection = inspectDatabase()
  expect(afterCorrection).toEqual(before)
  const savedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
    && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  const response = await savedResponse
  expect(response.status()).toBe(201)
  const saved = await response.json()
  expect(saved.outcome).toBe('insufficient_coverage')
  expect(saved.persistence.state).toBe('saved')
  expect(saved.coverage.limitation_codes).toContain('geographic_applicability_unverified')
  const expectedScope = { country_code: 'CH', town, postcode: '1008', locality: {
    verification: 'matched_in_reference', selection: 'single_match', normalized: { town: 'jouxtens-mézery', postcode: '1008' },
    association: { reference: { source: 'swisstopo', release: 'swisstopo-chli-associations-2026-10-01-v1', source_record: 10 },
      country_code: 'CH', locality_name: town, postcode: '1008', source_postcode_id: '5852', additional_number: '02',
      administrative: { municipality_name: town, municipality_id: '5585', canton: 'VD' } } } }
  expect(saved.search_scope).toEqual(expectedScope)
  expect(attempts.length).toBe(2)
  const initial = JSON.parse(attempts[0].body)
  const corrected = JSON.parse(attempts[1].body)
  expect(initial.submission_key !== corrected.submission_key).toBe(true)
  expect(attempts[0].proofDigest !== attempts[1].proofDigest).toBe(true)
  expect(initial.text === corrected.text && corrected.text === example).toBe(true)
  expect(initial.search_location.country_code === corrected.search_location.country_code
    && corrected.search_location.country_code === 'CH' && initial.search_location.town === corrected.search_location.town
    && corrected.search_location.town === town).toBe(true)
  expect(initial.search_location.postcode === '10A8' && corrected.search_location.postcode === '1008').toBe(true)
  expect(initial.location_choice === 'provided' && corrected.location_choice === 'provided').toBe(true)
  expect(JSON.stringify(initial.language_context) === JSON.stringify(corrected.language_context)).toBe(true)
  const after = inspectDatabase()
  expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
    request_alternative: before.counts.request_alternative,
    request_alternative_evidence: before.counts.request_alternative_evidence })
  const added = after.rows.filter((row: { id: string }) => !priorIds.has(row.id))
  expect(added.length).toBe(1)
  expect(added[0].id).toBe(saved.persistence.request_id)
  expect(added[0].projection).toEqual(saved)
  expect(after.rows.filter((row: { id: string }) => priorIds.has(row.id))).toEqual(before.rows)
  expect(after.snapshots).toEqual(before.snapshots)
  const stored = JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
        'language_context':json.loads(row[3])}))
`, database, added[0].id], { encoding: 'utf8' }))
  expect(stored.original_text === example).toBe(true)
  expect(stored.search_location).toEqual(expectedScope)
  expect(JSON.stringify(stored.language_context) === JSON.stringify(corrected.language_context)).toBe(true)
  expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement'
    && item.quote === 'without replacing it')).toBe(true)
  const span = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint'
    && item.normalized === 'no_replacement').span
  expect(span.start === 18 && span.end === 38 && span.quote === 'without replacing it').toBe(true)
  const localityReference = stored.interpretation.provenance.reference_versions.locality
  expect(localityReference.release).toBe('swisstopo-chli-associations-2026-10-01-v1')
  expect(localityReference.sha256).toBe('eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9')
  await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  const shownScope = page.getByRole('region', { name: 'Matched reference association', exact: true })
  await expect(shownScope).toContainText('Matched in this reference; delivery and service coverage are not established.')
  await expect(shownScope).toContainText(town)
  await expect(shownScope).toContainText('1008/02')
  await expect(shownScope).toContainText('association record: 10')
  await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  await expect(page.getByRole('alert')).not.toBeVisible()
  await expect(page.getByRole('region', { name: 'Clarification', exact: true })).not.toBeVisible()
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(town)
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('1008')
  const evidencePath = testInfo.outputPath('postcode-correction-evidence.json')
  writeFileSync(evidencePath, JSON.stringify({
    scope: 'One declared malformed CH postcode corrected before explicit assessment; approved references with synthetic meaning/evidence.',
    before, after_invalid: afterInvalid, after_correction: afterCorrection, after,
    malformed_response: { status: invalid.status(), body: invalidBody }, corrected_response: { status: response.status(), body: saved },
    saved_request_id: added[0].id, matched_association: expectedScope.locality.association, locality_reference: localityReference,
    posts_after_invalid_input: 1, posts_after_correction_only: 1, posts_after_explicit_submission: attempts.length,
    malformed_post_reached_actual_API_without_native_validation_changes: true,
    no_saved_rows_for_invalid_input_or_editing_alone: true,
    correction_uses_new_key_and_proof_preserves_other_fields_language_and_requirement_span: true,
    validation_loading_and_saved_identity_scope_verified: true,
    prior_records_options_links_source_versions_and_review_dates_preserved: true,
    raw_keys_proofs_digests_headers_bindings_or_complete_captured_requests_recorded: false }, null, 2))
  await testInfo.attach('postcode-correction-evidence', { path: evidencePath, contentType: 'application/json' })
})

for (const fixture of [
  { selection: 'single_match', town: '  jouxtens-me\u0301zery  ', postcode: ' 1008 ', normalizedTown: 'jouxtens-mézery',
    association: { source_record: 10, locality_name: 'Jouxtens-Mézery', postcode: '1008', source_postcode_id: '5852',
      additional_number: '02', administrative: { municipality_name: 'Jouxtens-Mézery', municipality_id: '5585', canton: 'VD' } } },
  { selection: 'explicit', town: 'Lausanne', postcode: '1015', normalizedTown: 'lausanne',
    association: { source_record: 16, locality_name: 'Lausanne', postcode: '1015', source_postcode_id: '163',
      additional_number: '00', administrative: { municipality_name: 'Saint-Sulpice (VD)', municipality_id: '5648', canton: 'VD' } } },
] as const) {
  test(`pinned reference association ${fixture.selection} saves honest insufficient coverage`, async ({ page }, testInfo) => {
    const release = 'swisstopo-chli-associations-2026-10-01-v1'
    const { source_record: sourceRecord, ...associationFields } = fixture.association
    const expectedAssociation = { reference: { source: 'swisstopo', release, source_record: sourceRecord },
      country_code: 'CH', ...associationFields }
    const before = inspectDatabase()
    expect(before.counts.search_request > 0).toBe(true)
    const priorIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
    const attempts: ReturnType<typeof captureAttempt>[] = []
    page.on('request', request => {
      if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
    })
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await page.getByLabel('Town (optional)', { exact: true }).fill(fixture.town)
    await page.getByLabel('Postcode (optional)', { exact: true }).fill(fixture.postcode)
    const initialResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
    let response = await initialResponse
    let body = await response.json()
    let clarification: { status: number; body: unknown } | null = null
    let afterClarification = before
    if (fixture.selection === 'explicit') {
      expect(response.status()).toBe(200)
      expect(body.outcome).toBe('clarification_required')
      expect(body.persistence).toEqual({ state: 'not_attempted' })
      expect(body.issues).toEqual([{ code: 'locality_reference_ambiguous' }])
      expect(body.clarification.choices).toEqual([])
      const expectedChoices = [
        { record: 15, municipality: 'Ecublens (VD)', municipalityId: '5635' },
        { record: 16, municipality: 'Saint-Sulpice (VD)', municipalityId: '5648' },
        { record: 17, municipality: 'Chavannes-près-Renens', municipalityId: '5627' },
      ].map(choice => ({ reference: { source: 'swisstopo', release, source_record: choice.record },
        country_code: 'CH', locality_name: 'Lausanne', postcode: '1015', source_postcode_id: '163',
        additional_number: '00', administrative: { municipality_name: choice.municipality,
          municipality_id: choice.municipalityId, canton: 'VD' } }))
      expect(body.clarification.associations).toEqual(expectedChoices)
      const associations = page.getByRole('combobox', { name: 'Reference association', exact: true })
      await expect(associations.locator('option')).toHaveCount(4)
      expect(await associations.locator('option').evaluateAll(options => options.map(option => (option as HTMLOptionElement).value)))
        .toEqual(['', '15', '16', '17'])
      for (const choice of expectedChoices) {
        const shownChoice = associations.locator(`option[value="${choice.reference.source_record}"]`)
        await expect(shownChoice).toContainText(choice.locality_name)
        await expect(shownChoice).toContainText(choice.postcode)
        await expect(shownChoice).toContainText(choice.administrative.municipality_name)
        await expect(shownChoice).toContainText(choice.administrative.canton)
      }
      await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('associations')
      await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
      await expect(page.getByRole('button', { name: 'Confirm entered locality as intended scope', exact: true })).not.toBeVisible()
      await expect(page.getByLabel('Explanation language', { exact: true })).not.toBeVisible()
      await expect(page.getByRole('status')).not.toBeVisible()
      await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
      await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
      await expect(page.getByTestId('saved-option')).toHaveCount(0)
      expect(attempts.length).toBe(1)
      afterClarification = inspectDatabase()
      expect(afterClarification).toEqual(before)
      const continueSelection = page.getByRole('button', { name: 'Continue with selected association', exact: true })
      await expect(continueSelection).toBeDisabled()
      await associations.selectOption('16')
      await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
      await expect(continueSelection).toBeEnabled()
      expect(attempts.length).toBe(1)
      expect(inspectDatabase()).toEqual(before)
      await expect(page.getByLabel('Describe your request')).toHaveValue(example)
      await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(fixture.town)
      await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(fixture.postcode)
      clarification = { status: response.status(), body }
      const selectedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
        && response.request().method() === 'POST')
      await continueSelection.click()
      response = await selectedResponse
      body = await response.json()
    }
    expect(response.status()).toBe(201)
    expect(body.outcome).toBe('insufficient_coverage')
    expect(body.persistence.state).toBe('saved')
    expect(body.coverage.limitation_codes).toContain('geographic_applicability_unverified')
    const expectedScope = { country_code: 'CH', town: fixture.town, postcode: fixture.postcode,
      locality: { verification: 'matched_in_reference', selection: fixture.selection,
        normalized: { town: fixture.normalizedTown, postcode: fixture.postcode.trim() }, association: expectedAssociation } }
    expect(body.search_scope).toEqual(expectedScope)
    expect(attempts.length).toBe(fixture.selection === 'explicit' ? 2 : 1)
    const first = JSON.parse(attempts[0].body)
    const last = JSON.parse(attempts.at(-1)!.body)
    expect(first.location_choice === 'provided' && last.location_choice === 'provided').toBe(true)
    expect(!('reference' in first.search_location)).toBe(true)
    expect(last.text === first.text && last.text === example).toBe(true)
    expect(last.search_location.country_code === 'CH' && last.search_location.town === fixture.town
      && last.search_location.postcode === fixture.postcode).toBe(true)
    expect(JSON.stringify(last.language_context) === JSON.stringify(first.language_context)).toBe(true)
    if (fixture.selection === 'explicit') {
      expect(last.submission_key !== first.submission_key).toBe(true)
      expect(attempts.at(-1)!.proofDigest !== attempts[0].proofDigest).toBe(true)
      expect(JSON.stringify(last.search_location.reference) === JSON.stringify(expectedAssociation.reference)).toBe(true)
      expect(Object.keys(last.search_location.reference).sort()).toEqual(['release', 'source', 'source_record'])
    }
    const after = inspectDatabase()
    expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative,
      request_alternative_evidence: before.counts.request_alternative_evidence })
    const added = after.rows.filter((row: { id: string }) => !priorIds.has(row.id))
    expect(added.length).toBe(1)
    expect(added[0].id).toBe(body.persistence.request_id)
    expect(added[0].projection).toEqual(body)
    expect(after.rows.filter((row: { id: string }) => priorIds.has(row.id))).toEqual(before.rows)
    expect(after.snapshots).toEqual(before.snapshots)
    const stored = JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
        'location_choice':row[3],'language_context':json.loads(row[4])}))
`, database, added[0].id], { encoding: 'utf8' }))
    expect(stored.original_text === example && stored.location_choice === 'provided').toBe(true)
    expect(stored.search_location).toEqual(expectedScope)
    expect(JSON.stringify(stored.language_context) === JSON.stringify(first.language_context)).toBe(true)
    expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement'
      && item.quote === 'without replacing it')).toBe(true)
    const span = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint'
      && item.normalized === 'no_replacement').span
    expect(span.start === 18 && span.end === 38 && span.quote === 'without replacing it').toBe(true)
    const localityReference = stored.interpretation.provenance.reference_versions.locality
    expect(localityReference.release).toBe(release)
    expect(localityReference.sha256).toBe('eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9')
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
    await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
    const shownScope = page.getByRole('region', { name: 'Matched reference association', exact: true })
    await expect(shownScope).toContainText('Matched in this reference; delivery and service coverage are not established.')
    await expect(shownScope).toContainText(expectedAssociation.locality_name)
    await expect(shownScope).toContainText(expectedAssociation.postcode)
    await expect(shownScope).toContainText(expectedAssociation.administrative.municipality_name)
    await expect(shownScope).toContainText(expectedAssociation.administrative.canton)
    await expect(shownScope).toContainText(release)
    if (fixture.selection === 'explicit') await expect(shownScope).not.toContainText('Ecublens (VD)')
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(fixture.town)
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(fixture.postcode)
    await page.getByLabel('Town (optional)', { exact: true }).fill('Changed intended locality')
    await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
    await expect(shownScope).not.toBeVisible()
    await expect(page.getByRole('combobox', { name: 'Reference association', exact: true })).not.toBeVisible()
    expect(attempts.length).toBe(fixture.selection === 'explicit' ? 2 : 1)
    expect(inspectDatabase()).toEqual(after)
    const evidencePath = testInfo.outputPath(`association-${fixture.selection}-evidence.json`)
    writeFileSync(evidencePath, JSON.stringify({ scope: 'Approved pinned association reference with synthetic request meaning and alternative evidence.',
      journey: fixture.selection, before, after_clarification: afterClarification, after,
      clarification_response: clarification, saved_response: { status: response.status(), body },
      saved_request_id: added[0].id, matched_association: expectedAssociation, locality_reference: localityReference,
      exact_raw_values_language_and_independent_requirement_span_preserved: true,
      no_save_during_unresolved_clarification_or_selection: fixture.selection === 'explicit' ? true : null,
      explicit_choice_uses_new_key_and_proof: fixture.selection === 'explicit' ? true : null,
      saved_scope_and_display_come_from_committed_projection: true,
      final_edit_sends_no_request_and_clears_selection_presentation: true,
      prior_records_options_links_source_versions_and_review_dates_preserved: true,
      browser_submissions: attempts.length,
      raw_keys_proofs_digests_headers_bindings_or_complete_captured_requests_recorded: false }, null, 2))
    await testInfo.attach(`association-${fixture.selection}-evidence`, { path: evidencePath, contentType: 'application/json' })
  })
}

test('explicit locality confirmation saves reference-unverified intent without unsupported coverage', async ({ page }, testInfo) => {
  const rawTown = '  Synthetic optional town  '
  const rawPostcode = ' 0123 '
  const before = inspectDatabase()
  expect(before.counts.search_request > 0).toBe(true)
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const attempts: ReturnType<typeof captureAttempt>[] = []
  page.on('request', request => {
    if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
  })
  await page.goto('/')
  await page.getByLabel('Describe your request').fill(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await page.getByLabel('Town (optional)', { exact: true }).fill(rawTown)
  await page.getByLabel('Postcode (optional)', { exact: true }).fill(rawPostcode)
  const clarificationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
    && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  const clarification = await clarificationResponse
  expect(clarification.status()).toBe(200)
  const clarificationBody = await clarification.json()
  expect(clarificationBody.outcome).toBe('clarification_required')
  expect(clarificationBody.persistence).toEqual({ state: 'not_attempted' })
  expect(clarificationBody.issues).toEqual([{ code: 'locality_reference_unavailable' }])
  await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('cannot currently be verified')
  await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('Confirmation establishes intended scope only.')
  await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability')
  const confirm = page.getByRole('button', { name: 'Confirm entered locality as intended scope', exact: true })
  await expect(confirm).toBeEnabled()
  await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(rawTown)
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(rawPostcode)
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
    await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  }
  await expect(page.getByTestId('saved-option')).toHaveCount(0)
  await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  expect(attempts.length).toBe(1)
  const afterClarification = inspectDatabase()
  expect(afterClarification).toEqual(before)
  const confirmationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
    && response.request().method() === 'POST')
  await confirm.click()
  const response = await confirmationResponse
  expect(response.status()).toBe(201)
  const saved = await response.json()
  expect(saved.outcome).toBe('insufficient_coverage')
  expect(saved.persistence.state).toBe('saved')
  expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  expect(saved.coverage.limitation_codes).toContain('geographic_applicability_unverified')
  const expectedScope = { country_code: 'CH', town: rawTown, postcode: rawPostcode,
    locality: { confirmation: 'user_confirmed', verification: 'reference_unverified',
      normalized: { town: 'synthetic optional town', postcode: '0123' } } }
  expect(saved.search_scope).toEqual(expectedScope)
  expect(attempts.length).toBe(2)
  const initial = JSON.parse(attempts[0].body)
  const confirmed = JSON.parse(attempts[1].body)
  expect(initial.location_choice === 'provided' && confirmed.location_choice === 'confirmed_unverified').toBe(true)
  expect(initial.submission_key !== confirmed.submission_key).toBe(true)
  expect(attempts[0].proofDigest !== attempts[1].proofDigest).toBe(true)
  expect(confirmed.text === initial.text && confirmed.text === example).toBe(true)
  expect(JSON.stringify(confirmed.search_location) === JSON.stringify(initial.search_location)).toBe(true)
  expect(JSON.stringify(confirmed.search_location) === JSON.stringify({ country_code: 'CH', town: rawTown, postcode: rawPostcode })).toBe(true)
  expect(JSON.stringify(confirmed.language_context) === JSON.stringify(initial.language_context)).toBe(true)
  const after = inspectDatabase()
  expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
    request_alternative: before.counts.request_alternative,
    request_alternative_evidence: before.counts.request_alternative_evidence })
  const added = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  expect(added.length).toBe(1)
  expect(added[0].id).toBe(saved.persistence.request_id)
  expect(added[0].projection).toEqual(saved)
  expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  expect(after.snapshots).toEqual(before.snapshots)
  const stored = JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
        'location_choice':row[3],'language_context':json.loads(row[4])}))
`, database, added[0].id], { encoding: 'utf8' }))
  expect(stored.original_text === example).toBe(true)
  expect(stored.location_choice).toBe('confirmed_unverified')
  expect(stored.search_location).toEqual(expectedScope)
  expect(JSON.stringify(stored.language_context) === JSON.stringify(initial.language_context)).toBe(true)
  expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement' && item.quote === 'without replacing it')).toBe(true)
  const constraintSpan = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint' && item.normalized === 'no_replacement')
  expect(constraintSpan.span.start === 18 && constraintSpan.span.end === 38 && constraintSpan.span.quote === 'without replacing it').toBe(true)
  expect(stored.interpretation.provenance.reference_versions.country.release).toBe('geonames-countryInfo-2026-10-23-v1')
  await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  const scope = page.getByRole('region', { name: 'Confirmed intended locality', exact: true })
  await expect(scope).toContainText('User-confirmed intended locality; reference-unverified.')
  await expect(scope).toContainText('does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability')
  await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
  await expect(page.getByTestId('saved-option')).toHaveCount(0)
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Search country')).toHaveValue('CH')
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(rawTown)
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(rawPostcode)
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.getByRole('alert')).not.toBeVisible()
  await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  await page.getByLabel('Town (optional)', { exact: true }).fill('Changed synthetic town')
  await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  await expect(scope).not.toBeVisible()
  await expect(confirm).not.toBeVisible()
  await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
  expect(attempts.length).toBe(2)
  expect(inspectDatabase()).toEqual(after)
  const evidencePath = testInfo.outputPath('confirmed-locality-evidence.json')
  writeFileSync(evidencePath, JSON.stringify({
    scope: 'One explicit O-1 locality-intent confirmation with real approved country reference and synthetic meaning/evidence.',
    expected_fixture_outcome: 'insufficient_coverage; ordinary in-CH support does not establish applicability for the entered locality',
    before, after_clarification: afterClarification, after,
    clarification_response: { status: clarification.status(), body: clarificationBody },
    confirmed_response: { status: response.status(), body: saved },
    saved_request_id: added[0].id, saved_scope: stored.search_location,
    country_reference: stored.interpretation.provenance.reference_versions.country,
    posts_after_clarification: 1, posts_after_explicit_confirmation: 2, posts_after_non_submitting_edit: attempts.length,
    no_saved_rows_before_explicit_confirmation: true,
    confirmation_uses_new_key_and_proof_with_unchanged_text_raw_locality_and_language: true,
    original_no_replacement_requirement_and_span_provenance_preserved: true,
    raw_locality_and_normalized_leading_zero_postcode_retained_separately: true,
    saved_status_comes_from_actual_committed_projection: true,
    final_locality_edit_clears_confirmation_presentation_without_submitting: true,
    prior_records_options_links_source_versions_and_review_dates_preserved: true,
    no_raw_key_proof_digest_header_binding_or_complete_captured_request_recorded: true,
  }, null, 2))
  await testInfo.attach('confirmed-locality-evidence', { path: evidencePath, contentType: 'application/json' })
})

test('approved country selector preserves cleared input and saves XK coverage', async ({ page }, testInfo) => {
  const before = inspectDatabase()
  expect(before.counts.search_request > 0).toBe(true)
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  const catalogueResponse = await page.request.get('/api/countries')
  expect(catalogueResponse.status()).toBe(200)
  const catalogue = await catalogueResponse.json()
  expect(typeof catalogue.version === 'string' && catalogue.version.length > 0).toBe(true)
  expect(catalogue.countries.length).toBe(250)
  expect(catalogue.countries.some((entry: { code: string }) => entry.code === 'XK')).toBe(true)
  expect(catalogue.countries.some((entry: { code: string }) => entry.code === 'AN' || entry.code === 'CS')).toBe(false)
  let submissions = 0
  page.on('request', request => {
    if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') submissions += 1
  })
  await page.goto('/')
  const country = page.getByRole('combobox', { name: 'Search country', exact: true })
  await expect(country).toBeEnabled()
  await expect(country).toHaveValue('CH')
  await expect(country.locator('option')).toHaveCount(251)
  const visibleCountries = await country.locator('option').evaluateAll(options => options
    .map(option => ({ code: (option as HTMLOptionElement).value, label: option.textContent || '' }))
    .filter(option => option.code !== '')
    .map(option => ({ code: option.code, name: option.label.slice(`${option.code} — `.length) })))
  expect(visibleCountries).toEqual(catalogue.countries)
  await expect(country.locator('option:checked')).toHaveText('CH — Switzerland')
  await expect(page.getByRole('link', { name: 'GeoNames', exact: true })).toHaveAttribute('href', catalogue.attribution.source_link)
  await expect(page.getByRole('link', { name: catalogue.attribution.license, exact: true })).toHaveAttribute('href', catalogue.attribution.license_link)
  await expect(page.getByText('Approved country reference; interpretation and alternative evidence remain synthetic.', { exact: true })).toBeVisible()
  await page.getByLabel('Describe your request').fill(example)
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
  await country.selectOption('')
  await expect(country).toHaveValue('')
  expect(submissions).toBe(0)
  await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  const emptyValidation = await country.evaluate(element => {
    const select = element as HTMLSelectElement
    return { value: select.value, valid: select.validity.valid, value_missing: select.validity.valueMissing,
      message_present: select.validationMessage.length > 0 }
  })
  expect(emptyValidation).toEqual({ value: '', valid: false, value_missing: true, message_present: true })
  expect(submissions).toBe(0)
  await expect(country).toHaveValue('')
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
  await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
    await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  }
  const afterEmpty = inspectDatabase()
  expect(afterEmpty).toEqual(before)
  await country.selectOption('XK')
  await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  await expect(country).toHaveValue('XK')
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  expect(submissions).toBe(0)
  expect(inspectDatabase()).toEqual(before)
  const pending = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
    && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  const response = await pending
  expect(response.status()).toBe(201)
  const saved = await response.json()
  expect(saved.outcome).toBe('insufficient_coverage')
  expect(saved.persistence.state).toBe('saved')
  expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  expect(submissions).toBe(1)
  await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  await expect(page.getByText('Research is unavailable in this increment; alternatives may exist.', { exact: false })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
  await expect(page.getByTestId('saved-option')).toHaveCount(0)
  await expect(page.getByRole('alert')).not.toBeVisible()
  await expect(page.getByRole('status')).not.toBeVisible()
  await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  await expect(country).toHaveValue('XK')
  await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  const after = inspectDatabase()
  expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
    request_alternative: before.counts.request_alternative,
    request_alternative_evidence: before.counts.request_alternative_evidence })
  const added = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  expect(added.length).toBe(1)
  expect(added[0].id).toBe(saved.persistence.request_id)
  expect(added[0].projection).toEqual(saved)
  await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  expect(after.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
    .toEqual(before.snapshots.request_alternative)
  expect(after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
    .toEqual(before.snapshots.request_alternative_evidence)
  expect(after.snapshots.evidence).toEqual(before.snapshots.evidence)
  const stored = JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),
        'search_location':json.loads(row[2]),'language_context':json.loads(row[3])}))
`, database, added[0].id], { encoding: 'utf8' }))
  expect(stored.original_text === example).toBe(true)
  expect(JSON.stringify(stored.search_location) === JSON.stringify({ country_code: 'XK' })).toBe(true)
  expect(stored.interpretation.constraints.some((item: { value: string }) => item.value === 'no_replacement')).toBe(true)
  expect(stored.language_context.browser_language === 'en').toBe(true)
  const evidencePath = testInfo.outputPath('approved-country-selector-evidence.json')
  writeFileSync(evidencePath, JSON.stringify({
    scope: 'One approved source-based country selector with synthetic request meaning and alternative evidence.',
    country_reference: { version: catalogue.version, included: catalogue.countries.length,
      exact_UI_API_code_and_source_name_agreement: true, explicit_empty_choice: true,
      XK_included_AN_CS_excluded: true, attribution_source_and_license_links_displayed: true },
    empty_country_validation: emptyValidation, comparison_posts_after_clear_and_validation: 0,
    comparison_posts_after_select_before_submit: 0, comparison_posts_after_explicit_submit: submissions,
    before, after_empty_validation: afterEmpty, after,
    actual_response: { status: response.status(), body: saved }, saved_request_id: added[0].id,
    initial_CH_and_explicit_empty_preserved_without_default_reset: true,
    text_optional_fields_independent_constraint_and_language_context_retained: true,
    prior_requests_options_links_source_versions_and_review_dates_preserved: true,
    no_key_proof_header_binding_or_complete_captured_request_recorded: true,
  }, null, 2))
  await testInfo.attach('approved-country-selector-evidence', { path: evidencePath, contentType: 'application/json' })
})

for (const fixture of [
  {
    kind: 'product', text: 'Find a secondhand laptop', subject: 'laptop',
    subjectSpan: { start: 18, end: 24, quote: 'laptop' },
    constraints: [{ value: 'secondhand', start: 7, end: 17, quote: 'secondhand' }],
    alternativeId: '00000000-0000-4000-8000-000000000510', evidenceId: '30000000-0000-4000-8000-000000000510',
    displayName: 'Reused laptop (synthetic product)', amount: '240.00', unit: 'secondhand laptop',
    basis: 'fictional item price', exclusions: ['delivery', 'accessories'], scope: { country_code: 'CH' },
    publisher: 'Fictional laptop retailer', sourceReference: 'synthetic:secondhand-laptop-v1',
    sourceQuote: 'Fictional test listing: a secondhand laptop for delivery to CH, CHF 240.00 per secondhand laptop. Delivery and accessories excluded; no real offer or stock claim.',
    descriptionParts: ['Fictional', 'secondhand laptop', 'CH'], explanationParts: ['240.00', 'delivery', 'accessories', 'fictional'],
  },
  {
    kind: 'habit', text: 'Refill my existing bottle with potable tap water instead of buying bottled water', subject: 'drinking_water',
    subjectSpan: { start: 31, end: 48, quote: 'potable tap water' },
    constraints: [
      { value: 'existing_bottle', start: 7, end: 25, quote: 'my existing bottle' },
      { value: 'potable_tap_water', start: 31, end: 48, quote: 'potable tap water' },
      { value: 'avoid_bottled_water', start: 49, end: 80, quote: 'instead of buying bottled water',
        negation: { start: 49, end: 59, quote: 'instead of' } },
    ],
    alternativeId: '00000000-0000-4000-8000-000000000520', evidenceId: '30000000-0000-4000-8000-000000000520',
    displayName: 'Refill an existing bottle (synthetic habit)', amount: '0.10', unit: 'refill',
    basis: 'hypothetical flat charge per refill', exclusions: ['bottle purchase', 'cleaning'],
    scope: { country_code: 'CH', conditions: ['existing_bottle', 'potable_tap_water'] },
    publisher: 'Fictional refill guide', sourceReference: 'synthetic:bottle-refill-habit-v1',
    sourceQuote: 'Fictional habit example in CH: refill an existing bottle with potable tap water instead of buying bottled water, conditional on an existing bottle and potable tap water. Hypothetical flat charge CHF 0.10 per refill; bottle purchase and cleaning excluded. No bottle capacity, local water quality, real tariff or environmental advantage is established.',
    descriptionParts: ['Fictional', 'existing bottle', 'potable tap water'],
    explanationParts: ['0.10', 'flat charge per refill', 'bottle purchase', 'cleaning', 'local tap-water'],
  },
] as const) {
  test(`prepared synthetic ${fixture.kind} comparison retains its specific meaning and evidence`, async ({ page }, testInfo) => {
    const before = inspectDatabase()
    const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
    const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
    expect(before.snapshots.evidence.some(([id]: [string, ...unknown[]]) => id === fixture.evidenceId)).toBe(true)
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(fixture.text)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
    const response = await responsePromise
    expect(response.status()).toBe(201)
    const saved = await response.json()
    expect(saved.outcome).toBe('comparison')
    expect(saved.persistence.state).toBe('saved')
    expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    expect(saved.comparison.options.length).toBe(1)
    const option = saved.comparison.options[0]
    expect(option.alternative_id).toBe(fixture.alternativeId)
    expect(option.display_name).toBe(fixture.displayName)
    expect(option.financial).toMatchObject({ status: 'supported', amount: fixture.amount, currency: 'CHF',
      unit: fixture.unit, period: 'once', basis: fixture.basis, exclusions: [...fixture.exclusions],
      charges_known: false, total_cost: null, difference: null, baseline: null })
    expect(option.environmental.status).toBe('unknown')
    expect(option.availability).toEqual({ status: 'unknown', value: null })
    expect(option.geographic_scope).toEqual(fixture.scope)
    expect(option.evidence.length).toBe(1)
    expect(option.evidence[0]).toMatchObject({ version_id: fixture.evidenceId, publisher: fixture.publisher,
      source_reference: fixture.sourceReference, supporting_quote: fixture.sourceQuote,
      reviewed_at: '2026-10-15T10:00:00+00:00', synthetic: true })
    for (const constraint of fixture.constraints) {
      const assessment = option.claims.find((claim: { claim: string }) => claim.claim === constraint.value)
      expect(assessment).toMatchObject({ support: 'supported', freshness: 'fresh', requirement: 'satisfied' })
    }
    const after = inspectDatabase()
    expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 1,
      request_alternative_evidence: before.counts.request_alternative_evidence + 1 })
    const addedRequests = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(addedRequest.projection).toEqual(saved)
    const storedOptions = after.snapshots.request_alternative.filter((row: [string, string, ...unknown[]]) => row[1] === addedRequest.id)
    expect(storedOptions.length).toBe(1)
    expect(storedOptions[0][0]).toBe(option.option_id)
    expect(storedOptions[0][2]).toBe(fixture.alternativeId)
    expect(JSON.parse(storedOptions[0][4])).toEqual(option)
    const associations = after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => id === option.option_id)
    expect(associations).toEqual([[option.option_id, fixture.evidenceId]])
    expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(after.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(after.snapshots.evidence).toEqual(before.snapshots.evidence)
    const storedRequest = JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2])}))
`, database, addedRequest.id], { encoding: 'utf8' }))
    const interpretation = storedRequest.interpretation
    expect(storedRequest.original_text === fixture.text).toBe(true)
    expect(JSON.stringify(storedRequest.search_location) === JSON.stringify({ country_code: 'CH' })).toBe(true)
    expect(interpretation.subject === fixture.subject).toBe(true)
    expect(interpretation.goals.length === 0 && interpretation.baseline === null && interpretation.budget === null).toBe(true)
    expect(JSON.stringify(interpretation.actions) === JSON.stringify(fixture.kind === 'habit' ? ['refill'] : [])).toBe(true)
    expect(interpretation.constraints.length === fixture.constraints.length).toBe(true)
    const subjectItem = interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'subject' && item.normalized === fixture.subject)
    expect(subjectItem.span.start === fixture.subjectSpan.start && subjectItem.span.end === fixture.subjectSpan.end
      && subjectItem.span.quote === fixture.subjectSpan.quote).toBe(true)
    for (const constraint of fixture.constraints) {
      expect(interpretation.constraints.some((item: { value: string; quote: string }) => item.value === constraint.value && item.quote === constraint.quote)).toBe(true)
      const originalItem = interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint' && item.normalized === constraint.value)
      expect(originalItem.span.start === constraint.start && originalItem.span.end === constraint.end && originalItem.span.quote === constraint.quote).toBe(true)
      if ('negation' in constraint) {
        expect(originalItem.negation.start === constraint.negation.start && originalItem.negation.end === constraint.negation.end
          && originalItem.negation.quote === constraint.negation.quote).toBe(true)
      }
    }
    if (fixture.kind === 'habit') {
      const actionItem = interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'action' && item.normalized === 'refill')
      expect(actionItem.span.start === 0 && actionItem.span.end === 6 && actionItem.span.quote === 'Refill').toBe(true)
    }
    const result = page.getByRole('region', { name: 'Saved comparison', exact: true })
    await expect(result).toBeVisible()
    await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
    const shown = page.getByTestId('saved-option')
    await expect(shown).toHaveCount(1)
    await expect(shown).toHaveAttribute('data-option-id', option.option_id)
    await expect(shown.getByRole('heading')).toHaveText(fixture.displayName)
    for (const part of fixture.descriptionParts) await expect(shown.locator('p').nth(0)).toContainText(part)
    for (const part of fixture.explanationParts) await expect(shown.locator('p').nth(1)).toContainText(part)
    const financial = shown.locator('dt:has-text("Financial information") + dd')
    await expect(financial).toContainText(`CHF ${fixture.amount}`)
    await expect(financial).toContainText(fixture.unit)
    await expect(financial).toContainText(fixture.basis)
    for (const excluded of fixture.exclusions) await expect(financial).toContainText(excluded)
    await expect(shown.locator('dt:has-text("Total cost") + dd')).toContainText(/unknown/i)
    await expect(shown.locator('dt:has-text("Cost difference") + dd')).toContainText(/unknown/i)
    await expect(shown.locator('dt:has-text("Current-choice baseline") + dd')).toContainText(/unspecified|unknown|not provided|not reported|no baseline/i)
    await expect(shown.locator('dt:has-text("Environmental/resource information") + dd')).toContainText(/unknown|no supported/i)
    await expect(shown.locator('dt:has-text("Availability") + dd')).toContainText(/unknown/i)
    if (fixture.kind === 'habit') {
      const geography = shown.locator('dt:has-text("Geographic scope") + dd')
      await expect(geography).toContainText('CH')
      await expect(geography).toContainText('existing bottle')
      await expect(geography).toContainText('potable tap water')
      await expect(shown.locator('dt:has-text("Conditions and unknowns") + dd')).toContainText('potable tap water')
      await expect(shown.locator('p').nth(1)).toContainText(/does not confirm local tap-water/i)
    }
    await shown.getByText(`Evidence: ${fixture.publisher}`, { exact: true }).click()
    await expect(shown.locator('blockquote')).toHaveText(fixture.sourceQuote)
    await expect(shown).toContainText(fixture.sourceReference)
    await expect(result).not.toContainText(/bicycle|repair|service/i)
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByLabel('Describe your request')).toHaveValue(fixture.text)
    const evidencePath = testInfo.outputPath(`${fixture.kind}-comparison-evidence.json`)
    writeFileSync(evidencePath, JSON.stringify({ scope: 'One exact prepared synthetic example; not general language or factual acceptance.',
      example_kind: fixture.kind, before, after, actual_response: { status: response.status(), body: saved },
      saved_request_id: addedRequest.id, option_id: option.option_id, alternative_id: fixture.alternativeId,
      evidence_associations: associations, baseline_was_nonempty: before.counts.search_request > 0,
      original_text_meaning_requirements_and_span_provenance_preserved: true,
      fixture_specific_content_units_conditions_and_unknowns_displayed: true,
      no_unrelated_bicycle_repair_or_service_content_in_result: true,
      prior_requests_options_links_and_source_versions_review_dates_preserved: true,
      real_application_qualification_rendering_persistence_and_response_used: true,
      credentials_headers_bindings_or_complete_captured_requests_recorded: false }, null, 2))
    await testInfo.attach(`${fixture.kind}-comparison-evidence`, { path: evidencePath, contentType: 'application/json' })
  })
}

for (const transition of [
  { action: 'fresh_reset', country: 'CH' },
  { action: 'country_edit', country: 'DE' },
] as const) {
  test(`direct new intent after uncertain save: ${transition.action}`, async ({ page }, testInfo) => {
    const controlFile = process.env.RESOLENA_TEST_UNCERTAIN_SAVE_FILE!
    const clockFile = process.env.RESOLENA_E2E_CLOCK_FILE!
    expect(Boolean(controlFile) && Boolean(clockFile)).toBe(true)
    expect(existsSync(controlFile)).toBe(false)
    const previousClock = readFileSync(clockFile)
    const faultEvidenceFile = controlFile.replace(/\.json$/, '.evidence.json')
    const timeT0 = '2026-10-15T10:00:00+00:00'
    const timeT1 = '2027-10-16T10:00:00+00:00'
    const warning = 'An earlier submission may already be saved. Editing starts a new submission; it does not undo an earlier save.'
    const before = inspectDatabase()
    const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
    const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
    const attempts: ReturnType<typeof captureAttempt>[] = []
    function readStoredRequest(requestId: string) {
      return JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context,assessed_at,outcome FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
        'location_choice':row[3],'language_context':json.loads(row[4]),'assessed_at':row[5],'outcome':row[6]}))
`, database, requestId], { encoding: 'utf8' }))
    }
    async function expectNoSavedPresentation() {
      for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
        await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
      }
      await expect(page.getByTestId('saved-option')).toHaveCount(0)
      await expect(page.getByTestId('request-id')).toHaveCount(0)
      await expect(page.getByText(timeT0, { exact: false })).not.toBeVisible()
    }
    await page.route('**/api/comparisons', async route => {
      attempts.push(captureAttempt(route.request()))
      if (attempts.length === 1) {
        const key = JSON.parse(attempts[0].body).submission_key
        writeFileSync(controlFile, JSON.stringify({ submission_key_digest: createHash('sha256').update(JSON.stringify(key)).digest('hex') }))
      }
      await route.continue()
    })
    try {
      writeFileSync(clockFile, JSON.stringify({ now: timeT0 }))
      await page.goto('/')
      await page.getByLabel('Describe your request').fill(example)
      await expect(page.getByLabel('Search country')).toHaveValue('CH')
      await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
      await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
      const unknownResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
        && response.request().method() === 'POST')
      await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
      const unknown = await unknownResponse
      expect(unknown.status()).toBe(503)
      const unknownBody = await unknown.json()
      expect(unknownBody).toEqual({ outcome: 'persistence_error', persistence: { state: 'unknown' },
        issues: [{ code: 'comparison_save_failed' }], assessed_outcome: 'comparison' })
      await expect(page.getByRole('alert')).toContainText('Saving could not be confirmed')
      await expect(page.getByRole('alert')).toContainText('may already be saved')
      for (const wording of ['could not be saved', 'cancelled', 'deleted', 'rolled back']) {
        await expect(page.getByRole('alert')).not.toContainText(wording)
      }
      await expect(page.getByText(warning, { exact: true })).toBeVisible()
      await expect(page.getByRole('status')).not.toBeVisible()
      await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
      await expect(page.getByLabel('Describe your request')).toHaveValue(example)
      await expect(page.getByLabel('Search country')).toHaveValue('CH')
      await expectNoSavedPresentation()
      const afterUnknown = inspectDatabase()
      expect(afterUnknown.counts).toEqual({ search_request: before.counts.search_request + 1,
        request_alternative: before.counts.request_alternative + 2,
        request_alternative_evidence: before.counts.request_alternative_evidence + 2 })
      const addedOriginals = afterUnknown.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
      expect(addedOriginals.length).toBe(1)
      const original = addedOriginals[0]
      expect(original.projection.outcome).toBe('comparison')
      expect(original.projection.assessed_at).toBe(timeT0)
      expect(original.id).toBe(original.projection.persistence.request_id)
      const originalOptionIds = new Set<string>(original.projection.comparison.options.map((option: { option_id: string }) => option.option_id))
      expect(originalOptionIds.size).toBe(2)
      const originalAssociations = afterUnknown.snapshots.request_alternative_evidence
        .filter(([id]: [string, string]) => originalOptionIds.has(id))
      expect(originalAssociations.length).toBe(2)
      const originalStoredRequest = readStoredRequest(original.id)
      expect(originalStoredRequest.original_text === example).toBe(true)
      expect(JSON.stringify(originalStoredRequest.search_location) === JSON.stringify({ country_code: 'CH' })).toBe(true)
      expect(JSON.stringify(originalStoredRequest.interpretation.constraints)
        === JSON.stringify([{ value: 'no_replacement', quote: 'without replacing it' }])).toBe(true)
      expect(originalStoredRequest.assessed_at).toBe(timeT0)
      expect(afterUnknown.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
      expect(afterUnknown.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
        .toEqual(before.snapshots.request_alternative)
      expect(afterUnknown.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
        .toEqual(before.snapshots.request_alternative_evidence)
      expect(afterUnknown.snapshots.evidence).toEqual(before.snapshots.evidence)
      await expect(page.getByText(original.id, { exact: false })).not.toBeVisible()
      expect(existsSync(controlFile)).toBe(false)
      const fault = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
      expect(fault.fault_counts).toEqual({ real_commits: 1, confirmation_losses: 1, read_failures: 1 })
      expect(fault.independent_after_commit).toEqual(afterUnknown)
      expect(fault.after_fault).toEqual(afterUnknown)
      expect(fault.dialect_methods_restored).toBe(true)
      expect(fault.observer_rows_supplied_to_application).toBe(false)
      await page.waitForTimeout(300)
      const requestsBeforeChange = attempts.length
      expect(requestsBeforeChange).toBe(1)
      expect(inspectDatabase()).toEqual(afterUnknown)

      if (transition.action === 'fresh_reset') {
        await page.getByRole('button', { name: 'Start a fresh search', exact: true }).click()
      } else {
        await page.getByLabel('Search country').selectOption('DE')
      }
      await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
      await expect(page.getByRole('button', { name: 'Find alternatives', exact: true })).toBeEnabled()
      await expect(page.getByRole('alert')).not.toBeVisible()
      await expect(page.getByLabel('Describe your request')).toHaveValue(example)
      await expect(page.getByLabel('Search country')).toHaveValue(transition.country)
      await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
      await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
      await expect(page.getByText(warning, { exact: true })).toBeVisible()
      await expectNoSavedPresentation()
      await expect(page.getByText(original.id, { exact: false })).not.toBeVisible()
      const requestsAfterChange = attempts.length
      expect(requestsAfterChange).toBe(1)
      const afterChange = inspectDatabase()
      expect(afterChange).toEqual(afterUnknown)

      writeFileSync(clockFile, JSON.stringify({ now: timeT1 }))
      await expect(page.getByText(warning, { exact: true })).toBeVisible()
      expect(attempts.length).toBe(1)
      const freshResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
        && response.request().method() === 'POST')
      await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
      const response = await freshResponse
      expect(response.status()).toBe(201)
      const saved = await response.json()
      expect(saved.outcome).toBe('insufficient_coverage')
      expect(saved.persistence.state).toBe('saved')
      expect(saved.assessed_at).toBe(timeT1)
      expect('comparison' in saved).toBe(false)
      if (transition.action === 'fresh_reset') {
        expect(saved.coverage.limitation_codes).toContain('essential_evidence_expired')
      }
      expect(attempts.length).toBe(2)
      const { submission_key: originalKey, ...originalValues } = JSON.parse(attempts[0].body)
      const { submission_key: newKey, ...newValues } = JSON.parse(attempts[1].body)
      expect(newKey !== originalKey).toBe(true)
      expect(attempts[1].proofDigest !== attempts[0].proofDigest).toBe(true)
      const expectedValues = { ...originalValues, search_location: { country_code: transition.country } }
      expect(JSON.stringify(newValues) === JSON.stringify(expectedValues)).toBe(true)
      expect(newValues.text === example && newValues.text === originalValues.text).toBe(true)
      expect(JSON.stringify(newValues.language_context) === JSON.stringify(originalValues.language_context)).toBe(true)
      const after = inspectDatabase()
      expect(after.counts).toEqual({ search_request: afterUnknown.counts.search_request + 1,
        request_alternative: afterUnknown.counts.request_alternative,
        request_alternative_evidence: afterUnknown.counts.request_alternative_evidence })
      const originalStateIds = new Set<string>(afterUnknown.rows.map((row: { id: string }) => row.id))
      const addedCoverage = after.rows.filter((row: { id: string }) => !originalStateIds.has(row.id))
      expect(addedCoverage.length).toBe(1)
      const current = addedCoverage[0]
      expect(current.id).toBe(saved.persistence.request_id)
      expect(current.id === original.id).toBe(false)
      expect(current.projection).toEqual(saved)
      expect(after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id)).length).toBe(2)
      expect(after.rows.filter((row: { id: string }) => originalStateIds.has(row.id))).toEqual(afterUnknown.rows)
      expect(after.snapshots).toEqual(afterUnknown.snapshots)
      expect(JSON.stringify(readStoredRequest(original.id)) === JSON.stringify(originalStoredRequest)).toBe(true)
      const newStoredRequest = readStoredRequest(current.id)
      expect(newStoredRequest.original_text === example).toBe(true)
      expect(JSON.stringify(newStoredRequest.search_location) === JSON.stringify({ country_code: transition.country })).toBe(true)
      expect(JSON.stringify(newStoredRequest.language_context) === JSON.stringify(originalStoredRequest.language_context)).toBe(true)
      expect(JSON.stringify(newStoredRequest.interpretation.constraints) === JSON.stringify(originalStoredRequest.interpretation.constraints)).toBe(true)
      expect(newStoredRequest.assessed_at).toBe(timeT1)
      expect(newStoredRequest.outcome).toBe('insufficient_coverage')
      await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
      await expect(page.getByText(current.id, { exact: true })).toBeVisible()
      await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
      await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
      await expect(page.getByTestId('saved-option')).toHaveCount(0)
      await expect(page.getByText(original.id, { exact: false })).not.toBeVisible()
      await expect(page.getByText(warning, { exact: true })).not.toBeVisible()
      await expect(page.getByRole('alert')).not.toBeVisible()
      await expect(page.getByRole('status')).not.toBeVisible()
      await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
      await expect(page.getByLabel('Describe your request')).toHaveValue(example)
      await expect(page.getByLabel('Search country')).toHaveValue(transition.country)
      expect(attempts.length).toBe(2)
      const evidencePath = testInfo.outputPath(`${transition.action}-after-uncertainty-evidence.json`)
      writeFileSync(evidencePath, JSON.stringify({ scope: 'Direct new intent after actual committed-unknown response, without recovery acknowledgement.',
        transition: transition.action, before, after_unknown: afterUnknown, after_change: afterChange, after,
        unknown_response: { status: unknown.status(), body: unknownBody }, fresh_response: { status: response.status(), body: saved },
        original_request_id: original.id, original_stored_nonsecret_request_metadata_unchanged: true,
        original_option_ids: [...originalOptionIds], original_evidence_associations: originalAssociations,
        new_request_id: current.id, new_stored_text_location_context_and_constraints_match_current_intent: true,
        time_t0: timeT0, time_t1: timeT1,
        request_counts: { before_reset_or_edit: requestsBeforeChange, after_reset_or_edit: requestsAfterChange, after_explicit_submission: attempts.length },
        bounded_no_automatic_continuation_ms: 300, no_recovery_request_or_acknowledgement: true,
        new_key_and_proof: true, current_payload_text_context_and_independent_constraints_preserved: true,
        earlier_save_warning_visible_until_explicit_new_submission: true, unchanged_existing_warning_lifecycle: true,
        original_comparison_and_all_prior_records_snapshots_source_evidence_unchanged: true,
        baseline_was_nonempty: before.counts.search_request > 0, fault,
        country_inputs_are_existing_synthetic_fixtures_not_reference_validation: true,
        raw_keys_proofs_digests_headers_bindings_or_complete_requests_recorded: false }, null, 2))
      await testInfo.attach(`${transition.action}-after-uncertainty-evidence`, { path: evidencePath, contentType: 'application/json' })
    } finally {
      writeFileSync(clockFile, previousClock)
      rmSync(controlFile, { force: true })
    }
  })
}

test('unknown absent persistence explicitly recovers with current reassessment', async ({ page }, testInfo) => {
  const controlFile = process.env.RESOLENA_TEST_UNCERTAIN_SAVE_FILE!
  const clockFile = process.env.RESOLENA_E2E_CLOCK_FILE!
  expect(Boolean(controlFile) && Boolean(clockFile)).toBe(true)
  expect(existsSync(controlFile)).toBe(false)
  const previousClock = readFileSync(clockFile)
  const faultEvidenceFile = controlFile.replace(/\.json$/, '.evidence.json')
  const processingEvidenceFile = controlFile.replace(/\.json$/, '.processing.json')
  const timeT0 = '2026-10-15T10:00:00+00:00'
  const timeT1 = '2027-10-16T10:00:00+00:00'
  const before = inspectDatabase()
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const attempts: ReturnType<typeof captureAttempt>[] = []
  await page.route('**/api/comparisons', async route => {
    attempts.push(captureAttempt(route.request()))
    if (attempts.length === 1) {
      const key = JSON.parse(attempts[0].body).submission_key
      writeFileSync(controlFile, JSON.stringify({ mode: 'absent',
        submission_key_digest: createHash('sha256').update(JSON.stringify(key)).digest('hex') }))
    }
    await route.continue()
  })
  function expectDiscardedIdentitiesAbsent(stored: ReturnType<typeof inspectDatabase>, prepared: { request_id: string; option_ids: string[] }) {
    const discardedOptions = new Set(prepared.option_ids)
    expect(stored.rows.some((row: { id: string }) => row.id === prepared.request_id)).toBe(false)
    expect(stored.snapshots.request_alternative.some(([id]: [string, ...unknown[]]) => discardedOptions.has(id))).toBe(false)
    expect(stored.snapshots.request_alternative_evidence.some(([id]: [string, string]) => discardedOptions.has(id))).toBe(false)
  }
  try {
    writeFileSync(clockFile, JSON.stringify({ now: timeT0 }))
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
    const unknownResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
    const unknown = await unknownResponse
    expect(unknown.status()).toBe(503)
    const unknownBody = await unknown.json()
    expect(unknownBody).toEqual({ outcome: 'persistence_error', persistence: { state: 'unknown' },
      issues: [{ code: 'comparison_save_failed' }], assessed_outcome: 'comparison' })
    await expect(page.getByRole('alert')).toContainText('Saving could not be confirmed')
    await expect(page.getByRole('alert')).toContainText('may already be saved')
    for (const wording of ['could not be saved', 'rolled back', 'definitely unsaved']) {
      await expect(page.getByRole('alert')).not.toContainText(wording)
    }
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByRole('button', { name: 'Recover submission', exact: true })).toBeEnabled()
    for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
      await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
    }
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    const afterUnknown = inspectDatabase()
    expect(afterUnknown).toEqual(before)
    expect(existsSync(controlFile)).toBe(false)
    await expect.poll(() => existsSync(faultEvidenceFile) && existsSync(processingEvidenceFile), { timeout: 5000 }).toBe(true)
    const fault = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
    expect(fault.mode).toBe('absent')
    expect(fault.fault_counts).toEqual({ real_commits: 0, confirmation_losses: 1, read_failures: 0 })
    expect(fault.real_reconciliation_selects).toBe(1)
    expect(fault.reconciliation_results).toEqual([false])
    expect(fault.normal_driver_rollback_observed).toBe(true)
    expect(fault.dialect_methods_restored).toBe(true)
    expect(fault.observer_rows_supplied_to_application).toBe(false)
    const processingAtT0 = JSON.parse(readFileSync(processingEvidenceFile, 'utf8'))
    expect(processingAtT0.attempts.length).toBe(1)
    const initial = processingAtT0.attempts[0]
    expect(initial.counts).toEqual({ interpret: 1, retrieve: 1, assess_clock: 1, prepare: 1,
      prepare_coverage: 0, save: 1, underlying_commits: 0 })
    expect(initial.returned_outcome).toBe(null)
    expect(initial.raised_persistence_state).toBe('unknown')
    expect(initial.lookup_results.filter((lookup: { scope: string }) => lookup.scope === 'application_initial'))
      .toEqual([{ scope: 'application_initial', found: false, real_selects: 1 }])
    expect(initial.retrieved_count).toBe(2)
    expect(initial.qualified_rendered_count).toBe(2)
    expect(initial.prepared.outcome).toBe('comparison')
    expect(initial.prepared.assessed_at).toBe(timeT0)
    expect(initial.prepared.option_ids.length).toBe(2)
    expect(priorRequestIds.has(initial.prepared.request_id)).toBe(false)
    expectDiscardedIdentitiesAbsent(afterUnknown, initial.prepared)
    await page.waitForTimeout(300)
    expect(attempts.length).toBe(1)
    expect(inspectDatabase()).toEqual(before)

    writeFileSync(clockFile, JSON.stringify({ now: timeT1 }))
    expect(attempts.length).toBe(1)
    const reassessedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Recover submission', exact: true }).click()
    const response = await reassessedResponse
    expect(response.status()).toBe(201)
    const saved = await response.json()
    expect(saved.outcome).toBe('insufficient_coverage')
    expect(saved.persistence.state).toBe('saved')
    expect(saved.assessed_at).toBe(timeT1)
    expect(saved.coverage.limitation_codes).toContain('essential_evidence_expired')
    expect('comparison' in saved).toBe(false)
    expect(attempts.length).toBe(2)
    const original = JSON.parse(attempts[0].body)
    const recovered = JSON.parse(attempts[1].body)
    expect(attempts[1].body === attempts[0].body).toBe(true)
    expect(recovered.submission_key === original.submission_key).toBe(true)
    expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
    expect(recovered.text === example && recovered.text === original.text).toBe(true)
    expect(recovered.search_location).toEqual({ country_code: 'CH' })
    expect(JSON.stringify(recovered.language_context) === JSON.stringify(original.language_context)).toBe(true)
    const processingAtT1 = JSON.parse(readFileSync(processingEvidenceFile, 'utf8'))
    expect(processingAtT1.attempts.length).toBe(2)
    const reassessed = processingAtT1.attempts[1]
    expect(reassessed.counts).toEqual({ interpret: 1, retrieve: 1, assess_clock: 1, prepare: 0,
      prepare_coverage: 1, save: 1, underlying_commits: 1 })
    expect(reassessed.lookup_results.filter((lookup: { scope: string }) => lookup.scope === 'application_initial'))
      .toEqual([{ scope: 'application_initial', found: false, real_selects: 1 }])
    expect(reassessed.retrieved_count).toBe(2)
    expect(reassessed.qualified_rendered_count).toBe(0)
    expect(reassessed.coverage_limitation_codes).toContain('essential_evidence_expired')
    expect(reassessed.prepared.option_ids).toEqual([])
    expect(reassessed.prepared.outcome).toBe('insufficient_coverage')
    expect(reassessed.prepared.assessed_at).toBe(timeT1)
    expect(reassessed.returned_outcome).toBe('insufficient_coverage')
    expect(reassessed.raised_persistence_state).toBe(null)
    expect(processingAtT1.total_counts).toEqual({ interpret: 2, retrieve: 2, assess_clock: 2, prepare: 1,
      prepare_coverage: 1, save: 2, underlying_commits: 1 })
    expect(processingAtT1.original_adapters_unchanged).toBe(true)
    expect(processingAtT1.raw_originating_proofs_or_requests_recorded).toBe(false)
    const afterRecovery = inspectDatabase()
    expect(afterRecovery.counts).toEqual({ search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative, request_alternative_evidence: before.counts.request_alternative_evidence })
    const addedRequests = afterRecovery.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(addedRequest.id).toBe(reassessed.prepared.request_id)
    expect(addedRequest.id === initial.prepared.request_id).toBe(false)
    expect(addedRequest.projection).toEqual(saved)
    expect(afterRecovery.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(afterRecovery.snapshots).toEqual(before.snapshots)
    expectDiscardedIdentitiesAbsent(afterRecovery, initial.prepared)
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
    await expect(page.getByText(addedRequest.id, { exact: true })).toBeVisible()
    await expect(page.getByText('Required evidence has expired;', { exact: false })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    expect(attempts.length).toBe(2)
    const evidencePath = testInfo.outputPath('unknown-absent-reassessment-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before, after_unknown: afterUnknown, after_recovery: afterRecovery,
      unknown_response: { status: unknown.status(), body: unknownBody }, saved_response: { status: response.status(), body: saved },
      discarded_unsaved_request_id: initial.prepared.request_id, discarded_unsaved_option_ids: initial.prepared.option_ids,
      new_saved_request_id: addedRequest.id, discarded_identities_remain_absent: true,
      baseline_was_nonempty: before.counts.search_request > 0, browser_submissions: attempts.length,
      bounded_no_automatic_continuation_ms: 300, same_serialized_body_key_proof_and_context: true,
      explicit_recovery_clicked_without_edits: true, time_t0: timeT0, time_t1: timeT1,
      fields_and_uncertainty_presentation_correct: true, saved_coverage_clears_uncertainty_without_stale_comparison: true,
      prior_records_snapshots_source_evidence_and_review_dates_preserved: true,
      fault_at_t0: fault, processing_at_t0: processingAtT0, processing_at_t1: processingAtT1,
      no_http_stub_or_delivery_abort: true, raw_keys_proofs_digests_headers_bindings_or_complete_requests_recorded: false }, null, 2))
    await testInfo.attach('unknown-absent-reassessment-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    writeFileSync(clockFile, previousClock)
    rmSync(controlFile, { force: true })
  }
})

for (const denial of [
  { status: 403, outcome: 'recovery_not_authorized', code: 'originating_proof_required' },
  { status: 409, outcome: 'submission_key_conflict', code: 'payload_changed' },
] as const) {
  test(`mocked denial UI contract ${denial.status} requires explicit fresh reset before unchanged-value submission`, async ({ page }, testInfo) => {
    const before = inspectDatabase()
    const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
    const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
    const attempts: ReturnType<typeof captureAttempt>[] = []
    const denialBody = { outcome: denial.outcome, persistence: { state: 'not_attempted' }, issues: [{ code: denial.code }] }
    let mockedResponses = 0
    let forwardedRequests = 0
    await page.route('**/api/comparisons', async route => {
      attempts.push(captureAttempt(route.request()))
      if (attempts.length === 1) {
        mockedResponses += 1
        await route.fulfill({ status: denial.status, contentType: 'application/json', body: JSON.stringify(denialBody) })
      } else {
        forwardedRequests += 1
        await route.continue()
      }
    })
    async function expectNoSavedPresentation() {
      for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
        await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
      }
      await expect(page.getByTestId('saved-option')).toHaveCount(0)
      await expect(page.getByTestId('request-id')).toHaveCount(0)
      await expect(page.locator('main code')).toHaveCount(0)
      await expect(page.getByText('Originally assessed at:', { exact: false })).not.toBeVisible()
      await expect(page.getByText('Prepared at the synthetic fixture time:', { exact: false })).not.toBeVisible()
      await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    }
    async function expectUnchangedFields() {
      await expect(page.getByLabel('Describe your request')).toHaveValue(example)
      await expect(page.getByLabel('Search country')).toHaveValue('CH')
      await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
      await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
      for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
        await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
      }
    }
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    const deniedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
    const denied = await deniedResponse
    expect(denied.status()).toBe(denial.status)
    expect(await denied.json()).toEqual(denialBody)
    await expect(page.getByRole('alert')).toHaveText('This submission cannot be recovered with the current page context. Start an explicit fresh search.')
    for (const wording of ['was saved', 'could not be saved', 'rolled back', 'rollback', denial.code]) {
      await expect(page.getByRole('alert')).not.toContainText(wording)
    }
    await expect(page.getByText(denial.code, { exact: false })).not.toBeVisible()
    await expect(page.getByText(denial.outcome, { exact: false })).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expectUnchangedFields()
    await expectNoSavedPresentation()
    await expect(page.getByRole('button', { name: 'Start a fresh search', exact: true })).toBeEnabled()
    const afterDenial = inspectDatabase()
    expect(afterDenial).toEqual(before)
    expect(mockedResponses).toBe(1)
    expect(forwardedRequests).toBe(0)
    await page.waitForTimeout(300)
    const requestsBeforeReset = attempts.length
    expect(requestsBeforeReset).toBe(1)

    await page.getByRole('button', { name: 'Start a fresh search', exact: true }).click()
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByRole('button', { name: 'Find alternatives', exact: true })).toBeEnabled()
    await expectUnchangedFields()
    await expectNoSavedPresentation()
    await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
    const requestsAfterReset = attempts.length
    expect(requestsAfterReset).toBe(1)
    const afterReset = inspectDatabase()
    expect(afterReset).toEqual(before)

    const freshResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
    const response = await freshResponse
    expect(response.status()).toBe(201)
    const saved = await response.json()
    expect(saved.outcome).toBe('comparison')
    expect(saved.persistence.state).toBe('saved')
    expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    expect(attempts.length).toBe(2)
    expect(mockedResponses).toBe(1)
    expect(forwardedRequests).toBe(1)
    const { submission_key: deniedKey, ...deniedValues } = JSON.parse(attempts[0].body)
    const { submission_key: freshKey, ...freshValues } = JSON.parse(attempts[1].body)
    expect(freshKey !== deniedKey).toBe(true)
    expect(attempts[1].proofDigest !== attempts[0].proofDigest).toBe(true)
    expect(JSON.stringify(freshValues) === JSON.stringify(deniedValues)).toBe(true)
    expect(freshValues.text === await page.getByLabel('Describe your request').inputValue()).toBe(true)
    expect(freshValues.search_location.country_code === await page.getByLabel('Search country').inputValue()).toBe(true)
    expect(Object.keys(freshValues.search_location).length === 1 && freshValues.location_choice === 'provided').toBe(true)
    expect(JSON.stringify(freshValues.language_context) === JSON.stringify(deniedValues.language_context)).toBe(true)
    const currentLanguage = await page.evaluate(() => navigator.language.split('-')[0].toLowerCase())
    const currentLanguageContext = ['de', 'fr', 'it', 'en'].includes(currentLanguage) ? { browser_language: currentLanguage } : {}
    expect(JSON.stringify(freshValues.language_context) === JSON.stringify(currentLanguageContext)).toBe(true)
    const after = inspectDatabase()
    expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2 })
    const addedRequests = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(addedRequest.projection).toEqual(saved)
    expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(after.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(after.snapshots.evidence).toEqual(before.snapshots.evidence)
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).toBeVisible()
    await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
    await expect(page.getByTestId('saved-option')).toHaveCount(2)
    for (const [index, option] of saved.comparison.options.entries()) {
      const shown = page.getByTestId('saved-option').nth(index)
      await expect(shown).toHaveAttribute('data-option-id', option.option_id)
      await expect(shown.getByRole('heading')).toHaveText(option.display_name)
    }
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expectUnchangedFields()
    expect(attempts.length).toBe(2)
    const evidencePath = testInfo.outputPath(`mocked-${denial.status}-fresh-action-evidence.json`)
    writeFileSync(evidencePath, JSON.stringify({
      scope: 'Thin React UI-contract case: mocked denial input followed by actual fresh backend saving.',
      denied_input: { mocked: true, status: denial.status, body: denialBody }, backend_denial_or_security_verified: false,
      before, after_denial: afterDenial, after_reset: afterReset, after,
      saved_response: { mocked: false, status: response.status(), body: saved }, saved_request_id: addedRequest.id,
      baseline_was_nonempty: before.counts.search_request > 0, bounded_no_automatic_request_ms: 300,
      request_counts: { before_reset: requestsBeforeReset, after_reset: requestsAfterReset, after_explicit_submission: attempts.length,
        mocked_denial_responses: mockedResponses, actual_backend_requests_forwarded: forwardedRequests },
      loading_ended_fields_and_context_retained: true, explicit_fresh_reset_clears_denial_without_request: true,
      fresh_key_and_proof_differ: true, unchanged_values_and_current_fields_context_used: true,
      no_saved_identity_timestamp_or_internal_detail_presented_on_denial_or_reset: true,
      prior_records_source_evidence_and_review_dates_preserved: true,
      raw_keys_proofs_digests_headers_bindings_or_complete_captured_requests_recorded: false,
    }, null, 2))
    await testInfo.attach(`mocked-${denial.status}-fresh-action-evidence`, { path: evidencePath, contentType: 'application/json' })
  })
}

test('actual processing failure allows explicit unchanged-submission retry and atomic saving', async ({ page }, testInfo) => {
  const controlFile = process.env.RESOLENA_TEST_PROCESSING_ERROR_FILE!
  expect(Boolean(controlFile)).toBe(true)
  expect(existsSync(controlFile)).toBe(false)
  const faultEvidenceFile = controlFile.replace(/\.json$/, '.evidence.json')
  const before = inspectDatabase()
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  const attempts: ReturnType<typeof captureAttempt>[] = []
  await page.route('**/api/comparisons', async route => {
    attempts.push(captureAttempt(route.request()))
    if (attempts.length === 1) {
      const key = JSON.parse(attempts[0].body).submission_key
      writeFileSync(controlFile, JSON.stringify({ submission_key_digest: createHash('sha256').update(JSON.stringify(key)).digest('hex') }))
    }
    await route.continue()
  })
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    const failedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
    const failed = await failedResponse
    expect(failed.status()).toBe(500)
    const failedBody = await failed.json()
    expect(failedBody).toEqual({ outcome: 'processing_error', persistence: { state: 'not_attempted' },
      issues: [{ code: 'comparison_processing_failed' }] })
    await expect(page.getByRole('alert')).toContainText('The comparison could not be prepared')
    for (const wording of ['could not be saved', 'unknown', 'rollback', 'unsupported', 'coverage']) {
      await expect(page.getByRole('alert')).not.toContainText(wording)
    }
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByRole('button', { name: 'Try again', exact: true })).toBeEnabled()
    for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
      await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
    }
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    const afterError = inspectDatabase()
    expect(afterError).toEqual(before)
    expect(existsSync(controlFile)).toBe(false)
    await expect.poll(() => existsSync(faultEvidenceFile), { timeout: 5000 }).toBe(true)
    const faultAfterError = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
    expect(faultAfterError.attempts.length).toBe(1)
    expect(faultAfterError.attempts[0].counts).toEqual({ interpret: 1, retrieve: 1, assess_clock: 0,
      prepare: 0, prepare_coverage: 0, save: 0 })
    expect(faultAfterError.attempts[0].fault_raised).toBe(true)
    expect(faultAfterError.attempts[0].returned_outcome).toBe(null)
    expect(faultAfterError.fault_consumed).toBe(true)
    expect(faultAfterError.original_adapters_unchanged).toBe(true)
    await page.waitForTimeout(300)
    expect(attempts.length).toBe(1)
    expect(inspectDatabase()).toEqual(before)

    const savedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Try again', exact: true }).click()
    const response = await savedResponse
    expect(response.status()).toBe(201)
    const saved = await response.json()
    expect(saved.outcome).toBe('comparison')
    expect(saved.persistence.state).toBe('saved')
    expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    expect(attempts.length).toBe(2)
    const initialPayload = JSON.parse(attempts[0].body)
    const retriedPayload = JSON.parse(attempts[1].body)
    expect(attempts[1].body === attempts[0].body).toBe(true)
    expect(retriedPayload.submission_key === initialPayload.submission_key).toBe(true)
    expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
    expect(retriedPayload.text === example && retriedPayload.text === initialPayload.text).toBe(true)
    expect(retriedPayload.search_location).toEqual({ country_code: 'CH' })
    expect(retriedPayload.language_context).toEqual(initialPayload.language_context)
    const faultAfterRetry = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
    expect(faultAfterRetry.attempts.length).toBe(2)
    expect(faultAfterRetry.attempts[1].counts).toEqual({ interpret: 1, retrieve: 1, assess_clock: 1,
      prepare: 1, prepare_coverage: 0, save: 1 })
    expect(faultAfterRetry.attempts[1].fault_raised).toBe(false)
    expect(faultAfterRetry.attempts[1].returned_outcome).toBe('comparison')
    expect(faultAfterRetry.total_counts).toEqual({ interpret: 2, retrieve: 2, assess_clock: 1,
      prepare: 1, prepare_coverage: 0, save: 1 })
    expect(faultAfterRetry.fault_consumed).toBe(true)
    expect(faultAfterRetry.original_adapters_unchanged).toBe(true)
    expect(faultAfterRetry.raw_originating_proofs_or_requests_recorded).toBe(false)
    const after = inspectDatabase()
    expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2 })
    const addedRequests = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(addedRequest.projection).toEqual(saved)
    expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(after.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(after.snapshots.evidence).toEqual(before.snapshots.evidence)
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).toBeVisible()
    await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
    await expect(page.getByTestId('saved-option')).toHaveCount(2)
    for (const [index, option] of saved.comparison.options.entries()) {
      const shown = page.getByTestId('saved-option').nth(index)
      await expect(shown).toHaveAttribute('data-option-id', option.option_id)
      await expect(shown.getByRole('heading')).toHaveText(option.display_name)
    }
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
      await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
    }
    expect(attempts.length).toBe(2)
    expect(existsSync(controlFile)).toBe(false)
    const evidencePath = testInfo.outputPath('processing-error-retry-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before, after_error: afterError, after,
      error_response: { status: failed.status(), body: failedBody }, saved_response: { status: response.status(), body: saved },
      saved_request_id: addedRequest.id, baseline_was_nonempty: before.counts.search_request > 0,
      browser_submissions: attempts.length, bounded_no_automatic_retry_ms: 300,
      same_serialized_body_key_proof_and_language_context: true, fields_and_language_context_preserved: true,
      loading_ended_on_both_outcomes: true, explicit_try_again_clicked_without_edits: true,
      prior_records_source_evidence_and_review_dates_preserved: true, fault_after_error: faultAfterError,
      fault_after_retry: faultAfterRetry, raw_originating_proofs_headers_bindings_or_requests_recorded: false }, null, 2))
    await testInfo.attach('processing-error-retry-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    rmSync(controlFile, { force: true })
  }
})

test('loading remains active while the required save is uncommitted', async ({ page }, testInfo) => {
  const controlFile = process.env.RESOLENA_TEST_DELAYED_SAVE_FILE!
  expect(Boolean(controlFile)).toBe(true)
  expect(existsSync(controlFile)).toBe(false)
  const reachedFile = controlFile.replace(/\.json$/, '.reached.json')
  const releaseFile = controlFile.replace(/\.json$/, '.release.json')
  const gateEvidenceFile = controlFile.replace(/\.json$/, '.evidence.json')
  const before = inspectDatabase()
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  let submissions = 0
  let successfulResponses = 0
  let submissionKeyDigest = ''
  let released = false
  function releaseGate() {
    if (!submissionKeyDigest || released) return
    const temporaryReleaseFile = `${releaseFile}.tmp`
    writeFileSync(temporaryReleaseFile, JSON.stringify({ submission_key_digest: submissionKeyDigest }))
    renameSync(temporaryReleaseFile, releaseFile)
    released = true
  }
  page.on('response', response => {
    if (response.url().endsWith('/api/comparisons') && response.request().method() === 'POST' && response.ok()) {
      successfulResponses += 1
    }
  })
  await page.route('**/api/comparisons', async route => {
    submissions += 1
    if (submissions === 1) {
      const submitted = route.request().postDataJSON()
      expect(submitted.text === example).toBe(true)
      expect(submitted.search_location).toEqual({ country_code: 'CH' })
      submissionKeyDigest = createHash('sha256').update(JSON.stringify(submitted.submission_key)).digest('hex')
      writeFileSync(controlFile, JSON.stringify({ submission_key_digest: submissionKeyDigest }))
    }
    await route.continue()
  })
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
      && response.request().method() === 'POST')
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    await expect.poll(() => existsSync(reachedFile), { timeout: 10000 }).toBe(true)
    const reached = JSON.parse(readFileSync(reachedFile, 'utf8'))
    expect(reached.stage).toBe('after_required_inserts_before_underlying_commit')
    expect(reached.transaction_active).toBe(true)
    expect(reached.transaction_rows).toEqual({ search_request: 1, request_alternative: 2, request_alternative_evidence: 2 })
    expect(reached.underlying_commit_calls).toBe(0)
    expect(reached.save_calls).toBe(1)
    expect(reached.independent_before).toEqual(before)
    expect(reached.independent_while_paused).toEqual(before)
    expect(reached.observer_rows_supplied_to_application).toBe(false)
    expect(existsSync(controlFile)).toBe(false)
    expect(existsSync(releaseFile)).toBe(false)
    await expect(page.getByRole('status')).toContainText('including saving. No result is confirmed yet.')
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'true')
    await expect(page.getByRole('button', { name: 'Processing…', exact: true })).toBeDisabled()
    for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
      await expect(page.getByLabel(label, { exact: true })).toBeDisabled()
    }
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('alert')).not.toBeVisible()
    expect(successfulResponses).toBe(0)
    expect(submissions).toBe(1)
    const during = inspectDatabase()
    expect(during).toEqual(before)
    expect(existsSync(releaseFile)).toBe(false)
    releaseGate()

    const response = await responsePromise
    expect(response.status()).toBe(201)
    const saved = await response.json()
    expect(saved.outcome).toBe('comparison')
    expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    await expect.poll(() => existsSync(gateEvidenceFile), { timeout: 10000 }).toBe(true)
    const gate = JSON.parse(readFileSync(gateEvidenceFile, 'utf8'))
    expect(gate.underlying_commit_calls).toBe(1)
    expect(gate.save_calls).toBe(1)
    expect(gate.release_received).toBe(true)
    expect(gate.dialect_method_restored).toBe(true)
    expect(gate.store_save_hook_restored).toBe(true)
    expect(gate.observer_rows_supplied_to_application).toBe(false)
    const after = inspectDatabase()
    expect(after.counts).toEqual({
      search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2,
    })
    const addedRequests = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(reached.request_id)
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(addedRequest.projection).toEqual(saved)
    expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(after.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(after.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(after.snapshots.evidence).toEqual(before.snapshots.evidence)
    expect(gate.independent_after).toEqual(after)
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).toBeVisible()
    await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
    await expect(page.getByTestId('saved-option')).toHaveCount(2)
    for (const [index, option] of saved.comparison.options.entries()) {
      await expect(page.getByTestId('saved-option').nth(index)).toHaveAttribute('data-option-id', option.option_id)
    }
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByRole('alert')).not.toBeVisible()
    for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
      await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
    }
    expect(successfulResponses).toBe(1)
    expect(submissions).toBe(1)
    const evidencePath = testInfo.outputPath('delayed-required-save-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before, during, after, saved_response: { status: response.status(), body: saved },
      added_request_id: addedRequest.id, baseline_was_nonempty: before.counts.search_request > 0,
      browser_submissions: submissions, successful_responses_while_closed: 0, successful_responses_after_release: successfulResponses,
      loading_and_controls_busy_before_commit: true, no_saved_presentation_before_commit: true,
      prior_records_and_source_evidence_preserved: true, gate_reached: reached,
      gate: { save_calls: gate.save_calls, underlying_commit_calls: gate.underlying_commit_calls,
        release_received: gate.release_received, dialect_method_restored: gate.dialect_method_restored,
        store_save_hook_restored: gate.store_save_hook_restored, timeline: gate.timeline,
        observer_rows_supplied_to_application: gate.observer_rows_supplied_to_application },
      no_http_delivery_gate: true, raw_originating_proofs_or_complete_requests_recorded: false }, null, 2))
    await testInfo.attach('delayed-required-save-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    releaseGate()
    if (submissionKeyDigest) {
      await expect.poll(() => existsSync(gateEvidenceFile), { timeout: 10000 }).toBe(true)
    }
  }
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

test('delivered unknown persistence error requires explicit same-submission recovery', async ({ page }, testInfo) => {
  const controlFile = process.env.RESOLENA_TEST_UNCERTAIN_SAVE_FILE!
  expect(Boolean(controlFile)).toBe(true)
  expect(existsSync(controlFile)).toBe(false)
  const faultEvidenceFile = controlFile.replace(/\.json$/, '.evidence.json')
  const before = inspectDatabase()
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  const attempts: ReturnType<typeof captureAttempt>[] = []
  let releaseError!: () => void
  const errorGate = new Promise<void>(resolve => { releaseError = resolve })
  type Capture = { status: number; body: any; stored: ReturnType<typeof inspectDatabase> }
  let captureError!: (value: Capture) => void
  const backendError = new Promise<Capture>(resolve => { captureError = resolve })
  await page.route('**/api/comparisons', async route => {
    attempts.push(captureAttempt(route.request()))
    if (attempts.length === 1) {
      const key = JSON.parse(attempts[0].body).submission_key
      writeFileSync(controlFile, JSON.stringify({ submission_key_digest: createHash('sha256').update(JSON.stringify(key)).digest('hex') }))
      const response = await route.fetch({ maxRetries: 0 })
      captureError({ status: response.status(), body: await response.json(), stored: inspectDatabase() })
      await errorGate
      await route.fulfill({ response })
    } else {
      await route.continue()
    }
  })
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const delivered = await backendError
    expect(delivered.status).toBe(503)
    expect(delivered.body).toEqual({ outcome: 'persistence_error', persistence: { state: 'unknown' },
      issues: [{ code: 'comparison_save_failed' }], assessed_outcome: 'comparison' })
    const stored = delivered.stored
    expect(stored.counts).toEqual({
      search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2,
    })
    const addedRequests = stored.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    const saved = addedRequest.projection
    expect(stored.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(stored.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(stored.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(saved.outcome).toBe('comparison')
    expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(stored.snapshots.evidence).toEqual(before.snapshots.evidence)
    expect(existsSync(controlFile)).toBe(false)
    const fault = JSON.parse(readFileSync(faultEvidenceFile, 'utf8'))
    expect(fault.fault_counts).toEqual({ real_commits: 1, confirmation_losses: 1, read_failures: 1 })
    expect(fault.independent_after_commit).toEqual(stored)
    expect(fault.after_fault).toEqual(stored)
    expect(fault.dialect_methods_restored).toBe(true)
    expect(fault.observer_rows_supplied_to_application).toBe(false)
    await expect(page.getByRole('status')).toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'true')
    await expect(page.getByRole('button', { name: 'Processing…' })).toBeDisabled()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('alert')).not.toBeVisible()
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    releaseError()
    const errorResponse = await responsePromise
    expect(errorResponse.status()).toBe(delivered.status)
    expect(await errorResponse.json()).toEqual(delivered.body)
    await expect(page.getByRole('alert')).toContainText('Saving could not be confirmed')
    await expect(page.getByRole('alert')).toContainText('may already be saved')
    await expect(page.getByRole('alert')).not.toContainText('could not be saved')
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByText('Existing knowledge could not support', { exact: false })).not.toBeVisible()
    await expect(page.getByRole('button', { name: 'Recover submission' })).toBeEnabled()
    await expect(page.getByRole('button', { name: 'Start a fresh search' })).toBeEnabled()
    await page.waitForTimeout(300)
    expect(attempts.length).toBe(1)
    expect(inspectDatabase()).toEqual(stored)

    const recoveryResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Recover submission' }).click()
    const response = await recoveryResponse
    expect(response.status()).toBe(200)
    const acknowledgement = await response.json()
    expect(acknowledgement).toEqual({ outcome: 'submission_recovered', persistence: saved.persistence,
      saved_outcome: 'comparison', assessed_at: saved.assessed_at })
    expect(attempts.length).toBe(2)
    expect(attempts[1].body === attempts[0].body).toBe(true)
    expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
    const acknowledged = page.getByRole('region', { name: 'Saved submission acknowledged' })
    await expect(acknowledged).toContainText(saved.persistence.request_id)
    await expect(acknowledged).toContainText('Original outcome: comparison')
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
    const evidencePath = testInfo.outputPath('delivered-unknown-recovery-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before, committed: stored, recovered: after, fault,
      added_request_id: addedRequest.id, new_identity_selected_by_baseline_difference: true,
      preexisting_records_and_source_evidence_preserved: true,
      runner_control: { path: controlFile, initially_absent: true, consumed_after_error: true },
      error_response: { status: errorResponse.status(), body: delivered.body },
      recovery_response: { status: response.status(), body: acknowledgement },
      browser_submissions: attempts.length, same_serialized_body_key_and_proof: true,
      loading_held_until_actual_error_delivered: true, fields_preserved_after_error_and_recovery: true,
      no_comparison_or_coverage_presented: true, no_automatic_retry_observed_ms: 300,
      fresh_search_action_unchanged_and_not_exercised: true, raw_originating_proofs_recorded: false }, null, 2))
    await testInfo.attach('delivered-unknown-recovery-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    releaseError()
  }
})

test('unavailable locality requires explicit country-only continuation before saving', async ({ page }, testInfo) => {
  const before = inspectDatabase()
  const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  const attempts: ReturnType<typeof captureAttempt>[] = []
  let releaseSaved!: () => void
  const savedGate = new Promise<void>(resolve => { releaseSaved = resolve })
  type Capture = { status: number; body: any; stored: ReturnType<typeof inspectDatabase> }
  let captureSaved!: (value: Capture) => void
  const committed = new Promise<Capture>(resolve => { captureSaved = resolve })
  await page.route('**/api/comparisons', async route => {
    attempts.push(captureAttempt(route.request()))
    const response = await route.fetch({ maxRetries: 0 })
    if (attempts.length === 2) {
      captureSaved({ status: response.status(), body: await response.json(), stored: inspectDatabase() })
      await savedGate
    }
    await route.fulfill({ response })
  })
  try {
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await expect(page.getByLabel('Town (optional)', { exact: true })).toBeVisible({ timeout: 3000 })
    await page.getByLabel('Town (optional)', { exact: true }).fill('Synthetic optional town')
    await page.getByLabel('Postcode (optional)', { exact: true }).fill('0123')
    const clarificationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const clarification = await clarificationResponse
    expect(clarification.status()).toBe(200)
    const clarificationBody = await clarification.json()
    expect(clarificationBody.outcome).toBe('clarification_required')
    expect(clarificationBody.persistence).toEqual({ state: 'not_attempted' })
    expect(clarificationBody.issues).toEqual([{ code: 'locality_reference_unavailable' }])
    await expect(page.getByRole('region', { name: 'Clarification' })).toContainText('cannot currently be verified')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('Synthetic optional town')
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('0123')
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).not.toBeVisible()
    await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
    expect(inspectDatabase()).toEqual(before)
    await page.waitForTimeout(300)
    expect(attempts.length).toBe(1)
    expect(inspectDatabase()).toEqual(before)

    const savedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Continue with country only', exact: true }).click()
    const saved = await committed
    expect(saved.status).toBe(201)
    expect(saved.body.outcome).toBe('comparison')
    expect(saved.stored.counts).toEqual({
      search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2,
    })
    const addedRequests = saved.stored.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(saved.body.persistence.request_id)
    expect(addedRequest.projection).toEqual(saved.body)
    expect(saved.stored.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(saved.stored.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(saved.stored.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(saved.stored.snapshots.evidence).toEqual(before.snapshots.evidence)
    expect(attempts.length).toBe(2)
    const original = JSON.parse(attempts[0].body)
    const continuation = JSON.parse(attempts[1].body)
    expect(original.search_location).toEqual({ country_code: 'CH', town: 'Synthetic optional town', postcode: '0123' })
    expect(original.location_choice).toBe('provided')
    expect(continuation.search_location).toEqual({ country_code: 'CH' })
    expect(continuation.location_choice).toBe('country_only')
    expect(continuation.text === original.text && continuation.text === example).toBe(true)
    expect(continuation.language_context).toEqual(original.language_context)
    expect(continuation.submission_key !== original.submission_key).toBe(true)
    expect(attempts[1].proofDigest !== attempts[0].proofDigest).toBe(true)
    const storedRequest = JSON.parse(execFileSync(python, ['-c', `
import json,sqlite3,sys
with sqlite3.connect(sys.argv[1]) as connection:
    row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context,assessed_at,outcome FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
    print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
        'location_choice':row[3],'language_context':json.loads(row[4]),'assessed_at':row[5],'outcome':row[6]}))
`, database, addedRequest.id], { encoding: 'utf8' }))
    expect(storedRequest.original_text).toBe(example)
    expect(storedRequest.search_location).toEqual({ country_code: 'CH' })
    expect(storedRequest.location_choice).toBe('country_only')
    expect(storedRequest.language_context).toEqual(original.language_context)
    expect(storedRequest.interpretation.constraints).toEqual([{ value: 'no_replacement', quote: 'without replacing it' }])
    expect(storedRequest.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    await expect(page.getByRole('status')).toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByText('Search scope: country only (CH).', { exact: true })).toBeVisible()
    releaseSaved()
    const delivered = await savedResponse
    expect(delivered.status()).toBe(201)
    expect(await delivered.json()).toEqual(saved.body)
    await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
    await expect(page.getByTestId('saved-option')).toHaveCount(2)
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    expect(inspectDatabase()).toEqual(saved.stored)
    const evidencePath = testInfo.outputPath('country-only-continuation-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({ before, clarification_response: { status: clarification.status(), body: clarificationBody },
      clarification_saved_no_search: true, fields_retained_until_explicit_choice: true, bounded_no_automatic_continuation_ms: 300,
      committed: saved.stored, saved_request_id: addedRequest.id, saved_request: storedRequest,
      saved_response: { status: delivered.status(), body: saved.body }, browser_submissions: attempts.length,
      explicit_choice_uses_new_key_and_proof: true, original_text_country_language_preserved: true,
      prior_records_and_source_evidence_preserved: true, saved_before_presentation: true,
      delayed_save_t12_exercised: false, raw_originating_proofs_recorded: false }, null, 2))
    await testInfo.attach('country-only-continuation-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    releaseSaved()
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

test('real SQLite write failure preserves fields and never presents a completed comparison', async ({ page }, testInfo) => {
  const clockFile = process.env.RESOLENA_E2E_CLOCK_FILE!
  const clockBefore = readFileSync(clockFile)
  expect(JSON.parse(clockBefore.toString()).now).toBe('2026-10-15T10:00:00+00:00')
  const before = inspectDatabase('fail')
  let triggerInstalled = true
  try {
    const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
    const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
    const attempts: ReturnType<typeof captureAttempt>[] = []
    await page.route('**/api/comparisons', async route => {
      attempts.push(captureAttempt(route.request()))
      await route.continue()
    })
    await page.goto('/')
    await page.getByLabel('Describe your request').fill(example)
    await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
    await page.getByRole('button', { name: 'Find alternatives' }).click()
    const response = await responsePromise
    expect(response.status()).toBe(503)
    expect((await response.json()).persistence.state).toBe('failed')
    const failedBody = await response.json()
    expect(failedBody).toEqual({ outcome: 'persistence_error', persistence: { state: 'failed' },
      issues: [{ code: 'comparison_save_failed' }], assessed_outcome: 'comparison' })
    await expect(page.getByRole('alert')).toContainText('The comparison could not be saved')
    await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
    await expect(page.getByTestId('saved-option')).toHaveCount(0)
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    await expect(page.getByRole('button', { name: 'Try again' })).toBeEnabled()
    expect(inspectDatabase().counts).toEqual(before.counts)
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
    await expect(page.getByRole('alert')).not.toContainText('unknown')
    await expect(page.getByRole('alert')).not.toContainText('could not be confirmed')
    await expect(page.getByText('An earlier submission may already be saved.', { exact: false })).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
      await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
    }
    const afterFailure = inspectDatabase()
    expect(afterFailure).toEqual(before)
    expect(readFileSync(clockFile).equals(clockBefore)).toBe(true)
    await page.waitForTimeout(300)
    expect(attempts.length).toBe(1)
    expect(inspectDatabase()).toEqual(before)

    const afterTriggerRemoval = inspectDatabase('restore')
    triggerInstalled = false
    expect(afterTriggerRemoval).toEqual(before)
    const retryResponse = page.waitForResponse(reply => reply.url().endsWith('/api/comparisons')
      && reply.request().method() === 'POST')
    await page.getByRole('button', { name: 'Try again', exact: true }).click()
    const retry = await retryResponse
    expect(retry.status()).toBe(201)
    const saved = await retry.json()
    expect(saved.outcome).toBe('comparison')
    expect(saved.persistence.state).toBe('saved')
    expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
    expect(attempts.length).toBe(2)
    const initialPayload = JSON.parse(attempts[0].body)
    const retriedPayload = JSON.parse(attempts[1].body)
    expect(attempts[1].body === attempts[0].body).toBe(true)
    expect(retriedPayload.submission_key === initialPayload.submission_key).toBe(true)
    expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
    expect(retriedPayload.text === example && retriedPayload.text === initialPayload.text).toBe(true)
    expect(JSON.stringify(retriedPayload.search_location) === JSON.stringify({ country_code: 'CH' })).toBe(true)
    expect(JSON.stringify(retriedPayload.language_context) === JSON.stringify(initialPayload.language_context)).toBe(true)
    const afterRetry = inspectDatabase()
    expect(afterRetry.counts).toEqual({ search_request: before.counts.search_request + 1,
      request_alternative: before.counts.request_alternative + 2,
      request_alternative_evidence: before.counts.request_alternative_evidence + 2 })
    const addedRequests = afterRetry.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
    expect(addedRequests.length).toBe(1)
    const addedRequest = addedRequests[0]
    expect(addedRequest.id).toBe(saved.persistence.request_id)
    expect(addedRequest.projection).toEqual(saved)
    expect(afterRetry.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
    expect(afterRetry.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative)
    expect(afterRetry.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
      .toEqual(before.snapshots.request_alternative_evidence)
    expect(afterRetry.snapshots.evidence).toEqual(before.snapshots.evidence)
    expect(readFileSync(clockFile).equals(clockBefore)).toBe(true)
    await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).toBeVisible()
    await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
    await expect(page.getByTestId('saved-option')).toHaveCount(2)
    for (const [index, option] of saved.comparison.options.entries()) {
      const shown = page.getByTestId('saved-option').nth(index)
      await expect(shown).toHaveAttribute('data-option-id', option.option_id)
      await expect(shown.getByRole('heading')).toHaveText(option.display_name)
    }
    await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
    await expect(page.getByRole('alert')).not.toBeVisible()
    await expect(page.getByRole('status')).not.toBeVisible()
    await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
    await expect(page.getByLabel('Describe your request')).toHaveValue(example)
    await expect(page.getByLabel('Search country')).toHaveValue('CH')
    for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
      await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
    }
    expect(attempts.length).toBe(2)
    const evidencePath = testInfo.outputPath('confirmed-write-failure-retry-evidence.json')
    writeFileSync(evidencePath, JSON.stringify({
      scope: 'Extension of the existing real SQLite write-failure scenario with clicked unchanged-submission retry.',
      before, after_failure: afterFailure, after_trigger_removal: afterTriggerRemoval, after_retry: afterRetry,
      failed_response: { status: response.status(), body: failedBody }, retry_response: { status: retry.status(), body: saved },
      saved_request_id: addedRequest.id, baseline_was_nonempty: before.counts.search_request > 0,
      browser_submissions: attempts.length, bounded_no_automatic_retry_ms: 300,
      same_serialized_body_key_proof_and_language_context: true, explicit_try_again_clicked_without_edits: true,
      failed_save_message_fields_loading_and_controls_verified: true, no_uncertainty_or_saved_presentation_after_failure: true,
      prior_records_options_links_source_evidence_and_review_dates_preserved: true,
      clock_bytes_unchanged: true, owned_trigger_removed_before_retry: !triggerInstalled,
      raw_keys_proofs_digests_headers_bindings_or_complete_requests_recorded: false,
    }, null, 2))
    await testInfo.attach('confirmed-write-failure-retry-evidence', { path: evidencePath, contentType: 'application/json' })
  } finally {
    if (triggerInstalled) inspectDatabase('restore')
  }
})

test('changed-country request saves coverage without invented matches or global absence claims', async ({ page }) => {
  const before = inspectDatabase()
  await page.goto('/')
  await page.getByLabel('Describe your request').fill(example)
  await page.getByLabel('Search country').selectOption('DE')
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
    await page.getByLabel('Search country').selectOption('DE')
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
