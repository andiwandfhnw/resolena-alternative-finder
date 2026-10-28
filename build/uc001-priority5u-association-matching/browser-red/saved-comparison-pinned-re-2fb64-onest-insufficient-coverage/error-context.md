# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> pinned reference association single_match saves honest insufficient coverage
- Location: ../tests/e2e/saved-comparison.spec.ts:78:7

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 201
Received: 200
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
      - paragraph [ref=e10]: Test-only interpreter and evidence. No real providers, multilingual support or verified savings.
      - paragraph [ref=e11]: Use “Repair my bicycle without replacing it” with CH for a comparison or DE for a synthetic coverage limitation.
      - paragraph [ref=e12]: “Velo” exercises explanation-language preferences. Only English synthetic rendering is configured.
      - paragraph [ref=e13]: “Synthetic hourly bicycle repair” exercises source-bound test wording in DE/FR/IT/EN. “Synthetic pending bicycle repair” exercises a missing-review limitation. These fixtures do not verify linguistic fidelity.
      - paragraph [ref=e14]:
        - text: Country code/name data derived from GeoNames countryInfo.
        - link "GeoNames" [ref=e15] [cursor=pointer]:
          - /url: https://download.geonames.org/export/dump/countryInfo.txt
        - text: ;
        - link "CC BY 4.0" [ref=e16] [cursor=pointer]:
          - /url: https://creativecommons.org/licenses/by/4.0/
        - text: . Selected ISO/Country fields, sorted codes, excluded AN/CS and included XK under the owner's 2026-10-23 source-based policy. Source names unchanged. No endorsement is implied.
  - generic [ref=e17]:
    - generic [ref=e18]: Describe your request
    - textbox "Describe your request" [ref=e19]: Repair my bicycle without replacing it
    - generic [ref=e20]: Search country
    - combobox "Search country" [ref=e21]:
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
    - paragraph [ref=e22]: CH — Switzerland is the editable default, not a detected location.
    - generic [ref=e23]: Town (optional)
    - textbox "Town (optional)" [ref=e24]: jouxtens-mézery
    - generic [ref=e25]: Postcode (optional)
    - textbox "Postcode (optional)" [ref=e26]: "1008"
    - generic [ref=e27]:
      - button "Try again" [ref=e28] [cursor=pointer]
      - button "Continue with country only" [ref=e29] [cursor=pointer]
      - button "Confirm entered locality as intended scope" [ref=e30] [cursor=pointer]
      - button "Start a fresh search" [ref=e31] [cursor=pointer]
  - alert [ref=e32]: Clarification is required before knowledge can be assessed. Your fields are preserved.
  - region "Clarification" [ref=e33]:
    - paragraph [ref=e34]: The locality cannot currently be verified because locality reference data is unavailable. Correct the fields, explicitly continue country-only, or confirm the entered locality as intended scope. Confirmation establishes intended scope only. It does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability.
    - paragraph [ref=e35]: Confirmation establishes intended scope only. The locality remains reference-unverified; it does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability.
```

# Test source

```ts
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
  70  | for (const fixture of [
  71  |   { selection: 'single_match', town: '  jouxtens-me\u0301zery  ', postcode: ' 1008 ', normalizedTown: 'jouxtens-mézery',
  72  |     association: { source_record: 10, locality_name: 'Jouxtens-Mézery', postcode: '1008', source_postcode_id: '5852',
  73  |       additional_number: '02', administrative: { municipality_name: 'Jouxtens-Mézery', municipality_id: '5585', canton: 'VD' } } },
  74  |   { selection: 'explicit', town: 'Lausanne', postcode: '1015', normalizedTown: 'lausanne',
  75  |     association: { source_record: 16, locality_name: 'Lausanne', postcode: '1015', source_postcode_id: '163',
  76  |       additional_number: '00', administrative: { municipality_name: 'Saint-Sulpice (VD)', municipality_id: '5648', canton: 'VD' } } },
  77  | ] as const) {
  78  |   test(`pinned reference association ${fixture.selection} saves honest insufficient coverage`, async ({ page }, testInfo) => {
  79  |     const release = 'swisstopo-chli-associations-2026-10-01-v1'
  80  |     const { source_record: sourceRecord, ...associationFields } = fixture.association
  81  |     const expectedAssociation = { reference: { source: 'swisstopo', release, source_record: sourceRecord },
  82  |       country_code: 'CH', ...associationFields }
  83  |     const before = inspectDatabase()
  84  |     expect(before.counts.search_request > 0).toBe(true)
  85  |     const priorIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  86  |     const attempts: ReturnType<typeof captureAttempt>[] = []
  87  |     page.on('request', request => {
  88  |       if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
  89  |     })
  90  |     await page.goto('/')
  91  |     await page.getByLabel('Describe your request').fill(example)
  92  |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  93  |     await page.getByLabel('Town (optional)', { exact: true }).fill(fixture.town)
  94  |     await page.getByLabel('Postcode (optional)', { exact: true }).fill(fixture.postcode)
  95  |     const initialResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  96  |       && response.request().method() === 'POST')
  97  |     await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  98  |     let response = await initialResponse
  99  |     let body = await response.json()
  100 |     let clarification: { status: number; body: any } | null = null
  101 |     let afterClarification = before
  102 |     if (fixture.selection === 'explicit') {
  103 |       expect(response.status()).toBe(200)
  104 |       expect(body.outcome).toBe('clarification_required')
  105 |       expect(body.persistence).toEqual({ state: 'not_attempted' })
  106 |       expect(body.issues).toEqual([{ code: 'locality_reference_ambiguous' }])
  107 |       expect(body.clarification.choices).toEqual([])
  108 |       const expectedChoices = [
  109 |         { record: 15, municipality: 'Ecublens (VD)', municipalityId: '5635' },
  110 |         { record: 16, municipality: 'Saint-Sulpice (VD)', municipalityId: '5648' },
  111 |         { record: 17, municipality: 'Chavannes-près-Renens', municipalityId: '5627' },
  112 |       ].map(choice => ({ reference: { source: 'swisstopo', release, source_record: choice.record },
  113 |         country_code: 'CH', locality_name: 'Lausanne', postcode: '1015', source_postcode_id: '163',
  114 |         additional_number: '00', administrative: { municipality_name: choice.municipality,
  115 |           municipality_id: choice.municipalityId, canton: 'VD' } }))
  116 |       expect(body.clarification.associations).toEqual(expectedChoices)
  117 |       const associations = page.getByRole('combobox', { name: 'Reference association', exact: true })
  118 |       await expect(associations.locator('option')).toHaveCount(4)
  119 |       expect(await associations.locator('option').evaluateAll(options => options.map(option => (option as HTMLOptionElement).value)))
  120 |         .toEqual(['', '15', '16', '17'])
  121 |       for (const choice of expectedChoices) {
  122 |         const shownChoice = associations.locator(`option[value="${choice.reference.source_record}"]`)
  123 |         await expect(shownChoice).toContainText(choice.locality_name)
  124 |         await expect(shownChoice).toContainText(choice.postcode)
  125 |         await expect(shownChoice).toContainText(choice.administrative.municipality_name)
  126 |         await expect(shownChoice).toContainText(choice.administrative.canton)
  127 |       }
  128 |       await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText('associations')
  129 |       await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
  130 |       await expect(page.getByRole('button', { name: 'Confirm entered locality as intended scope', exact: true })).not.toBeVisible()
  131 |       await expect(page.getByLabel('Explanation language', { exact: true })).not.toBeVisible()
  132 |       await expect(page.getByRole('status')).not.toBeVisible()
  133 |       await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  134 |       await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).not.toBeVisible()
  135 |       await expect(page.getByTestId('saved-option')).toHaveCount(0)
  136 |       expect(attempts.length).toBe(1)
  137 |       afterClarification = inspectDatabase()
  138 |       expect(afterClarification).toEqual(before)
  139 |       const continueSelection = page.getByRole('button', { name: 'Continue with selected association', exact: true })
  140 |       await expect(continueSelection).toBeDisabled()
  141 |       await associations.selectOption('16')
  142 |       await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  143 |       await expect(continueSelection).toBeEnabled()
  144 |       expect(attempts.length).toBe(1)
  145 |       expect(inspectDatabase()).toEqual(before)
  146 |       await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  147 |       await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(fixture.town)
  148 |       await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue(fixture.postcode)
  149 |       clarification = { status: response.status(), body }
  150 |       const selectedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  151 |         && response.request().method() === 'POST')
  152 |       await continueSelection.click()
  153 |       response = await selectedResponse
  154 |       body = await response.json()
  155 |     }
> 156 |     expect(response.status()).toBe(201)
      |                               ^ Error: expect(received).toBe(expected) // Object.is equality
  157 |     expect(body.outcome).toBe('insufficient_coverage')
  158 |     expect(body.persistence.state).toBe('saved')
  159 |     expect(body.coverage.limitation_codes).toContain('geographic_applicability_unverified')
  160 |     const expectedScope = { country_code: 'CH', town: fixture.town, postcode: fixture.postcode,
  161 |       locality: { verification: 'matched_in_reference', selection: fixture.selection,
  162 |         normalized: { town: fixture.normalizedTown, postcode: fixture.postcode.trim() }, association: expectedAssociation } }
  163 |     expect(body.search_scope).toEqual(expectedScope)
  164 |     expect(attempts.length).toBe(fixture.selection === 'explicit' ? 2 : 1)
  165 |     const first = JSON.parse(attempts[0].body)
  166 |     const last = JSON.parse(attempts.at(-1)!.body)
  167 |     expect(first.location_choice === 'provided' && last.location_choice === 'provided').toBe(true)
  168 |     expect(!('reference' in first.search_location)).toBe(true)
  169 |     expect(last.text === first.text && last.text === example).toBe(true)
  170 |     expect(last.search_location.country_code === 'CH' && last.search_location.town === fixture.town
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
```