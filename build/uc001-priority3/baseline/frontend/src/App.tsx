import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

interface SavedOption {
  option_id: string
  alternative_id: string
  position: number
  display_name: string
  description: string
  explanation: string
  financial: { status: string; amount: string | null; currency?: string; unit?: string; period?: string; basis?: string; price_basis?: string; exclusions?: string[]; assumptions?: string[]; total_cost: string | null; difference: string | null; baseline?: { amount: string; currency: string; unit: string; period: string; basis: string } | null; baseline_provenance?: string | null }
  environmental: { status: string; explanation: string }
  claims: { support: string; freshness: string; requirement: string; attribution: string[]; checked_at: string[] }[]
  availability: { status: string; value: boolean | null }
  geographic_scope: Record<string, unknown>
  evidence: { version_id: string; publisher: string; source_reference: string; source_language: string; supporting_quote: string; reviewed_at: string; publication_date?: string | null; updated_at?: string | null; retrieved_at?: string | null; data_period?: string | null; method?: string; baseline?: string; assumptions?: string[] }[]
}

interface ApiResult {
  outcome: string
  persistence: { state: string; request_id?: string }
  comparison?: { request_id: string; assessed_at: string; options: SavedOption[]; omitted_count: number }
  assessed_outcome?: string
  limitations?: string[]
}

interface Attempt {
  fingerprint: string
  key: string
  proof: string
}

function App() {
  const [text, setText] = useState('')
  const [country, setCountry] = useState('CH')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<ApiResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [recovering, setRecovering] = useState(false)
  const [uncertain, setUncertain] = useState(false)
  const attempt = useRef<Attempt | null>(null)
  const inFlight = useRef(false)

  function clearPresentation() {
    setResult(null)
    setError(null)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (inFlight.current) return
    inFlight.current = true
    setBusy(true)
    clearPresentation()
    const payload = { text, search_location: { country_code: country }, location_choice: 'provided', language_context: {} }
    const fingerprint = JSON.stringify(payload)
    try {
      if (attempt.current?.fingerprint !== fingerprint) {
        const bytes = crypto.getRandomValues(new Uint8Array(32))
        attempt.current = {
          fingerprint, key: crypto.randomUUID(),
          proof: Array.from(bytes, value => value.toString(16).padStart(2, '0')).join(''),
        }
      }
      const current = attempt.current!
      const response = await fetch('/api/comparisons', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Submission-Proof': current.proof },
        body: JSON.stringify({ ...payload, submission_key: current.key }),
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
        setError('This demonstration supports only the synthetic example with country CH. Real interpretation and reviewed knowledge are not configured.')
      } else if (body.outcome === 'invalid_input') {
        setError('Enter a request and a two-letter search-country code. Your fields are preserved.')
      } else if (body.outcome === 'clarification_required') {
        setError('Clarification is required before knowledge can be assessed. Your fields are preserved.')
      } else if (body.outcome === 'interpretation_unavailable') {
        setError('This request could not be interpreted. Rephrase in German, French, Italian or English. Your fields are preserved.')
      } else if (body.outcome === 'recovery_not_authorized' || body.outcome === 'submission_key_conflict') {
        setError('This submission cannot be recovered with the current page context. Start an explicit fresh search.')
      } else {
        setError('The comparison could not be prepared. Your fields are preserved; try again explicitly.')
      }
    } catch {
      setUncertain(true)
      setRecovering(true)
      setError('No result was confirmed. The submission may already be saved. Recover it explicitly or start a fresh search.')
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

  return (
    <main>
      <header>
        <p className="eyebrow">Resolena Alternative Finder</p>
        <h1>Explore practical alternatives</h1>
        <aside className="demo-note">
          <strong>Synthetic demonstration</strong>
          <p>Test-only interpreter and evidence. No real providers, multilingual support or verified savings.</p>
          <p>Use “Repair my bicycle without replacing it” with CH for a comparison or DE for a synthetic coverage limitation.</p>
        </aside>
      </header>

      <form onSubmit={submit} aria-busy={busy}>
        <label htmlFor="request">Describe your request</label>
        <textarea id="request" value={text} required disabled={busy} rows={3}
          onChange={event => { setText(event.target.value); setRecovering(false); clearPresentation() }} />
        <label htmlFor="country">Search country</label>
        <input id="country" value={country} required disabled={busy} maxLength={2} pattern="[A-Z]{2}"
          aria-describedby="country-help"
          onChange={event => { setCountry(event.target.value.toUpperCase()); setRecovering(false); clearPresentation() }} />
        <p id="country-help">CH — Switzerland is the editable default, not a detected location.</p>
        <div className="actions">
          <button type="submit" disabled={busy}>{busy ? 'Processing…' : recovering ? 'Recover submission' : error ? 'Try again' : 'Find alternatives'}</button>
          {(result || uncertain || error) && <button type="button" className="secondary" disabled={busy} onClick={freshSearch}>Start a fresh search</button>}
        </div>
      </form>

      {busy && <p role="status">Processing your request, including saving. No result is confirmed yet.</p>}
      {error && <p role="alert" className="error">{error}</p>}
      {uncertain && <p>An earlier submission may already be saved. Editing starts a new submission; it does not undo an earlier save.</p>}

      {result?.outcome === 'submission_recovered' && <section>
        <h2>Saved submission acknowledged</h2>
        <p>Request <code>{result.persistence.request_id}</code> was saved. This acknowledgement does not replay a comparison or confirm present-day facts.</p>
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
            <p>{option.description}</p>
            <p>{option.explanation}</p>
            <dl>
              <dt>Financial information</dt><dd>{option.financial.amount !== null
                ? <>{option.financial.price_basis}: {option.financial.currency} {option.financial.amount}; unit: {option.financial.unit}; period: {option.financial.period}; basis: {option.financial.basis}. Exclusions: {option.financial.exclusions?.join(', ') || 'none stated'}. Assumptions: {option.financial.assumptions?.join(', ') || 'none stated'}.</>
                : 'Unknown; no supported financial information.'}</dd>
              <dt>Total cost</dt><dd>{option.financial.total_cost === null ? 'Unknown; unknown charges are not zero.' : `${option.financial.currency} ${option.financial.total_cost}`}</dd>
              <dt>Cost difference</dt><dd>{option.financial.difference === null ? 'Unknown; no supported comparable difference.' : `${option.financial.currency} ${option.financial.difference} on the stated basis and exclusions.`}</dd>
              <dt>Current-choice baseline</dt><dd>{option.financial.baseline
                ? `${option.financial.baseline_provenance}: ${option.financial.baseline.currency} ${option.financial.baseline.amount}; ${option.financial.baseline.unit}; ${option.financial.baseline.period}; ${option.financial.baseline.basis}.`
                : 'Unspecified; no baseline or savings inferred.'}</dd>
              <dt>Environmental/resource information</dt><dd>{option.environmental.status}: {option.environmental.explanation}</dd>
              <dt>Availability</dt><dd>{option.availability.status}{option.availability.value !== null ? `: ${option.availability.value ? 'available' : 'unavailable'} at review time; no live guarantee` : ''}</dd>
              <dt>Geographic scope</dt><dd>{['country_code', 'town', 'postcode', 'conditions'].map(key => option.geographic_scope[key]).filter(Boolean).map(String).join('; ') || 'Unknown'}</dd>
            </dl>
            {option.claims.map((claim, index) => <p key={index} className="metadata">Support: {claim.support}; freshness: {claim.freshness}; requirement: {claim.requirement}. {claim.attribution?.join(', ')}; checked at {claim.checked_at?.join(', ')} (synthetic). Evidence support does not imply independent verification or a live guarantee.</p>)}
            {option.evidence.map(source => <details key={source.version_id}>
              <summary>Evidence: {source.publisher}</summary>
              <p>{source.source_reference}; original language: {source.source_language}; synthetic review: {source.reviewed_at}.</p>
              <p>Publication: {source.publication_date || 'unknown'}; update: {source.updated_at || 'unknown'}; retrieval: {source.retrieved_at || 'unknown'}; data period: {source.data_period || 'unknown'}.</p>
              {source.method && <p>Method: {source.method}; baseline: {source.baseline || 'unknown'}; assumptions: {source.assumptions?.join(', ') || 'unknown'}.</p>}
              <blockquote>{source.supporting_quote}</blockquote>
            </details>)}
          </li>)}
        </ol>
      </section>}
    </main>
  )
}

export default App
