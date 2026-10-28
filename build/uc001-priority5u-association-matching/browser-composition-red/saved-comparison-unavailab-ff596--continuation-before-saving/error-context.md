# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> unavailable locality requires explicit country-only continuation before saving
- Location: ../tests/e2e/saved-comparison.spec.ts:1721:5

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
  1653 |     expect(fault.dialect_methods_restored).toBe(true)
  1654 |     expect(fault.observer_rows_supplied_to_application).toBe(false)
  1655 |     await expect(page.getByRole('status')).toBeVisible()
  1656 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'true')
  1657 |     await expect(page.getByRole('button', { name: 'Processing…' })).toBeDisabled()
  1658 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  1659 |     await expect(page.getByRole('alert')).not.toBeVisible()
  1660 |     const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  1661 |     releaseError()
  1662 |     const errorResponse = await responsePromise
  1663 |     expect(errorResponse.status()).toBe(delivered.status)
  1664 |     expect(await errorResponse.json()).toEqual(delivered.body)
  1665 |     await expect(page.getByRole('alert')).toContainText('Saving could not be confirmed')
  1666 |     await expect(page.getByRole('alert')).toContainText('may already be saved')
  1667 |     await expect(page.getByRole('alert')).not.toContainText('could not be saved')
  1668 |     await expect(page.getByRole('status')).not.toBeVisible()
  1669 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  1670 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  1671 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  1672 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  1673 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  1674 |     await expect(page.getByText('Existing knowledge could not support', { exact: false })).not.toBeVisible()
  1675 |     await expect(page.getByRole('button', { name: 'Recover submission' })).toBeEnabled()
  1676 |     await expect(page.getByRole('button', { name: 'Start a fresh search' })).toBeEnabled()
  1677 |     await page.waitForTimeout(300)
  1678 |     expect(attempts.length).toBe(1)
  1679 |     expect(inspectDatabase()).toEqual(stored)
  1680 | 
  1681 |     const recoveryResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  1682 |     await page.getByRole('button', { name: 'Recover submission' }).click()
  1683 |     const response = await recoveryResponse
  1684 |     expect(response.status()).toBe(200)
  1685 |     const acknowledgement = await response.json()
  1686 |     expect(acknowledgement).toEqual({ outcome: 'submission_recovered', persistence: saved.persistence,
  1687 |       saved_outcome: 'comparison', assessed_at: saved.assessed_at })
  1688 |     expect(attempts.length).toBe(2)
  1689 |     expect(attempts[1].body === attempts[0].body).toBe(true)
  1690 |     expect(attempts[1].proofDigest === attempts[0].proofDigest).toBe(true)
  1691 |     const acknowledged = page.getByRole('region', { name: 'Saved submission acknowledged' })
  1692 |     await expect(acknowledged).toContainText(saved.persistence.request_id)
  1693 |     await expect(acknowledged).toContainText('Original outcome: comparison')
  1694 |     await expect(acknowledged).toContainText(`Originally assessed at: ${saved.assessed_at}`)
  1695 |     await expect(acknowledged).toContainText('does not replay a comparison or confirm present-day facts')
  1696 |     await expect(page.getByRole('alert')).not.toBeVisible()
  1697 |     await expect(page.getByRole('status')).not.toBeVisible()
  1698 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  1699 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  1700 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  1701 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  1702 |     const after = inspectDatabase()
  1703 |     expect(after).toEqual(stored)
  1704 |     const evidencePath = testInfo.outputPath('delivered-unknown-recovery-evidence.json')
  1705 |     writeFileSync(evidencePath, JSON.stringify({ before, committed: stored, recovered: after, fault,
  1706 |       added_request_id: addedRequest.id, new_identity_selected_by_baseline_difference: true,
  1707 |       preexisting_records_and_source_evidence_preserved: true,
  1708 |       runner_control: { path: controlFile, initially_absent: true, consumed_after_error: true },
  1709 |       error_response: { status: errorResponse.status(), body: delivered.body },
  1710 |       recovery_response: { status: response.status(), body: acknowledgement },
  1711 |       browser_submissions: attempts.length, same_serialized_body_key_and_proof: true,
  1712 |       loading_held_until_actual_error_delivered: true, fields_preserved_after_error_and_recovery: true,
  1713 |       no_comparison_or_coverage_presented: true, no_automatic_retry_observed_ms: 300,
  1714 |       fresh_search_action_unchanged_and_not_exercised: true, raw_originating_proofs_recorded: false }, null, 2))
  1715 |     await testInfo.attach('delivered-unknown-recovery-evidence', { path: evidencePath, contentType: 'application/json' })
  1716 |   } finally {
  1717 |     releaseError()
  1718 |   }
  1719 | })
  1720 | 
  1721 | test('unavailable locality requires explicit country-only continuation before saving', async ({ page }, testInfo) => {
  1722 |   const before = inspectDatabase()
  1723 |   const priorRequestIds = new Set<string>(before.rows.map((row: { id: string }) => row.id))
  1724 |   const priorOptionIds = new Set<string>(before.snapshots.request_alternative.map(([id]: [string, ...unknown[]]) => id))
  1725 |   const attempts: ReturnType<typeof captureAttempt>[] = []
  1726 |   let releaseSaved!: () => void
  1727 |   const savedGate = new Promise<void>(resolve => { releaseSaved = resolve })
  1728 |   type Capture = { status: number; body: any; stored: ReturnType<typeof inspectDatabase> }
  1729 |   let captureSaved!: (value: Capture) => void
  1730 |   const committed = new Promise<Capture>(resolve => { captureSaved = resolve })
  1731 |   await page.route('**/api/comparisons', async route => {
  1732 |     attempts.push(captureAttempt(route.request()))
  1733 |     const response = await route.fetch({ maxRetries: 0 })
  1734 |     if (attempts.length === 2) {
  1735 |       captureSaved({ status: response.status(), body: await response.json(), stored: inspectDatabase() })
  1736 |       await savedGate
  1737 |     }
  1738 |     await route.fulfill({ response })
  1739 |   })
  1740 |   try {
  1741 |     await page.goto('/')
  1742 |     await page.getByLabel('Describe your request').fill(example)
  1743 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toBeVisible({ timeout: 3000 })
  1744 |     await page.getByLabel('Town (optional)', { exact: true }).fill('Synthetic optional town')
  1745 |     await page.getByLabel('Postcode (optional)', { exact: true }).fill('0123')
  1746 |     const clarificationResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  1747 |     await page.getByRole('button', { name: 'Find alternatives' }).click()
  1748 |     const clarification = await clarificationResponse
  1749 |     expect(clarification.status()).toBe(200)
  1750 |     const clarificationBody = await clarification.json()
  1751 |     expect(clarificationBody.outcome).toBe('clarification_required')
  1752 |     expect(clarificationBody.persistence).toEqual({ state: 'not_attempted' })
> 1753 |     expect(clarificationBody.issues).toEqual([{ code: 'locality_reference_unavailable' }])
       |                                      ^ Error: expect(received).toEqual(expected) // deep equality
  1754 |     await expect(page.getByRole('region', { name: 'Clarification' })).toContainText('cannot currently be verified')
  1755 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  1756 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  1757 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('Synthetic optional town')
  1758 |     await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('0123')
  1759 |     await expect(page.getByRole('status')).not.toBeVisible()
  1760 |     await expect(page.locator('form')).toHaveAttribute('aria-busy', 'false')
  1761 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  1762 |     await expect(page.getByRole('heading', { name: 'Saved coverage outcome' })).not.toBeVisible()
  1763 |     await expect(page.getByRole('button', { name: 'Continue with country only', exact: true })).toBeEnabled()
  1764 |     expect(inspectDatabase()).toEqual(before)
  1765 |     await page.waitForTimeout(300)
  1766 |     expect(attempts.length).toBe(1)
  1767 |     expect(inspectDatabase()).toEqual(before)
  1768 | 
  1769 |     const savedResponse = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  1770 |     await page.getByRole('button', { name: 'Continue with country only', exact: true }).click()
  1771 |     const saved = await committed
  1772 |     expect(saved.status).toBe(201)
  1773 |     expect(saved.body.outcome).toBe('comparison')
  1774 |     expect(saved.stored.counts).toEqual({
  1775 |       search_request: before.counts.search_request + 1,
  1776 |       request_alternative: before.counts.request_alternative + 2,
  1777 |       request_alternative_evidence: before.counts.request_alternative_evidence + 2,
  1778 |     })
  1779 |     const addedRequests = saved.stored.rows.filter((row: { id: string }) => !priorRequestIds.has(row.id))
  1780 |     expect(addedRequests.length).toBe(1)
  1781 |     const addedRequest = addedRequests[0]
  1782 |     expect(addedRequest.id).toBe(saved.body.persistence.request_id)
  1783 |     expect(addedRequest.projection).toEqual(saved.body)
  1784 |     expect(saved.stored.rows.filter((row: { id: string }) => priorRequestIds.has(row.id))).toEqual(before.rows)
  1785 |     expect(saved.stored.snapshots.request_alternative.filter(([id]: [string, ...unknown[]]) => priorOptionIds.has(id)))
  1786 |       .toEqual(before.snapshots.request_alternative)
  1787 |     expect(saved.stored.snapshots.request_alternative_evidence.filter(([id]: [string, string]) => priorOptionIds.has(id)))
  1788 |       .toEqual(before.snapshots.request_alternative_evidence)
  1789 |     expect(saved.stored.snapshots.evidence).toEqual(before.snapshots.evidence)
  1790 |     expect(attempts.length).toBe(2)
  1791 |     const original = JSON.parse(attempts[0].body)
  1792 |     const continuation = JSON.parse(attempts[1].body)
  1793 |     expect(original.search_location).toEqual({ country_code: 'CH', town: 'Synthetic optional town', postcode: '0123' })
  1794 |     expect(original.location_choice).toBe('provided')
  1795 |     expect(continuation.search_location).toEqual({ country_code: 'CH' })
  1796 |     expect(continuation.location_choice).toBe('country_only')
  1797 |     expect(continuation.text === original.text && continuation.text === example).toBe(true)
  1798 |     expect(continuation.language_context).toEqual(original.language_context)
  1799 |     expect(continuation.submission_key !== original.submission_key).toBe(true)
  1800 |     expect(attempts[1].proofDigest !== attempts[0].proofDigest).toBe(true)
  1801 |     const storedRequest = JSON.parse(execFileSync(python, ['-c', `
  1802 | import json,sqlite3,sys
  1803 | with sqlite3.connect(sys.argv[1]) as connection:
  1804 |     row=connection.execute('SELECT original_text,interpretation,search_location,location_choice,language_context,assessed_at,outcome FROM search_request WHERE id=?',(sys.argv[2],)).fetchone()
  1805 |     print(json.dumps({'original_text':row[0],'interpretation':json.loads(row[1]),'search_location':json.loads(row[2]),
  1806 |         'location_choice':row[3],'language_context':json.loads(row[4]),'assessed_at':row[5],'outcome':row[6]}))
  1807 | `, database, addedRequest.id], { encoding: 'utf8' }))
  1808 |     expect(storedRequest.original_text).toBe(example)
  1809 |     expect(storedRequest.search_location).toEqual({ country_code: 'CH' })
  1810 |     expect(storedRequest.location_choice).toBe('country_only')
  1811 |     expect(storedRequest.language_context).toEqual(original.language_context)
  1812 |     expect(storedRequest.interpretation.constraints).toEqual([{ value: 'no_replacement', quote: 'without replacing it' }])
  1813 |     expect(storedRequest.assessed_at).toBe('2026-10-15T10:00:00+00:00')
  1814 |     await expect(page.getByRole('status')).toBeVisible()
  1815 |     await expect(page.getByTestId('saved-option')).toHaveCount(0)
  1816 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  1817 |     await expect(page.getByLabel('Town (optional)', { exact: true })).toHaveValue('')
  1818 |     await expect(page.getByLabel('Postcode (optional)', { exact: true })).toHaveValue('')
  1819 |     await expect(page.getByText('Search scope: country only (CH).', { exact: true })).toBeVisible()
  1820 |     releaseSaved()
  1821 |     const delivered = await savedResponse
  1822 |     expect(delivered.status()).toBe(201)
  1823 |     expect(await delivered.json()).toEqual(saved.body)
  1824 |     await expect(page.getByTestId('request-id')).toHaveText(addedRequest.id)
  1825 |     await expect(page.getByTestId('saved-option')).toHaveCount(2)
  1826 |     await expect(page.getByRole('status')).not.toBeVisible()
  1827 |     await expect(page.getByRole('alert')).not.toBeVisible()
  1828 |     await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  1829 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  1830 |     expect(inspectDatabase()).toEqual(saved.stored)
  1831 |     const evidencePath = testInfo.outputPath('country-only-continuation-evidence.json')
  1832 |     writeFileSync(evidencePath, JSON.stringify({ before, clarification_response: { status: clarification.status(), body: clarificationBody },
  1833 |       clarification_saved_no_search: true, fields_retained_until_explicit_choice: true, bounded_no_automatic_continuation_ms: 300,
  1834 |       committed: saved.stored, saved_request_id: addedRequest.id, saved_request: storedRequest,
  1835 |       saved_response: { status: delivered.status(), body: saved.body }, browser_submissions: attempts.length,
  1836 |       explicit_choice_uses_new_key_and_proof: true, original_text_country_language_preserved: true,
  1837 |       prior_records_and_source_evidence_preserved: true, saved_before_presentation: true,
  1838 |       delayed_save_t12_exercised: false, raw_originating_proofs_recorded: false }, null, 2))
  1839 |     await testInfo.attach('country-only-continuation-evidence', { path: evidencePath, contentType: 'application/json' })
  1840 |   } finally {
  1841 |     releaseSaved()
  1842 |   }
  1843 | })
  1844 | 
  1845 | test('explicit fresh search after recovered acknowledgement reassesses expired evidence', async ({ page }, testInfo) => {
  1846 |   const clockFile = process.env.RESOLENA_E2E_CLOCK_FILE!
  1847 |   expect(Boolean(clockFile)).toBe(true)
  1848 |   const originalTime = '2026-10-15T10:00:00+00:00'
  1849 |   const freshTime = '2027-10-16T10:00:00+00:00'
  1850 |   writeFileSync(clockFile, JSON.stringify({ now: originalTime }))
  1851 |   const before = inspectDatabase()
  1852 |   const attempts: ReturnType<typeof captureAttempt>[] = []
  1853 |   type Capture = { body: any; status: number; stored: ReturnType<typeof inspectDatabase> }
```