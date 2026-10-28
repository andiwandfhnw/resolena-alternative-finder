# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> malformed CH postcode requires correction before explicit saved assessment
- Location: ../tests/e2e/saved-comparison.spec.ts:85:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 422
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
    - textbox "Town (optional)" [ref=e26]: Jouxtens-Mézery
    - generic [ref=e27]: Postcode (optional)
    - textbox "Postcode (optional)" [ref=e28]: 10A8
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
  39  | test.beforeEach(({}, testInfo) => {
  40  |   const controlFile = process.env.RESOLENA_TEST_LOCALITY_REFERENCE_FILE!
  41  |   expect(Boolean(controlFile)).toBe(true)
  42  |   rmSync(controlFile, { force: true })
  43  |   if (['explicit locality confirmation saves reference-unverified intent without unsupported coverage',
  44  |     'unavailable locality requires explicit country-only continuation before saving'].includes(testInfo.title)) {
  45  |     writeFileSync(controlFile, JSON.stringify({ unavailable: true }))
  46  |   }
  47  | })
  48  | 
  49  | test.afterEach(() => {
  50  |   const controlFile = process.env.RESOLENA_TEST_LOCALITY_REFERENCE_FILE
  51  |   if (controlFile) rmSync(controlFile, { force: true })
  52  | })
  53  | 
  54  | test('browser displays exactly the committed API comparison and stable database identities', async ({ page }) => {
  55  |   await page.goto('/')
  56  |   await expect(page.getByText('Development demonstration', { exact: true })).toBeVisible()
  57  |   await page.getByLabel('Describe your request').fill(example)
  58  |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  59  |   const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons') && response.request().method() === 'POST')
  60  |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  61  |   const response = await responsePromise
  62  |   expect(response.status()).toBe(201)
  63  |   const saved = await response.json()
  64  |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  65  |   await expect(page.getByTestId('request-id')).toHaveText(saved.persistence.request_id)
  66  |   const options = page.getByTestId('saved-option')
  67  |   await expect(options).toHaveCount(2)
  68  |   await expect(options.first()).toContainText('CHF 45.00')
  69  |   await expect(options.first()).toContainText('unknown charges are not zero')
  70  |   await expect(options.first()).toContainText('No supported environmental/resource information.')
  71  |   await expect(options.first()).toContainText('Availability')
  72  |   for (const [index, option] of saved.comparison.options.entries()) {
  73  |     await expect(options.nth(index)).toHaveAttribute('data-option-id', option.option_id)
  74  |     await expect(options.nth(index).getByRole('heading')).toHaveText(option.display_name)
  75  |   }
  76  |   const stored = inspectDatabase()
  77  |   expect(stored.counts).toEqual({ search_request: 1, request_alternative: 2, request_alternative_evidence: 2 })
  78  |   expect(stored.rows[0].projection).toEqual(saved)
  79  |   await expect(page.getByRole('status')).not.toBeVisible()
  80  |   await page.reload()
  81  |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  82  |   expect(inspectDatabase().rows[0].id).toBe(saved.persistence.request_id)
  83  | })
  84  | 
  85  | test('malformed CH postcode requires correction before explicit saved assessment', async ({ page }, testInfo) => {
  86  |   const town = 'Jouxtens-Mézery'
  87  |   const before = inspectDatabase()
  88  |   expect(before.counts.search_request > 0).toBe(true)
  89  |   const priorIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  90  |   const attempts: ReturnType<typeof captureAttempt>[] = []
  91  |   page.on('request', request => {
  92  |     if (request.url().endsWith('/api/comparisons') && request.method() === 'POST') attempts.push(captureAttempt(request))
  93  |   })
  94  |   await page.goto('/')
  95  |   await page.getByLabel('Describe your request').fill(example)
  96  |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  97  |   await page.getByLabel('Town (optional)', { exact: true }).fill(town)
  98  |   await page.getByLabel('Postcode (optional)', { exact: true }).fill('10A8')
  99  |   const invalidResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  100 |     && response.request().method() === 'POST')
  101 |   await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  102 |   const invalid = await invalidResponse
> 103 |   expect(invalid.status()).toBe(422)
      |                            ^ Error: expect(received).toBe(expected) // Object.is equality
  104 |   const invalidBody = await invalid.json()
  105 |   expect(invalidBody.outcome).toBe('invalid_input')
  106 |   expect(invalidBody.persistence).toEqual({ state: 'not_attempted' })
  107 |   expect(invalidBody.issues).toEqual([{ code: 'postcode_format_invalid' }])
  108 |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).toContainText(/four-digit postcode/i)
  109 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  110 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  111 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(town)
  112 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('10A8')
  113 |   await expect(page.getByRole('status')).not.toBeVisible()
  114 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  115 |   for (const label of ['Describe your request', 'Search country', 'Town (optional)', 'Postcode (optional)']) {
  116 |     await expect(page.getByLabel(label, { exact: true })).toBeEnabled()
  117 |   }
  118 |   for (const heading of ['Saved comparison', 'Saved coverage outcome', 'Saved submission acknowledged']) {
  119 |     await expect(page.getByRole('heading', { name: heading, exact: true })).not.toBeVisible()
  120 |   }
  121 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  122 |   expect(attempts.length).toBe(1)
  123 |   const afterInvalid = inspectDatabase()
  124 |   expect(afterInvalid).toEqual(before)
  125 |   await page.getByLabel('Postcode (optional)', { exact: true }).fill('1008')
  126 |   await page.evaluate(() => new Promise<void>(resolve => { requestAnimationFrame(() => resolve()) }))
  127 |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).not.toBeVisible()
  128 |   await expect(page.getByRole('alert')).not.toBeVisible()
  129 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  130 |   await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue(town)
  131 |   await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('1008')
  132 |   expect(attempts.length).toBe(1)
  133 |   const afterCorrection = inspectDatabase()
  134 |   expect(afterCorrection).toEqual(before)
  135 |   const savedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons')
  136 |     && response.request().method() === 'POST')
  137 |   await page.getByRole('button', { name: 'Find alternatives', exact: true }).click()
  138 |   const response = await savedResponse
  139 |   expect(response.status()).toBe(201)
  140 |   const saved = await response.json()
  141 |   expect(saved.outcome).toBe('insufficient_coverage')
  142 |   expect(saved.persistence.state).toBe('saved')
  143 |   expect(saved.coverage.limitation_codes).toContain('geographic_applicability_unverified')
  144 |   const expectedScope = { country_code: 'CH', town, postcode: '1008', locality: {
  145 |     verification: 'matched_in_reference', selection: 'single_match', normalized: { town: 'jouxtens-mézery', postcode: '1008' },
  146 |     association: { reference: { source: 'swisstopo', release: 'swisstopo-chli-associations-2026-10-01-v1', source_record: 10 },
  147 |       country_code: 'CH', locality_name: town, postcode: '1008', source_postcode_id: '5852', additional_number: '02',
  148 |       administrative: { municipality_name: town, municipality_id: '5585', canton: 'VD' } } } }
  149 |   expect(saved.search_scope).toEqual(expectedScope)
  150 |   expect(attempts.length).toBe(2)
  151 |   const initial = JSON.parse(attempts[0].body)
  152 |   const corrected = JSON.parse(attempts[1].body)
  153 |   expect(initial.submission_key !== corrected.submission_key).toBe(true)
  154 |   expect(attempts[0].proofDigest !== attempts[1].proofDigest).toBe(true)
  155 |   expect(initial.text === corrected.text && corrected.text === example).toBe(true)
  156 |   expect(initial.search_location.country_code === corrected.search_location.country_code
  157 |     && corrected.search_location.country_code === 'CH' && initial.search_location.town === corrected.search_location.town
  158 |     && corrected.search_location.town === town).toBe(true)
  159 |   expect(initial.search_location.postcode === '10A8' && corrected.search_location.postcode === '1008').toBe(true)
  160 |   expect(initial.location_choice === 'provided' && corrected.location_choice === 'provided').toBe(true)
  161 |   expect(JSON.stringify(initial.language_context) === JSON.stringify(corrected.language_context)).toBe(true)
  162 |   const after = inspectDatabase()
  163 |   expect(after.counts).toEqual({ search_request: before.counts.search_request + 1,
  164 |     request_alternative: before.counts.request_alternative,
  165 |     request_alternative_evidence: before.counts.request_alternative_evidence })
  166 |   const added = after.rows.filter((row: { id: string }) => !priorIds.has(row.id))
  167 |   expect(added.length).toBe(1)
  168 |   expect(added[0].id).toBe(saved.persistence.request_id)
  169 |   expect(added[0].projection).toEqual(saved)
  170 |   expect(after.rows.filter((row: { id: string }) => priorIds.has(row.id))).toEqual(before.rows)
  171 |   expect(after.snapshots).toEqual(before.snapshots)
  172 |   const stored = JSON.parse(execFileSync(python, ['-c', `
  173 | import json,sqlite3,sys
  174 | with sqlite3.connect(sys.argv[1]) as connection:
  175 |     row=connection.execute('SELECT original_text,interpretation,search_location,language_context FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  176 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
  177 |         'language_context':json.loads(row[3])}))
  178 | `, database, added[0].id], { encoding: 'utf8' }))
  179 |   expect(stored.original_text === example).toBe(true)
  180 |   expect(stored.search_location).toEqual(expectedScope)
  181 |   expect(JSON.stringify(stored.language_context) === JSON.stringify(corrected.language_context)).toBe(true)
  182 |   expect(stored.interpretation.constraints.some((item: { value: string; quote: string }) => item.value === 'no_replacement'
  183 |     && item.quote === 'without replacing it')).toBe(true)
  184 |   const span = stored.interpretation.provenance.items.find((item: { kind: string; normalized: string }) => item.kind === 'constraint'
  185 |     && item.normalized === 'no_replacement').span
  186 |   expect(span.start === 18 && span.end === 38 && span.quote === 'without replacing it').toBe(true)
  187 |   const localityReference = stored.interpretation.provenance.reference_versions.locality
  188 |   expect(localityReference.release).toBe('swisstopo-chli-associations-2026-10-01-v1')
  189 |   expect(localityReference.sha256).toBe('eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9')
  190 |   await expect(page.getByRole('heading', { name: 'Saved coverage outcome', exact: true })).toBeVisible()
  191 |   await expect(page.getByText(added[0].id, { exact: false })).toBeVisible()
  192 |   const shownScope = page.getByRole('region', { name: 'Matched reference association', exact: true })
  193 |   await expect(shownScope).toContainText('Matched in this reference; delivery and service coverage are not established.')
  194 |   await expect(shownScope).toContainText(town)
  195 |   await expect(shownScope).toContainText('1008/02')
  196 |   await expect(shownScope).toContainText('association record: 10')
  197 |   await expect(page.getByRole('heading', { name: 'Saved comparison', exact: true })).not.toBeVisible()
  198 |   await expect(page.getByRole('alert')).not.toBeVisible()
  199 |   await expect(page.getByRole('region', { name: 'Clarification', exact: true })).not.toBeVisible()
  200 |   await expect(page.getByRole('status')).not.toBeVisible()
  201 |   await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  202 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  203 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
```