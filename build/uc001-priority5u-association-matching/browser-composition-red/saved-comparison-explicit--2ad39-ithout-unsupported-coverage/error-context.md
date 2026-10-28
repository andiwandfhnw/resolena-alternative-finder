# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> explicit locality confirmation saves reference-unverified intent without unsupported coverage
- Location: ../tests/e2e/saved-comparison.spec.ts:248:5

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 1

  Array [
    Object {
-     "code": "locality_reference_unavailable",
+     "code": "locality_reference_unknown",
    },
  ]
```

# Page snapshot

```yaml
- main [ref=e3]:
  - generic [ref=e4]:
    - paragraph [ref=e5]: Resolena Alternative Finder
    - heading "Explore practical alternatives" [level=1] [ref=e6]
    - complementary [ref=e7]:
      - strong [ref=e8]: Development demonstration
      - paragraph [ref=e9]: Approved country reference; interpretation and alternative evidence remain synthetic.
      - paragraph [ref=e10]:
        - text: "CH/LI reference source:"
        - link "Federal Office of Topography swisstopo" [ref=e11] [cursor=pointer]:
          - /url: https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities
        - text: . The approved association reference is used only when configured in this development composition; reference matches do not establish delivery or service coverage.
      - paragraph [ref=e12]: Test-only interpreter and evidence. No real providers, multilingual support or verified savings.
      - paragraph [ref=e13]: Use “Repair my bicycle without replacing it” with CH for a comparison or DE for a synthetic coverage limitation.
      - paragraph [ref=e14]: “Velo” exercises explanation-language preferences. Only English synthetic rendering is configured.
      - paragraph [ref=e15]: “Synthetic hourly bicycle repair” exercises source-bound test wording in DE/FR/IT/EN. “Synthetic pending bicycle repair” exercises a missing-review limitation. These fixtures do not verify linguistic fidelity.
      - paragraph [ref=e16]:
        - text: Country code/name data derived from GeoNames countryInfo.
        - link "GeoNames" [ref=e17] [cursor=pointer]:
          - /url: https://download.geonames.org/export/dump/countryInfo.txt
        - text: ;
        - link "CC BY 4.0" [ref=e18] [cursor=pointer]:
          - /url: https://creativecommons.org/licenses/by/4.0/
        - text: . Selected ISO/Country fields, sorted codes, excluded AN/CS and included XK under the owner's 2026-10-23 source-based policy. Source names unchanged. No endorsement is implied.
  - generic [ref=e19]:
    - generic [ref=e20]: Describe your request
    - textbox "Describe your request" [ref=e21]: Repair my bicycle without replacing it
    - generic [ref=e22]: Search country
    - combobox "Search country" [ref=e23]:
      - option "Choose a search country"
      - option "AD — Andorra"
      - option "AE — United Arab Emirates"
      - option "AF — Afghanistan"
      - option "AG — Antigua and Barbuda"
      - option "AI — Anguilla"
      - option "AL — Albania"
      - option "AM — Armenia"
      - option "AO — Angola"
      - option "AQ — Antarctica"
      - option "AR — Argentina"
      - option "AS — American Samoa"
      - option "AT — Austria"
      - option "AU — Australia"
      - option "AW — Aruba"
      - option "AX — Aland Islands"
      - option "AZ — Azerbaijan"
      - option "BA — Bosnia and Herzegovina"
      - option "BB — Barbados"
      - option "BD — Bangladesh"
      - option "BE — Belgium"
      - option "BF — Burkina Faso"
      - option "BG — Bulgaria"
      - option "BH — Bahrain"
      - option "BI — Burundi"
      - option "BJ — Benin"
      - option "BL — Saint Barthelemy"
      - option "BM — Bermuda"
      - option "BN — Brunei"
      - option "BO — Bolivia"
      - option "BQ — Bonaire, Saint Eustatius and Saba"
      - option "BR — Brazil"
      - option "BS — Bahamas"
      - option "BT — Bhutan"
      - option "BV — Bouvet Island"
      - option "BW — Botswana"
      - option "BY — Belarus"
      - option "BZ — Belize"
      - option "CA — Canada"
      - option "CC — Cocos Islands"
      - option "CD — Democratic Republic of the Congo"
      - option "CF — Central African Republic"
      - option "CG — Republic of the Congo"
      - option "CH — Switzerland" [selected]
      - option "CI — Ivory Coast"
      - option "CK — Cook Islands"
      - option "CL — Chile"
      - option "CM — Cameroon"
      - option "CN — China"
      - option "CO — Colombia"
      - option "CR — Costa Rica"
      - option "CU — Cuba"
      - option "CV — Cabo Verde"
      - option "CW — Curacao"
      - option "CX — Christmas Island"
      - option "CY — Cyprus"
      - option "CZ — Czechia"
      - option "DE — Germany"
      - option "DJ — Djibouti"
      - option "DK — Denmark"
      - option "DM — Dominica"
      - option "DO — Dominican Republic"
      - option "DZ — Algeria"
      - option "EC — Ecuador"
      - option "EE — Estonia"
      - option "EG — Egypt"
      - option "EH — Western Sahara"
      - option "ER — Eritrea"
      - option "ES — Spain"
      - option "ET — Ethiopia"
      - option "FI — Finland"
      - option "FJ — Fiji"
      - option "FK — Falkland Islands"
      - option "FM — Micronesia"
      - option "FO — Faroe Islands"
      - option "FR — France"
      - option "GA — Gabon"
      - option "GB — United Kingdom"
      - option "GD — Grenada"
      - option "GE — Georgia"
      - option "GF — French Guiana"
      - option "GG — Guernsey"
      - option "GH — Ghana"
      - option "GI — Gibraltar"
      - option "GL — Greenland"
      - option "GM — Gambia"
      - option "GN — Guinea"
      - option "GP — Guadeloupe"
      - option "GQ — Equatorial Guinea"
      - option "GR — Greece"
      - option "GS — South Georgia and the South Sandwich Islands"
      - option "GT — Guatemala"
      - option "GU — Guam"
      - option "GW — Guinea-Bissau"
      - option "GY — Guyana"
      - option "HK — Hong Kong"
      - option "HM — Heard Island and McDonald Islands"
      - option "HN — Honduras"
      - option "HR — Croatia"
      - option "HT — Haiti"
      - option "HU — Hungary"
      - option "ID — Indonesia"
      - option "IE — Ireland"
      - option "IL — Israel"
      - option "IM — Isle of Man"
      - option "IN — India"
      - option "IO — British Indian Ocean Territory"
      - option "IQ — Iraq"
      - option "IR — Iran"
      - option "IS — Iceland"
      - option "IT — Italy"
      - option "JE — Jersey"
      - option "JM — Jamaica"
      - option "JO — Jordan"
      - option "JP — Japan"
      - option "KE — Kenya"
      - option "KG — Kyrgyzstan"
      - option "KH — Cambodia"
      - option "KI — Kiribati"
      - option "KM — Comoros"
      - option "KN — Saint Kitts and Nevis"
      - option "KP — North Korea"
      - option "KR — South Korea"
      - option "KW — Kuwait"
      - option "KY — Cayman Islands"
      - option "KZ — Kazakhstan"
      - option "LA — Laos"
      - option "LB — Lebanon"
      - option "LC — Saint Lucia"
      - option "LI — Liechtenstein"
      - option "LK — Sri Lanka"
      - option "LR — Liberia"
      - option "LS — Lesotho"
      - option "LT — Lithuania"
      - option "LU — Luxembourg"
      - option "LV — Latvia"
      - option "LY — Libya"
      - option "MA — Morocco"
      - option "MC — Monaco"
      - option "MD — Moldova"
      - option "ME — Montenegro"
      - option "MF — Saint Martin"
      - option "MG — Madagascar"
      - option "MH — Marshall Islands"
      - option "MK — North Macedonia"
      - option "ML — Mali"
      - option "MM — Myanmar"
      - option "MN — Mongolia"
      - option "MO — Macao"
      - option "MP — Northern Mariana Islands"
      - option "MQ — Martinique"
      - option "MR — Mauritania"
      - option "MS — Montserrat"
      - option "MT — Malta"
      - option "MU — Mauritius"
      - option "MV — Maldives"
      - option "MW — Malawi"
      - option "MX — Mexico"
      - option "MY — Malaysia"
      - option "MZ — Mozambique"
      - option "NA — Namibia"
      - option "NC — New Caledonia"
      - option "NE — Niger"
      - option "NF — Norfolk Island"
      - option "NG — Nigeria"
      - option "NI — Nicaragua"
      - option "NL — The Netherlands"
      - option "NO — Norway"
      - option "NP — Nepal"
      - option "NR — Nauru"
      - option "NU — Niue"
      - option "NZ — New Zealand"
      - option "OM — Oman"
      - option "PA — Panama"
      - option "PE — Peru"
      - option "PF — French Polynesia"
      - option "PG — Papua New Guinea"
      - option "PH — Philippines"
      - option "PK — Pakistan"
      - option "PL — Poland"
      - option "PM — Saint Pierre and Miquelon"
      - option "PN — Pitcairn"
      - option "PR — Puerto Rico"
      - option "PS — Palestinian Territory"
      - option "PT — Portugal"
      - option "PW — Palau"
      - option "PY — Paraguay"
      - option "QA — Qatar"
      - option "RE — Reunion"
      - option "RO — Romania"
      - option "RS — Serbia"
      - option "RU — Russia"
      - option "RW — Rwanda"
      - option "SA — Saudi Arabia"
      - option "SB — Solomon Islands"
      - option "SC — Seychelles"
      - option "SD — Sudan"
      - option "SE — Sweden"
      - option "SG — Singapore"
      - option "SH — Saint Helena"
      - option "SI — Slovenia"
      - option "SJ — Svalbard and Jan Mayen"
      - option "SK — Slovakia"
      - option "SL — Sierra Leone"
      - option "SM — San Marino"
      - option "SN — Senegal"
      - option "SO — Somalia"
      - option "SR — Suriname"
      - option "SS — South Sudan"
      - option "ST — Sao Tome and Principe"
      - option "SV — El Salvador"
      - option "SX — Sint Maarten"
      - option "SY — Syria"
      - option "SZ — Eswatini"
      - option "TC — Turks and Caicos Islands"
      - option "TD — Chad"
      - option "TF — French Southern Territories"
      - option "TG — Togo"
      - option "TH — Thailand"
      - option "TJ — Tajikistan"
      - option "TK — Tokelau"
      - option "TL — Timor Leste"
      - option "TM — Turkmenistan"
      - option "TN — Tunisia"
      - option "TO — Tonga"
      - option "TR — Turkey"
      - option "TT — Trinidad and Tobago"
      - option "TV — Tuvalu"
      - option "TW — Taiwan"
      - option "TZ — Tanzania"
      - option "UA — Ukraine"
      - option "UG — Uganda"
      - option "UM — United States Minor Outlying Islands"
      - option "US — United States"
      - option "UY — Uruguay"
      - option "UZ — Uzbekistan"
      - option "VA — Vatican"
      - option "VC — Saint Vincent and the Grenadines"
      - option "VE — Venezuela"
      - option "VG — British Virgin Islands"
      - option "VI — U.S. Virgin Islands"
      - option "VN — Vietnam"
      - option "VU — Vanuatu"
      - option "WF — Wallis and Futuna"
      - option "WS — Samoa"
      - option "XK — Kosovo"
      - option "YE — Yemen"
      - option "YT — Mayotte"
      - option "ZA — South Africa"
      - option "ZM — Zambia"
      - option "ZW — Zimbabwe"
    - paragraph [ref=e24]: CH — Switzerland is the editable default, not a detected location.
    - generic [ref=e25]: Town (optional)
    - textbox "Town (optional)" [ref=e26]: Synthetic optional town
    - generic [ref=e27]: Postcode (optional)
    - textbox "Postcode (optional)" [ref=e28]: "0123"
    - generic [ref=e29]:
      - button "Try again" [ref=e30] [cursor=pointer]
      - button "Continue with country only" [ref=e31] [cursor=pointer]
      - button "Confirm entered locality as intended scope" [ref=e32] [cursor=pointer]
      - button "Start a fresh search" [ref=e33] [cursor=pointer]
  - alert [ref=e34]: Clarification is required before knowledge can be assessed. Your fields are preserved.
  - region "Clarification" [ref=e35]:
    - paragraph [ref=e36]: No association matches all entered fields within this reference's CH/LI coverage. This is not proof that the entered locality is invalid. Correct the fields, explicitly continue country-only, or confirm the entered locality as intended scope. Confirmation establishes intended scope only; it does not establish delivery or service coverage.
    - paragraph [ref=e37]: Confirmation establishes intended scope only. The locality remains reference-unverified; it does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability.
```

# Test source

```ts
  171 |       && last.search_location.postcode === fixture.postcode).toBe(true)
  172 |     expect(JSON.stringify(last.language_context) === JSON.stringify(first.language_context)).toBe(true)
  173 |     if (fixture.selection === 'explicit') {
  174 |       expect(last.submission_key !== first.submission_key).toBe(true)
  175 |       expect(attempts.at(-1)!.proofDigest !== attempts[0].proofDigest).toBe(true)
  176 |       expect(JSON.stringify(last.search_location.reference) === JSON.stringify(expectedAssociation.reference)).toBe(true)
  177 |       expect(Object.keys(last.search_location.reference).sort()).toEqual(['release', 'source', 'source_record'])
  178 |     }
  179 |     const after = inspectDatabase()
  180 |     expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
  181 |       request_alternative: before.counts.request_alternative,
  182 |       request_alternative_evidence: before.counts.request_alternative_evidence })
  183 |     const added = after.rows.filter((row: { id: string }) => !priorIds.has(row.id))
  184 |     expect(added.length).toBe(1)
  185 |     expect(added[0].id).toBe(body.persistence.request_id)
  186 |     expect(added[0].projection).toEqual(body)
  187 |     expect(after.rows.filter((row: { id: string }) => priorIds.has(row.id))).toEqual(before.rows)
  188 |     expect(after.snapshots).toEqual(before.snapshots)
  189 |     const stored = JSON.parse(execFileSync(python, ['-c', `
  190 | import json,sqlite3,sys
  191 | with sqlite3.connect(sys.argv[1]) as connection:
  192 |     row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  193 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
  194 |         'location_choice':row[3],'language_context':json.loads(row[4])}))
  195 | `, database, added[0].id], { encoding: 'utf8' }))
  196 |     expect(stored.original_text === example && stored.location_choice === 'provided').toBe(true)
  197 |     expect(stored.search_location).toEqual(expectedScope)
  198 |     expect(JSON.stringify(stored.language_context) === JSON.stringify(first.language_context)).toBe(true)
  199 |     expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement'
  200 |       && item.quote === 'without replacing it')).toBe(true)
  201 |     const span = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint'
  202 |       && item.normalized === 'no_replacement').span
  203 |     expect(span.start === 18 && span.end === 38 && span.quote === 'without replacing it').toBe(true)
  204 |     const localityReference = stored.interpretation.provenance.reference_versions.locality
  205 |     expect(localityReference.release).toBe(release)
  206 |     expect(localityReference.sha256).toBe('eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9')
  207 |     await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  208 |     await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  209 |     const shownScope = page.getByRole('region', { name: 'Matched reference association', exact: true })
  210 |     await expect(shownScope).toContainText('Matched in this reference; delivery and service coverage are not established.')
  211 |     await expect(shownScope).toContainText(expectedAssociation.locality_name)
  212 |     await expect(shownScope).toContainText(expectedAssociation.postcode)
  213 |     await expect(shownScope).toContainText(expectedAssociation.administrative.municipality_name)
  214 |     await expect(shownScope).toContainText(expectedAssociation.administrative.canton)
  215 |     await expect(shownScope).toContainText(release)
  216 |     if (fixture.selection === 'explicit') await expect(shownScope).not.toContainText('Ecublens (VD)')
  217 |     await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  218 |     await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
  219 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  220 |     await expect(page.getByRole('alert')).not.toBeVisible()
  221 |     await expect(page.getByRole('status')).not.toBeVisible()
  222 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  223 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(fixture.town)
  224 |     await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(fixture.postcode)
  225 |     await page.getByLabel('Town (optional)', { exact: true }).fill('Changed intended locality')
  226 |     await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  227 |     await expect(shownScope).not.toBeVisible()
  228 |     await expect(page.getByRole('combobox', { name: 'Reference association', exact: true })).not.toBeVisible()
  229 |     expect(attempts.length).toBe(fixture.selection === 'explicit' ? 2 : 1)
  230 |     expect(inspectDatabase()).toEqual(after)
  231 |     const evidencePath = testInfo.outputPath(`association-${fixture.selection}-evidence.json`)
  232 |     writeFileSync(evidencePath, JSON.stringify({ scope: 'Approved pinned association reference with synthetic request meaning and alternative evidence.',
  233 |       journey: fixture.selection, before, after_clarification: afterClarification, after,
  234 |       clarification_response: clarification, saved_response: { status: response.status(), body },
  235 |       saved_request_id: added[0].id, matched_association: expectedAssociation, locality_reference: localityReference,
  236 |       exact_raw_values_language_and_independent_requirement_span_preserved: true,
  237 |       no_save_during_unresolved_clarification_or_selection: fixture.selection === 'explicit' ? true : null,
  238 |       explicit_choice_uses_new_key_and_proof: fixture.selection === 'explicit' ? true : null,
  239 |       saved_scope_and_display_come_from_committed_projection: true,
  240 |       final_edit_sends_no_request_and_clears_selection_presentation: true,
  241 |       prior_records_options_links_source_versions_and_review_dates_preserved: true,
  242 |       browser_submissions: attempts.length,
  243 |       raw_keys_proofs_digests_headers_bindings_or_complete_captured_requests_recorded: false }, null, 2))
  244 |     await testInfo.attach(`association-${fixture.selection}-evidence`, { path: evidencePath, contentType: 'application/json' })
  245 |   })
  246 | }
  247 | 
  248 | test('explicit locality confirmation saves reference-unverified intent without unsupported coverage', async ({ page }, testInfo) => {
  249 |   const rawTown = '  Synthetic optional town  '
  250 |   const rawPostcode = ' 0123 '
  251 |   const before = inspectDatabase()
  252 |   expect(before.counts.search_request > 0).toBe(true)
  253 |   const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  254 |   const attempts: ReturnType<typeof captureAttempt>[] = []
  255 |   page.on('request', request => {
  256 |     if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
  257 |   })
  258 |   await page.goto('/')
  259 |   await page.getByLabel('Describe your request').fill(example)
  260 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  261 |   await page.getByLabel('Town (optional)', { exact: true }).fill(rawTown)
  262 |   await page.getByLabel('Postcode (optional)', { exact: true }).fill(rawPostcode)
  263 |   const clarificationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  264 |     && response.request().method() === 'POST')
  265 |   await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  266 |   const clarification = await clarificationResponse
  267 |   expect(clarification.status()).toBe(200)
  268 |   const clarificationBody = await clarification.json()
  269 |   expect(clarificationBody.outcome).toBe('clarification_required')
  270 |   expect(clarificationBody.persistence).toEqual({ state: 'not_attempted' })
> 271 |   expect(clarificationBody.issues).toEqual([{ code: 'locality_reference_unavailable' }])
      |                                    ^ Error: expect(received).toEqual(expected) // deep equality
  272 |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('cannot currently be verified')
  273 |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('Confirmation establishes intended scope only.')
  274 |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability')
  275 |   const confirm = page.getByRole('button', { name: 'Confirm entered locality as intended scope', exact: true })
  276 |   await expect(confirm).toBeEnabled()
  277 |   await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
  278 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  279 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  280 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(rawTown)
  281 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(rawPostcode)
  282 |   await expect(page.getByRole('status')).not.toBeVisible()
  283 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  284 |   for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
  285 |     await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  286 |   }
  287 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  288 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  289 |   expect(attempts.length).toBe(1)
  290 |   const afterClarification = inspectDatabase()
  291 |   expect(afterClarification).toEqual(before)
  292 |   const confirmationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  293 |     && response.request().method() === 'POST')
  294 |   await confirm.click()
  295 |   const response = await confirmationResponse
  296 |   expect(response.status()).toBe(201)
  297 |   const saved = await response.json()
  298 |   expect(saved.outcome).toBe('insufficient_coverage')
  299 |   expect(saved.persistence.state).toBe('saved')
  300 |   expect(saved.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  301 |   expect(saved.coverage.limitation_codes).toContain('geographic_applicability_unverified')
  302 |   const expectedScope = { country_code: 'CH', town: rawTown, postcode: rawPostcode,
  303 |     locality: { confirmation: 'user_confirmed', verification: 'reference_unverified',
  304 |       normalized: { town: 'synthetic optional town', postcode: '0123' } } }
  305 |   expect(saved.search_scope).toEqual(expectedScope)
  306 |   expect(attempts.length).toBe(2)
  307 |   const initial = JSON.parse(attempts[0].body)
  308 |   const confirmed = JSON.parse(attempts[1].body)
  309 |   expect(initial.location_choice === 'provided' && confirmed.location_choice === 'confirmed_unverified').toBe(true)
  310 |   expect(initial.submission_key !== confirmed.submission_key).toBe(true)
  311 |   expect(attempts[0].proofDigest !== attempts[1].proofDigest).toBe(true)
  312 |   expect(confirmed.text === initial.text && confirmed.text === example).toBe(true)
  313 |   expect(JSON.stringify(confirmed.search_location) === JSON.stringify(initial.search_location)).toBe(true)
  314 |   expect(JSON.stringify(confirmed.search_location) === JSON.stringify({ country_code: 'CH', town: rawTown, postcode: rawPostcode })).toBe(true)
  315 |   expect(JSON.stringify(confirmed.language_context) === JSON.stringify(initial.language_context)).toBe(true)
  316 |   const after = inspectDatabase()
  317 |   expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
  318 |     request_alternative: before.counts.request_alternative,
  319 |     request_alternative_evidence: before.counts.request_alternative_evidence })
  320 |   const added = after.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  321 |   expect(added.length).toBe(1)
  322 |   expect(added[0].id).toBe(saved.persistence.request_id)
  323 |   expect(added[0].projection).toEqual(saved)
  324 |   expect(after.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  325 |   expect(after.snapshots).toEqual(before.snapshots)
  326 |   const stored = JSON.parse(execFileSync(python, ['-c', `
  327 | import json,sqlite3,sys
  328 | with sqlite3.connect(sys.argv[1]) as connection:
  329 |     row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  330 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
  331 |         'location_choice':row[3],'language_context':json.loads(row[4])}))
  332 | `, database, added[0].id], { encoding: 'utf8' }))
  333 |   expect(stored.original_text === example).toBe(true)
  334 |   expect(stored.location_choice).toBe('confirmed_unverified')
  335 |   expect(stored.search_location).toEqual(expectedScope)
  336 |   expect(JSON.stringify(stored.language_context) === JSON.stringify(initial.language_context)).toBe(true)
  337 |   expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement' && item.quote === 'without replacing it')).toBe(true)
  338 |   const constraintSpan = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint' && item.normalized === 'no_replacement')
  339 |   expect(constraintSpan.span.start === 18 && constraintSpan.span.end === 38 && constraintSpan.span.quote === 'without replacing it').toBe(true)
  340 |   expect(stored.interpretation.provenance.reference_versions.country.release).toBe('geonames-countryInfo-2026-10-23-v1')
  341 |   await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  342 |   await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  343 |   const scope = page.getByRole('region', { name: 'Confirmed intended locality', exact: true })
  344 |   await expect(scope).toContainText('User-confirmed intended locality; reference-unverified.')
  345 |   await expect(scope).toContainText('does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability')
  346 |   await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  347 |   await expect(page.getByRole('heading', { name: 'Saved submission acknowledged', exact: true })).not.toBeVisible()
  348 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  349 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  350 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  351 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(rawTown)
  352 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(rawPostcode)
  353 |   await expect(page.getByRole('status')).not.toBeVisible()
  354 |   await expect(page.getByRole('alert')).not.toBeVisible()
  355 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  356 |   await page.getByLabel('Town (optional)', { exact: true }).fill('Changed synthetic town')
  357 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  358 |   await expect(scope).not.toBeVisible()
  359 |   await expect(confirm).not.toBeVisible()
  360 |   await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
  361 |   expect(attempts.length).toBe(2)
  362 |   expect(inspectDatabase()).toEqual(after)
  363 |   const evidencePath = testInfo.outputPath('confirmed-locality-evidence.json')
  364 |   writeFileSync(evidencePath, JSON.stringify({
  365 |     scope: 'One explicit O-1 locality-intent confirmation with real approved country reference and synthetic meaning/evidence.',
  366 |     expected_fixture_outcome: 'insufficient_coverage; ordinary in-CH support does not establish applicability for the entered locality',
  367 |     before, after_clarification: afterClarification, after,
  368 |     clarification_response: { status: clarification.status(), body: clarificationBody },
  369 |     confirmed_response: { status: response.status(), body: saved },
  370 |     saved_request_id: added[0].id, saved_scope: stored.search_location,
  371 |     country_reference: stored.interpretation.provenance.reference_versions.country,
```