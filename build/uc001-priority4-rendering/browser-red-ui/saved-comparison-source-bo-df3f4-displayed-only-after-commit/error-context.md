# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: saved-comparison.spec.ts >> source-bound synthetic fr wording is displayed only after commit
- Location: ../tests/e2e/saved-comparison.spec.ts:209:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByTestId('saved-option').getByText('Tarif déclaré par le prestataire synthétique : CHF 120.00 par heure de main-d’œuvre ; ce n’est pas un prix total.', { exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByTestId('saved-option').getByText('Tarif déclaré par le prestataire synthétique : CHF 120.00 par heure de main-d’œuvre ; ce n’est pas un prix total.', { exact: true }) with timeout 5000ms
  - waiting for getByTestId('saved-option').getByText('Tarif déclaré par le prestataire synthétique : CHF 120.00 par heure de main-d’œuvre ; ce n’est pas un prix total.', { exact: true })

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
  - text: Describe your request
  - textbox "Describe your request": Synthetic hourly bicycle repair
  - text: Search country
  - textbox "Search country": CH
  - paragraph: CH — Switzerland is the editable default, not a detected location.
  - button "Change explanation language"
  - button "Recover submission"
  - button "Start a fresh search"
  - paragraph: "Explanation language: fr; browser preference. Original-input hypothesis: uncertain (unknown; synthetic only)."
  - region "Saved comparison":
    - heading "Saved comparison" [level=2]
    - paragraph:
      - text: Request
      - code: 6a2d7c3c-5c0a-4790-96ff-344b813f93c4
    - paragraph: "Prepared at the synthetic fixture time: 2026-10-15T10:00:00+00:00. Alphabetical order does not imply best or exhaustive coverage."
    - paragraph: One qualifying alternative is shown; this does not imply it is the best or only alternative.
    - list:
      - listitem:
        - heading "Hourly repair (synthetic)" [level=3]
        - paragraph: Réparation de vélo synthétique.
        - paragraph: Déclaration du prestataire synthétique ; uniquement l’atelier de test en CH. Confirmer les travaux et le matériel avec l’atelier.
        - term: Financial information
        - definition: "quoted: CHF 120.00; unit: workshop labour hour; period: once; basis: hourly repair rate; not a complete repair quote. Exclusions: none stated. Assumptions: none stated."
        - term: Total cost
        - definition: Unknown; unknown charges are not zero.
        - term: Cost difference
        - definition: Unknown; no supported comparable difference.
        - term: Current-choice baseline
        - definition: Unspecified; no baseline or savings inferred.
        - term: Environmental/resource information
        - definition: "unknown: No supported environmental/resource information."
        - term: Availability
        - definition: unknown
        - term: Geographic scope
        - definition: CH
        - paragraph: "Support: supported; freshness: fresh; requirement: satisfied. provider-stated; checked at 2026-10-15T10:00:00+00:00 (synthetic). Evidence support does not imply independent verification or a live guarantee."
        - paragraph: "Support: supported; freshness: fresh; requirement: satisfied. provider-stated; checked at 2026-10-15T10:00:00+00:00 (synthetic). Evidence support does not imply independent verification or a live guarantee."
        - paragraph: "Support: supported; freshness: fresh; requirement: not_applicable. provider-stated; checked at 2026-10-15T10:00:00+00:00 (synthetic). Evidence support does not imply independent verification or a live guarantee."
        - paragraph: "Support: supported; freshness: fresh; requirement: satisfied. provider-stated; checked at 2026-10-15T10:00:00+00:00 (synthetic). Evidence support does not imply independent verification or a live guarantee."
        - paragraph: "Support: supported; freshness: fresh; requirement: not_applicable. provider-stated; checked at 2026-10-15T10:00:00+00:00 (synthetic). Evidence support does not imply independent verification or a live guarantee."
        - group: "Evidence: Synthetic hourly provider"
```

# Test source

```ts
  134 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  135 |     expect(inspectDatabase().counts).toEqual(before.counts)
  136 |     await page.getByLabel('Explanation language', { exact: true }).selectOption('en')
  137 |     await page.getByRole('button', { name: 'Try again' }).click()
  138 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  139 |     await expect(page.getByTestId('language-context')).toContainText('en; user choice')
  140 |     const stored = inspectDatabase()
  141 |     expect(stored.rows.at(-1).projection.language.recognition.status).toBe('unknown')
  142 |     expect(stored.rows.at(-1).projection.language.explanation_language).toBe('en')
  143 |   } finally {
  144 |     await context.close()
  145 |   }
  146 | })
  147 | 
  148 | test('language correction is a new explicit submission and does not fake a missing translation', async ({ page }) => {
  149 |   await page.goto('/')
  150 |   await page.getByLabel('Describe your request').fill(example)
  151 |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  152 |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  153 |   const before = inspectDatabase()
  154 |   await page.getByRole('button', { name: 'Change explanation language' }).click()
  155 |   await page.getByLabel('Explanation language', { exact: true }).selectOption('fr')
  156 |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  157 |   await expect(page.getByRole('alert')).toContainText('Only the English synthetic rendering is configured')
  158 |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  159 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  160 |   await expect(page.getByLabel('Describe your request')).toHaveValue(example)
  161 |   expect(inspectDatabase().counts).toEqual(before.counts)
  162 |   await page.getByLabel('Describe your request').fill('')
  163 |   await page.getByLabel('Describe your request').fill(example)
  164 |   const pending = page.waitForResponse(response => response.url().endsWith('/api/comparisons'))
  165 |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  166 |   const response = await pending
  167 |   expect(response.status()).toBe(201)
  168 |   expect((await response.json()).language.explanation_language).toBe('en')
  169 | })
  170 | 
  171 | test('capability limitation and meaning clarification preserve fields without search records', async ({ page }) => {
  172 |   const before = inspectDatabase()
  173 |   await page.goto('/')
  174 |   await page.getByLabel('Describe your request').fill('Synthetic unsupported input')
  175 |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  176 |   await expect(page.getByRole('alert')).toContainText('Synthetic capability limitation')
  177 |   await expect(page.getByRole('status')).not.toBeVisible()
  178 |   await expect(page.getByLabel('Describe your request')).toHaveValue('Synthetic unsupported input')
  179 |   await page.getByLabel('Describe your request').fill('Synthetic unclear clause')
  180 |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  181 |   await expect(page.getByText('Clarify the synthetic clause before continuing.')).toBeVisible()
  182 |   await expect(page.getByRole('status')).not.toBeVisible()
  183 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  184 |   expect(inspectDatabase().counts).toEqual(before.counts)
  185 | })
  186 | 
  187 | test('an unavailable browser-preferred rendering still allows explicit correction', async ({ browser }) => {
  188 |   const context = await browser.newContext({ locale: 'fr-CH' })
  189 |   const page = await context.newPage()
  190 |   const before = inspectDatabase()
  191 |   try {
  192 |     await page.goto('/')
  193 |     await page.getByLabel('Describe your request').fill('Velo')
  194 |     await page.getByRole('button', { name: 'Find alternatives' }).click()
  195 |     await expect(page.getByRole('alert')).toContainText('Only the English synthetic rendering is configured')
  196 |     expect(inspectDatabase().counts).toEqual(before.counts)
  197 |     await page.getByRole('button', { name: 'Change explanation language' }).click()
  198 |     await page.getByLabel('Explanation language', { exact: true }).selectOption('en')
  199 |     await page.getByRole('button', { name: 'Try again' }).click()
  200 |     await expect(page.getByRole('heading', { name: 'Saved comparison' })).toBeVisible()
  201 |     await expect(page.getByLabel('Search country')).toHaveValue('CH')
  202 |     await expect(page.getByTestId('language-context')).toContainText('en; user choice')
  203 |   } finally {
  204 |     await context.close()
  205 |   }
  206 | })
  207 | 
  208 | for (const language of ['de', 'fr', 'it', 'en']) {
  209 |   test(`source-bound synthetic ${language} wording is displayed only after commit`, async ({ browser }) => {
  210 |     const context = await browser.newContext({ locale: `${language}-CH` })
  211 |     const page = await context.newPage()
  212 |     let release!: () => void
  213 |     const gate = new Promise<void>(resolve => { release = resolve })
  214 |     let committed!: (body: unknown) => void
  215 |     const saved = new Promise<any>(resolve => { committed = resolve })
  216 |     await page.route('**/api/comparisons', async route => {
  217 |       const response = await route.fetch()
  218 |       committed(await response.json())
  219 |       await gate
  220 |       await route.fulfill({ response })
  221 |     })
  222 |     try {
  223 |       await page.goto('/')
  224 |       await page.getByLabel('Describe your request').fill('Synthetic hourly bicycle repair')
  225 |       await page.getByRole('button', { name: 'Find alternatives' }).click()
  226 |       const body = await saved
  227 |       const option = body.comparison.options[0]
  228 |       expect(inspectDatabase().rows.at(-1).projection).toEqual(body)
  229 |       await expect(page.getByRole('status')).toBeVisible()
  230 |       await expect(page.getByTestId('saved-option')).toHaveCount(0)
  231 |       release()
  232 |       const shown = page.getByTestId('saved-option')
  233 |       await expect(shown).toHaveCount(1)
> 234 |       await expect(shown.getByText(option.presentation.financial, { exact: true })).toBeVisible()
      |                                                                                     ^ Error: expect(locator).toBeVisible() failed
  235 |       await expect(shown.getByText(option.presentation.environmental, { exact: true })).toBeVisible()
  236 |       await expect(shown.getByText(option.presentation.total_cost, { exact: true })).toBeVisible()
  237 |       await expect(shown.getByText(option.presentation.conditions, { exact: true })).toBeVisible()
  238 |       await expect(shown.getByText(option.presentation.financial, { exact: true })).toHaveAttribute('lang', language)
  239 |       expect(option.rendering.review.synthetic).toBe(true)
  240 |       await shown.getByText('Evidence: Synthetic hourly provider').click()
  241 |       await expect(shown.getByRole('link', { name: 'https://synthetic.example.invalid/hourly-repair-v1' })).toHaveAttribute('href', 'https://synthetic.example.invalid/hourly-repair-v1')
  242 |       await expect(shown.locator('blockquote')).toHaveText(option.evidence[0].supporting_quote)
  243 |       await expect(page.getByLabel('Search country')).toHaveValue('CH')
  244 |     } finally {
  245 |       release()
  246 |       await context.close()
  247 |     }
  248 |   })
  249 | }
  250 | 
  251 | test('pending source-bound wording is an unsaved rendering limitation', async ({ page }) => {
  252 |   const before = inspectDatabase()
  253 |   await page.goto('/')
  254 |   await page.getByLabel('Describe your request').fill('Synthetic pending bicycle repair')
  255 |   await page.getByRole('button', { name: 'Find alternatives' }).click()
  256 |   await expect(page.getByRole('alert')).toContainText('Reviewed wording is unavailable')
  257 |   await expect(page.getByTestId('saved-option')).toHaveCount(0)
  258 |   await expect(page.getByRole('heading', { name: 'Saved comparison' })).not.toBeVisible()
  259 |   await expect(page.getByLabel('Describe your request')).toHaveValue('Synthetic pending bicycle repair')
  260 |   await expect(page.getByLabel('Search country')).toHaveValue('CH')
  261 |   await expect(page.getByRole('status')).not.toBeVisible()
  262 |   expect(inspectDatabase().counts).toEqual(before.counts)
  263 | })
  264 | 
```