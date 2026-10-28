import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

const languageNames = { de: 'Deutsch', fr: 'Français', it: 'Italiano', en: 'English' }
type Language = keyof typeof languageNames
type LocationChoice = 'provided' | 'country_only' | 'confirmed_unverified'
type Continuation = Exclude<LocationChoice, 'provided'> | 'association'
const localityIntentLimit = 'Confirmation establishes intended scope only. The locality remains reference-unverified; it does not verify existence, town/postcode identity, delivery, service coverage or nearby applicability.'

function supportedBrowserLanguage(): Language | undefined {
  const language = navigator.language.split('-')[0].toLowerCase()
  return Object.hasOwn(languageNames, language) ? language as Language : undefined
}

interface SavedOption {
  option_id: string
  alternative_id: string
  position: number
  display_name: string
  description: string
  explanation: string
  rendering?: { language: Language; version: string; derivation?: string }
  presentation?: Record<'financial' | 'total_cost' | 'difference' | 'baseline' | 'environmental' | 'availability' | 'geographic_scope' | 'conditions', string>
  financial: { status: string; amount: string | null; currency?: string; unit?: string; period?: string; basis?: string; price_basis?: string; exclusions?: string[]; assumptions?: string[]; total_cost: string | null; difference: string | null; baseline?: { amount: string; currency: string; unit: string; period: string; basis: string } | null; baseline_provenance?: string | null }
  environmental: { status: string; explanation: string }
  claims: { support: string; freshness: string; requirement: string; attribution: string[]; checked_at: string[] }[]
  availability: { status: string; value: boolean | null }
  geographic_scope: Record<string, unknown>
  evidence: { version_id: string; publisher: string; source_reference: string; source_language: string; supporting_quote: string; reviewed_at: string; publication_date?: string | null; updated_at?: string | null; retrieved_at?: string | null; data_period?: string | null; method?: string; baseline?: string; assumptions?: string[] }[]
}

interface ReferenceAssociation {
  reference: { source: string; release: string; source_record: number }
  country_code: string
  locality_name: string
  postcode: string
  source_postcode_id: string
  additional_number: string
  administrative: { municipality_name: string; municipality_id: string; canton: string }
}

interface ApiResult {
  outcome: string
  persistence: { state: string; request_id?: string }
  saved_outcome?: string
  assessed_at?: string
  comparison?: { request_id: string; assessed_at: string; options: SavedOption[]; omitted_count: number }
  assessed_outcome?: string
  limitations?: string[]
  limitation?: string
  issues?: { code: string }[]
  clarification?: { message: string; choices: Language[]; associations?: ReferenceAssociation[]; span?: { quote: string } }
  language?: { explanation_language: Language; origin: string; recognition: { status: string; language: Language | null } }
  search_scope?: {
    country_code: string
    town?: string
    postcode?: string
    locality?: { confirmation?: string; verification: string; normalized: { town?: string; postcode?: string };
      selection?: 'single_match' | 'explicit'; association?: ReferenceAssociation }
  }
}

interface Attempt {
  fingerprint: string
  key: string
  proof: string
  body: string
}

interface CountryCatalogue {
  version: string
  countries: { code: string; name: string }[]
  attribution: { credit: string; source_link: string; license: string; license_link: string; changes: string }
}

function SwisstopoAttribution() {
  return <p>©swisstopo. <a href="https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities">Official reference source</a>; <a href="https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices">Terms of use</a>.</p>
}

function App() {
  const [text, setText] = useState('')
  const [country, setCountry] = useState('CH')
  const [countryCatalogue, setCountryCatalogue] = useState<CountryCatalogue | null>(null)
  const [countryReferenceFailed, setCountryReferenceFailed] = useState(false)
  const [town, setTown] = useState('')
  const [postcode, setPostcode] = useState('')
  const [locationChoice, setLocationChoice] = useState<LocationChoice>('provided')
  const [selectedAssociation, setSelectedAssociation] = useState<ReferenceAssociation | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<ApiResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recovering, setRecovering] = useState(false)
  const [uncertain, setUncertain] = useState(false)
  const [policyResult, setPolicyResult] = useState<ApiResult | null>(null)
  const [showLanguageChoice, setShowLanguageChoice] = useState(false)
  const [languageChoice, setLanguageChoice] = useState<Language | ''>('')
  const [preferredLanguage, setPreferredLanguage] = useState<Language | undefined>()
  const [browserLanguage] = useState(supportedBrowserLanguage)
  const attempt = useRef<Attempt | null>(null)
  const inFlight = useRef(false)

  useEffect(() => {
    const controller = new AbortController()
    async function loadCountries() {
      try {
        const response = await fetch('/api/countries', { signal: controller.signal })
        if (!response.ok) throw new Error('Country reference unavailable')
        const catalogue: CountryCatalogue = await response.json()
        if (!catalogue.version || !Array.isArray(catalogue.countries) || !catalogue.countries.length
          || catalogue.countries.some(entry => typeof entry.code !== 'string' || typeof entry.name !== 'string')
          || !catalogue.attribution?.source_link || !catalogue.attribution.license_link) {
          throw new Error('Country reference unavailable')
        }
        if (!controller.signal.aborted) setCountryCatalogue(catalogue)
      } catch {
        if (!controller.signal.aborted) setCountryReferenceFailed(true)
      }
    }
    void loadCountries()
    return () => controller.abort()
  }, [])

  function clearPresentation() {
    setResult(null)
    setError(null)
    setPolicyResult(null)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await send()
  }

  async function send(continuation?: Continuation) {
    if (inFlight.current) return
    if (continuation === 'association' && !selectedAssociation) return
    if (!countryCatalogue && (!recovering || continuation)) {
      setError('Country reference data is unavailable. New searches cannot be submitted; your fields are preserved.')
      return
    }
    inFlight.current = true
    setBusy(true)
    clearPresentation()
    if (continuation) {
      attempt.current = null
      setRecovering(false)
      setLocationChoice(continuation === 'association' ? 'provided' : continuation)
      if (continuation !== 'association') setSelectedAssociation(null)
    }
    if (continuation === 'country_only') {
      setTown('')
      setPostcode('')
    }
    const languageContext = {
      ...(browserLanguage ? { browser_language: browserLanguage } : {}),
      ...(preferredLanguage ? { preferred_language: preferredLanguage } : {}),
      ...(languageChoice ? { explanation_language_choice: languageChoice } : {}),
    }
    const choice = continuation === 'association' ? 'provided' : continuation ?? locationChoice
    const payload = { text, search_location: { country_code: country,
      ...(choice !== 'country_only' && town ? { town } : {}),
      ...(choice !== 'country_only' && postcode ? { postcode } : {}),
      ...(choice === 'provided' && selectedAssociation ? { reference: selectedAssociation.reference } : {}) },
      location_choice: choice, language_context: languageContext }
    const fingerprint = JSON.stringify(payload)
    try {
      if (!attempt.current || (!recovering && attempt.current.fingerprint !== fingerprint)) {
        const bytes = crypto.getRandomValues(new Uint8Array(32))
        const key = crypto.randomUUID()
        attempt.current = {
          fingerprint, key,
          proof: Array.from(bytes, value => value.toString(16).padStart(2, '0')).join(''),
          body: JSON.stringify({ ...payload, submission_key: key }),
        }
      }
      const current = attempt.current!
      const response = await fetch('/api/comparisons', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Submission-Proof': current.proof },
        body: current.body,
      })
      const body: ApiResult = await response.json()
      if (response.ok && body.persistence?.state === 'saved'
        && (body.outcome === 'submission_recovered' || body.outcome === 'insufficient_coverage' || (body.outcome === 'comparison' && body.comparison))) {
        setResult(body)
        setRecovering(true)
        setUncertain(false)
      } else if (body.persistence?.state === 'unknown') {
        setUncertain(true)
        setRecovering(true)
        setError('Saving could not be confirmed. This submission may already be saved. Recover it explicitly or start a fresh search.')
      } else if (body.outcome === 'persistence_error') {
        setRecovering(false)
        setError(body.assessed_outcome === 'insufficient_coverage'
          ? 'Existing knowledge could not support a comparison, and the coverage outcome could not be saved. Your fields are preserved; try again explicitly.'
          : 'The comparison could not be saved in this attempt. Your fields are preserved; try again explicitly.')
      } else if (body.outcome === 'configuration_unavailable') {
        setError('Required interpretation, knowledge or reference configuration is unavailable. Your fields are preserved.')
      } else if (body.outcome === 'invalid_input') {
        if (body.clarification) {
          setPolicyResult(body)
          if (body.clarification.associations) setSelectedAssociation(null)
        }
        setError(body.clarification ? 'Review the location fields. Your fields are preserved.'
          : 'Enter a request and choose a listed search country. Your fields are preserved.')
      } else if (body.outcome === 'clarification_required') {
        setPolicyResult(body)
        if (body.clarification?.associations) setSelectedAssociation(null)
        if (body.clarification?.choices.length) setShowLanguageChoice(true)
        setError('Clarification is required before knowledge can be assessed. Your fields are preserved.')
      } else if (body.outcome === 'interpretation_unavailable') {
        setPolicyResult(body)
        setError(body.limitation || 'This request could not be interpreted. Rephrase in German, French, Italian or English. Your fields are preserved.')
      } else if (body.outcome === 'recovery_not_authorized' || body.outcome === 'submission_key_conflict') {
        setError('This submission cannot be recovered with the current page context. Start an explicit fresh search.')
      } else {
        setError('The comparison could not be prepared. Your fields are preserved; try again explicitly.')
      }
    } catch {
      setUncertain(true)
      setRecovering(true)
      setError('Delivery status is unknown. The submission may already be saved. Recover it explicitly or start a fresh search.')
    } finally {
      setBusy(false)
      inFlight.current = false
    }
  }

  function freshSearch() {
    attempt.current = null
    setRecovering(false)
    clearPresentation()
  }

  const confirmedScope = (result?.outcome === 'comparison' || result?.outcome === 'insufficient_coverage')
    && result.search_scope?.locality?.confirmation === 'user_confirmed'
    && result.search_scope.locality.verification === 'reference_unverified' ? result.search_scope : null
  const matchedAssociation = (result?.outcome === 'comparison' || result?.outcome === 'insufficient_coverage')
    && result.search_scope?.locality?.verification === 'matched_in_reference' ? result.search_scope.locality.association : null
  const associations = policyResult?.clarification?.associations ?? []
  const canConfirmLocality = policyResult?.issues?.some(issue => ['locality_reference_unknown', 'locality_reference_unavailable'].includes(issue.code))
  const canContinueCountryOnly = policyResult?.issues?.some(issue => ['locality_reference_ambiguous', 'locality_reference_unknown',
    'locality_reference_unavailable', 'locality_selection_inconsistent'].includes(issue.code))

  return (
    <main>
      <header>
        <p className="eyebrow">Resolena Alternative Finder</p>
        <h1>Explore practical alternatives</h1>
        <aside className="demo-note">
          <strong>Development demonstration</strong>
          <p>Approved country reference; interpretation and alternative evidence remain synthetic.</p>
          <p>CH/LI reference source: <a href="https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities">Federal Office of Topography swisstopo</a>. The approved association reference is used only when configured in this development composition; reference matches do not establish delivery or service coverage.</p>
          <p>Test-only interpreter and evidence. No real providers, multilingual support or verified savings.</p>
          <p>Use “Repair my bicycle without replacing it” with CH for a comparison or DE for a synthetic coverage limitation.</p>
          <p>“Velo” exercises explanation-language preferences. Only English synthetic rendering is configured.</p>
          <p>“Synthetic hourly bicycle repair” exercises source-bound test wording in DE/FR/IT/EN. “Synthetic pending bicycle repair” exercises a missing-review limitation. These fixtures do not verify linguistic fidelity.</p>
          {countryCatalogue && <p>{countryCatalogue.attribution.credit} <a href={countryCatalogue.attribution.source_link}>GeoNames</a>; <a href={countryCatalogue.attribution.license_link}>{countryCatalogue.attribution.license}</a>. {countryCatalogue.attribution.changes} No endorsement is implied.</p>}
        </aside>
      </header>

      <form onSubmit={submit} aria-busy={busy}>
        <label htmlFor="request">Describe your request</label>
        <textarea id="request" value={text} required disabled={busy} rows={3}
          onChange={event => { setText(event.target.value); setLanguageChoice(''); setShowLanguageChoice(false); setRecovering(false); clearPresentation() }} />
        <label htmlFor="country">Search country</label>
        <select id="country" value={country} required disabled={busy || !countryCatalogue}
          aria-describedby="country-help"
          onChange={event => { setCountry(event.target.value); setLocationChoice('provided'); setSelectedAssociation(null); setRecovering(false); clearPresentation() }}>
          <option value="">Choose a search country</option>
          {!countryCatalogue && country && <option value={country}>{country} — {countryReferenceFailed ? 'Country reference unavailable' : 'Loading country reference…'}</option>}
          {countryCatalogue?.countries.map(entry => <option key={entry.code} value={entry.code}>{entry.code} — {entry.name}</option>)}
        </select>
        <p id="country-help">CH — Switzerland is the editable default, not a detected location.</p>
        {countryReferenceFailed && <p role="alert" className="error">Country reference data could not be loaded. New searches are unavailable; your fields are preserved.</p>}
        <label htmlFor="town">Town (optional)</label>
        <input id="town" value={town} disabled={busy}
          onChange={event => { setTown(event.target.value); setLocationChoice('provided'); setSelectedAssociation(null); setRecovering(false); clearPresentation() }} />
        <label htmlFor="postcode">Postcode (optional)</label>
        <input id="postcode" value={postcode} disabled={busy}
          onChange={event => { setPostcode(event.target.value); setLocationChoice('provided'); setSelectedAssociation(null); setRecovering(false); clearPresentation() }} />
        {locationChoice === 'country_only' && <p>Search scope: country only ({country}).</p>}
        {(result?.language || policyResult?.issues?.some(issue => issue.code === 'rendering_unavailable')) && !showLanguageChoice && <button type="button" className="secondary" disabled={busy}
          onClick={() => { setShowLanguageChoice(true); setRecovering(false) }}>Change explanation language</button>}
        {showLanguageChoice && <div>
          <label htmlFor="explanation-language">Explanation language</label>
          <select id="explanation-language" value={languageChoice} disabled={busy}
            onChange={event => {
              const choice = event.target.value as Language | ''
              setLanguageChoice(choice)
              setPreferredLanguage(choice || undefined)
              setRecovering(false)
              setResult(null)
            }}>
            <option value="">Choose a language</option>
            {Object.entries(languageNames).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
          <p>Apply the choice by submitting explicitly. It does not change the search country.</p>
        </div>}
        {associations.length > 0 && <div>
          <label htmlFor="association">Reference association</label>
          <select id="association" value={selectedAssociation?.reference.source_record ?? ''} disabled={busy}
            onChange={event => {
              setSelectedAssociation(associations.find(association => String(association.reference.source_record) === event.target.value) ?? null)
              setRecovering(false)
              setResult(null)
            }}>
            <option value="">Choose a reference association</option>
            {associations.map(association => <option key={association.reference.source_record} value={association.reference.source_record}>
              {association.locality_name} — {association.postcode}/{association.additional_number}; {association.administrative.municipality_name}, {association.administrative.canton || association.country_code}; municipality {association.administrative.municipality_id}
            </option>)}
          </select>
          <p>These are reference associations, not a count of distinct physical localities. Selecting alone sends nothing.</p>
          <SwisstopoAttribution />
        </div>}
        <div className="actions">
          <button type="submit" disabled={busy || (!countryCatalogue && !recovering)}>{busy ? 'Processing…' : recovering ? 'Recover submission' : error ? 'Try again' : 'Find alternatives'}</button>
          {associations.length > 0 && <button type="button" className="secondary" disabled={busy || !selectedAssociation}
            onClick={() => { void send('association') }}>Continue with selected association</button>}
          {canContinueCountryOnly &&
            <button type="button" className="secondary" disabled={busy}
              onClick={() => { void send('country_only') }}>Continue with country only</button>}
          {canConfirmLocality &&
            <button type="button" className="secondary" disabled={busy}
              onClick={() => { void send('confirmed_unverified') }}>Confirm entered locality as intended scope</button>}
          {(result || uncertain || error) && <button type="button" className="secondary" disabled={busy} onClick={freshSearch}>Start a fresh search</button>}
        </div>
      </form>

      {busy && <p role="status">Processing your request, including saving. No result is confirmed yet.</p>}
      {error && <p role="alert" className="error">{error}</p>}
      {policyResult?.clarification && <section aria-label="Clarification">
        <p>{policyResult.clarification.message}</p>
        {canConfirmLocality && <p>{localityIntentLimit}</p>}
        {policyResult.clarification.span && <blockquote>{policyResult.clarification.span.quote}</blockquote>}
      </section>}
      {uncertain && <p>An earlier submission may already be saved. Editing starts a new submission; it does not undo an earlier save.</p>}
      {confirmedScope && <section aria-label="Confirmed intended locality">
        <p>User-confirmed intended locality; reference-unverified.</p>
        <p>Country: {confirmedScope.country_code}.{confirmedScope.town && <> Town: {confirmedScope.town}.</>}{confirmedScope.postcode && <> Postcode: {confirmedScope.postcode}.</>}</p>
        <p>{localityIntentLimit}</p>
      </section>}
      {matchedAssociation && <section aria-label="Matched reference association">
        <p>Matched in this reference; delivery and service coverage are not established.</p>
        <p>{matchedAssociation.country_code}; {matchedAssociation.locality_name} — {matchedAssociation.postcode}/{matchedAssociation.additional_number}; {matchedAssociation.administrative.municipality_name}, {matchedAssociation.administrative.canton || matchedAssociation.country_code}; municipality {matchedAssociation.administrative.municipality_id}.</p>
        <p>Source: {matchedAssociation.reference.source}; release: {matchedAssociation.reference.release}; association record: {matchedAssociation.reference.source_record}. Postal identifier: {matchedAssociation.source_postcode_id}; no locality GUID is established.</p>
        <SwisstopoAttribution />
      </section>}
      {result?.language && <p data-testid="language-context">Explanation language: {result.language.explanation_language}; {result.language.origin.replaceAll('_', ' ')}.
        Original-input hypothesis: {result.language.recognition.language || 'uncertain'} ({result.language.recognition.status}; synthetic only).</p>}

      {result?.outcome === 'submission_recovered' && <section aria-labelledby="recovery-heading">
        <h2 id="recovery-heading">Saved submission acknowledged</h2>
        <p>Request <code>{result.persistence.request_id}</code> was saved. This acknowledgement does not replay a comparison or confirm present-day facts.</p>
        <p>Original outcome: {result.saved_outcome}. Originally assessed at: {result.assessed_at}.</p>
      </section>}

      {result?.outcome === 'insufficient_coverage' && <section>
        <h2>Saved coverage outcome</h2>
        <p>Request <code>{result.persistence.request_id}</code> and its insufficient-coverage outcome were saved.</p>
        {result.limitations?.map(limitation => <p key={limitation}>{limitation}</p>)}
        <p>You can edit the fields and submit explicitly. Your constraints have been retained.</p>
      </section>}

      {result?.outcome === 'comparison' && result.comparison && <section aria-labelledby="comparison-heading">
        <h2 id="comparison-heading">Saved comparison</h2>
        <p>Request <code data-testid="request-id">{result.persistence.request_id}</code></p>
        <p>Prepared at the synthetic fixture time: {result.comparison.assessed_at}. Alphabetical order does not imply best or exhaustive coverage.</p>
        {result.comparison.options.length === 1 && <p>One qualifying alternative is shown; this does not imply it is the best or only alternative.</p>}
        {result.comparison.omitted_count > 0 && <p>{result.comparison.omitted_count} additional qualifying alternatives omitted by the three-result display limit.</p>}
        <ol className="options">
          {result.comparison.options.map(option => <li key={option.option_id} data-testid="saved-option" data-option-id={option.option_id}>
            <h3>{option.display_name}</h3>
            <p lang={option.rendering?.language}>{option.description}</p>
            <p lang={option.rendering?.language}>{option.explanation}</p>
            {option.rendering?.derivation && <p className="metadata">Paraphrased from the cited sources.</p>}
            <dl>
              <dt>Financial information</dt><dd lang={option.rendering?.language}>{option.presentation?.financial ?? (option.financial.amount !== null
                ? <>{option.financial.price_basis}: {option.financial.currency} {option.financial.amount}; unit: {option.financial.unit}; period: {option.financial.period}; basis: {option.financial.basis}. Exclusions: {option.financial.exclusions?.join(', ') || 'none stated'}. Assumptions: {option.financial.assumptions?.join(', ') || 'none stated'}.</>
                : 'Unknown; no supported financial information.')}</dd>
              <dt>Total cost</dt><dd lang={option.rendering?.language}>{option.presentation?.total_cost ?? (option.financial.total_cost === null ? 'Unknown; unknown charges are not zero.' : `${option.financial.currency} ${option.financial.total_cost}`)}</dd>
              <dt>Cost difference</dt><dd lang={option.rendering?.language}>{option.presentation?.difference ?? (option.financial.difference === null ? 'Unknown; no supported comparable difference.' : `${option.financial.currency} ${option.financial.difference} on the stated basis and exclusions.`)}</dd>
              <dt>Current-choice baseline</dt><dd lang={option.rendering?.language}>{option.presentation?.baseline ?? (option.financial.baseline
                ? `${option.financial.baseline_provenance}: ${option.financial.baseline.currency} ${option.financial.baseline.amount}; ${option.financial.baseline.unit}; ${option.financial.baseline.period}; ${option.financial.baseline.basis}.`
                : 'Unspecified; no baseline or savings inferred.')}</dd>
              <dt>Environmental/resource information</dt><dd lang={option.rendering?.language}>{option.presentation?.environmental ?? `${option.environmental.status}: ${option.environmental.explanation}`}</dd>
              <dt>Availability</dt><dd lang={option.rendering?.language}>{option.presentation?.availability ?? `${option.availability.status}${option.availability.value !== null ? `: ${option.availability.value ? 'available' : 'unavailable'} at review time; no live guarantee` : ''}`}</dd>
              <dt>Geographic scope</dt><dd lang={option.rendering?.language}>{option.presentation?.geographic_scope ?? (['country_code', 'town', 'postcode', 'conditions'].map(key => option.geographic_scope[key]).filter(Boolean).map(String).join('; ') || 'Unknown')}</dd>
              {option.presentation && <><dt>Conditions and unknowns</dt><dd lang={option.rendering?.language}>{option.presentation.conditions}</dd></>}
            </dl>
            {option.claims.map((claim, index) => <p key={index} className="metadata">Support: {claim.support}; freshness: {claim.freshness}; requirement: {claim.requirement}. {claim.attribution?.join(', ')}; checked at {claim.checked_at?.join(', ')} (synthetic). Evidence support does not imply independent verification or a live guarantee.</p>)}
            {option.evidence.map(source => <details key={source.version_id}>
              <summary>Evidence: {source.publisher}</summary>
              <p>{/^https?:\/\//.test(source.source_reference) ? <a href={source.source_reference}>{source.source_reference}</a> : source.source_reference}; original language: {source.source_language}; synthetic review: {source.reviewed_at}.</p>
              <p>Publication: {source.publication_date || 'unknown'}; update: {source.updated_at || 'unknown'}; retrieval: {source.retrieved_at || 'unknown'}; data period: {source.data_period || 'unknown'}.</p>
              {source.method && <p>Method: {source.method}; baseline: {source.baseline || 'unknown'}; assumptions: {source.assumptions?.join(', ') || 'unknown'}.</p>}
              <blockquote lang={source.source_language}>{source.supporting_quote}</blockquote>
            </details>)}
          </li>)}
        </ol>
      </section>}
    </main>
  )
}

export default App
