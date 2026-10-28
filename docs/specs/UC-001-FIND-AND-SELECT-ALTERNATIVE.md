# UC-001 — Find and compare alternatives

Journey increment 1 specification and planned Tests accepted by the owner on
2026-10-10. Mandatory increment-2 research specification remains incomplete.
On 2026-10-15 the owner accepted the integration DESIGN/ADR-003 baseline and
authorized Phase 3 priority 1; no acceptance criterion changes or claim of completed
implementation/linguistic validation follows. Earlier pending DESIGN statements
below describe their dated approval history.

Approval history: the owner approved the original Intent, Actors, Preconditions and Flow
on 2026-10-07, including persistence before selection. The owner approved the
search-location amendment below on 2026-10-09. Errors, Acceptance and Tests
were draft/pending at that amendment; it did not complete SPECIFY.
On 2026-10-09 the owner approved decomposition: original steps 1–7 remain
here; original steps 8–9 move to
[UC-003](UC-003-SELECT-DISPLAYED-ALTERNATIVE.md). This does not approve the
complete specifications. The historical filename is retained to preserve links.
Decision and journey boundaries: [ADR-002](../adr/ADR-002-use-case-decomposition.md).
Decision 1 (input policy), including the input acceptance examples below, was
approved by the owner on 2026-10-09 for journey increment 1. This approval
does not approve the complete Errors, Acceptance or Tests sections. Knowledge
sufficiency, freshness thresholds and remaining policies were pending at that
approval; subsequent scoped approvals are recorded below.
Decision 2 (essential versus optional evidence), including the examples below,
was approved by the owner on 2026-10-09 with the stated clarifications. This
candidate-evidence check alone did not approve source quality, freshness, overall
sufficiency or minimum content; their subsequent scoped approvals are recorded
below. Selection eligibility and complete specification/Errors/Acceptance/Tests
acceptance remain separate.
The claim-specific source-quality policy and examples were separately approved
on 2026-10-09, including scoped provider/retailer attribution, scope-aware conflict
handling and documented calculations. Freshness, applicability and overall
sufficiency remain separate checks; this approval does not complete SPECIFY.
Freshness rules, initial periods and their scoped examples were approved by
the owner on 2026-10-10. They are project-policy defaults, not factual guarantees;
Overall sufficiency was pending at that approval; its subsequent scoped approval
is recorded below. Complete sections were pending at that review.
Overall sufficiency and minimum comparison content for increment 1 were approved
on 2026-10-10, including the focused examples below. This does not determine
UC-003 selection eligibility or complete the mandatory research scope.
The increment-1 coverage fallback, display/order, currency and persistence-failure
policies and focused examples were approved on 2026-10-10. Complete increment-1
sections were pending consolidated review at that approval; DESIGN owns transaction
and retry implementation choices.
Country/locality validation, processing-error handling and descriptive label
meanings were approved on 2026-10-10 with the owner's clarifications, recorded
in Flow/Errors below. Consolidated increment-1 sections were then presented for review.
On 2026-10-10 the owner approved AC-14 with the loading clarifications below and
accepted increment-1 Errors, Acceptance and planned Tests (AC-01–14, T-01–12).
SPECIFY is complete only for UC-001 increment 1; the owner selected DESIGN for
that scope. This accepts specification/test planning, not implementation, passing
tests, UC-003 decisions, mandatory research or full UC-001/journey completion.
On 2026-10-10 a language requirement was identified during DESIGN and proposed
separately from the earlier acceptance. The owner subsequently approved the scoped
multilingual amendment with refinements below on 2026-10-10, including its affected
acceptance examples and planned scenarios. AC-01–14/T-01–12 and their earlier
acceptance remain intact; AC-15/LAC/TL extend that baseline, not verified support.
Implementation mechanisms and final DESIGN acceptance remain pending.
On 2026-10-10 the owner separately approved O-1 and O-2: intended/reference-unverified
locality still needs applicability evidence; same-identity recovery, distinct fresh
search, truthful loading/commit status, concurrency/payload integrity and originating-
client ownership are recorded below. This does not accept the complete DESIGN/ADR-003.

## Intent

Help a user find and compare practical alternatives to a product,
service, purchase, or everyday habit or behaviour by comparing
financial and environmental/resource implications. Build reusable
Resolena knowledge from requests and evidence-backed results. Explicit selection
belongs to UC-003; its relevance signal never automatically changes factual
confidence or validation status. Trigger: submit a text request with search location.

## Actors

Primary: A user seeking an alternative, without needing an account.

Secondary: An external research service, if configured and approved,
used only when existing knowledge is insufficient and only through
minimized, non-identifying queries.

The knowledge base and database are internal system components,
not external actors.

## Preconditions

- The user can access the Alternative Finder.
- Resolena-controlled persistence is available.
- Existing knowledge may be empty; previous requests or selections
  are not required.
- External research must satisfy the approved privacy boundary
  before it can be used.

Approved location privacy: retain only granularity needed for comparison,
normally country, optionally town/postcode where justified. Location combined
with request text may identify someone; these fields do not make a query
anonymous. External research still requires query minimization and privacy
review. Raw inputs or location must not be forwarded to external LLM providers.
This increment introduces no exact-coordinate collection, IP geolocation,
background tracking or automatic location detection.

## Flow

1. Submit: The user submits a text description of a product, service,
   purchase, habit or behaviour, including their goal and any relevant
   constraints.

   Search location is where the alternative is needed, not necessarily the
   user's physical location. Switzerland is the visible, editable default
   country, clearly identified as a default rather than a detected location.
   This default is valid unless changed or cleared; no confirmation click is required.
   The user can change country and optionally enter a town/postcode.
   Choosing a country does not promise research coverage or verified alternatives.

   Approved loading (AC-14, 2026-10-10): indicate processing while handling the
   request, including required persistence. End loading when a comparison,
   insufficient-coverage outcome, clarification request or error is presented.
   Loading feedback must not imply successful saving or display invented progress percentages.

2. Interpret: The system validates and normalizes the request,
   identifying its category, current choice, goal and stated
   constraints. It does not invent missing facts.

   Approved decision 1: nonblank text with a recognisable product, service,
   purchase or habit plus a valid country is sufficient to begin. Missing goal,
   budget, current price or locality remains unspecified; infer neither
   “cheapest” nor “lowest environmental impact”. Preserve explicitly stated
   constraints. An unclear subject requires correction, whereas a recognisable
   subject without matching knowledge is insufficient coverage, not invalid input.
   Ambiguous locality requires clarification or the user's explicit choice to
   continue country-only; never silently remove it. A cleared/invalid country
   requires correction rather than silently restoring the Switzerland default.

   Approved location validation (2026-10-10): distinguish malformed input,
   demonstrated country/locality mismatch, ambiguity and unavailable reference
   knowledge. Explain demonstrated field issues and allow correction. Inability
   to verify locality does not prove invalidity: offer clarification or explicit
   country-only continuation, retaining constraints until the user chooses.
   Introduce neither external geocoding nor location detection. Format rules and
   reference-data/matching mechanisms belong in DESIGN under these requirements.

   Increment-1 scope clarification — owner-approved 2026-10-23, recorded 2026-10-25:
   [ADR-007](../adr/ADR-007-increment-1-locality-matching-scope.md) limits
   reference-backed locality matching to the approved CH/LI release. Outside CH/LI,
   existing honest clarification and explicit country-only or user-confirmed/reference-unverified
   continuation satisfy Priority 5 locality handling, preserving independent textual
   constraints, minimal retention and evidence-based applicability. GeoNames
   cities500/admin1 preparation, review and integration are deferred beyond increment 1
   as separately authorized future capability. The approved GeoNames countryInfo
   catalogue and DE/FR/IT/EN remain unchanged; no other behavior or criterion/test identifier changes.

3. Retrieve: The system searches existing Resolena knowledge for
   relevant alternatives and supporting evidence.

4. Assess: The system assesses relevance, evidence quality and
   freshness to determine whether existing knowledge is sufficient.

   Use search location in relevance and sufficiency assessment: delivery area
   for products, service coverage for services, practical applicability for
   habits/behaviours. Knowledge from another market is not automatically
   sufficient. Apply neither a universal distance filter nor a Switzerland-only
   boundary. Validation outcomes follow step 2; presentation order follows step 6.
   A later ranking policy would require separate approval.

   Approved decision 2: essential evidence establishes relevance to the
   recognisable subject or satisfaction of an explicit goal/constraint,
   including geographic applicability where needed for usability. A “cheaper”
   goal requires a supported cost comparison even without a numeric budget.
   Missing essential evidence leaves the requirement unverified; evidence
   contradicting it establishes failure of that requirement. Unknown delivery
   is unverified; confirmed non-delivery fails a delivery constraint. An
   unsupported candidate does not disqualify other supported candidates.
   Passing this check does not establish overall knowledge sufficiency.

   Approved source-quality policy: identify the publisher, source reference and
   passage/data supporting each claim; record publication/update dates when
   supplied and the actual review date without inventing dates. Accept a source
   only for claims within its competence and product/market/condition scope.
   Provider/retailer evidence supports their own scoped statements: label it as
   provider-/retailer-stated, not independent verification or guaranteed price,
   stock or availability.

   Financial/environmental advantages require supporting inputs and a clear
   comparison basis; environmental comparisons also require a documented method
   and scope. Vague marketing slogans are insufficient. Traceable source inputs
   plus a documented calculation, baseline and assumptions can support a calculated
   comparison; a source need not contain the exact calculated result.

   Before declaring conflict, compare product variant, geography, conditions and
   applicable dates. Only unresolved disagreement about the same scoped claim
   triggers the conflict rule: do not label that claim verified until reviewed.
   Apply the essential/optional distinction to the affected information while
   retaining other supported candidates. Assess quality per claim without scores,
   weights or mandatory citation counts, using stored reviewed evidence in
   increment 1. Source quality is separate from the freshness, applicability and
   overall-sufficiency checks approved below.

   Approved freshness policy (2026-10-10), per claim: price and stock/availability
   windows are 24 hours; service coverage 90 days; product specifications and
   environmental evidence 365 days. Days mean elapsed 24-hour periods since
   actual review, compared using consistent, unambiguous timestamps. Respect
   earlier source expiry and known invalidating changes. Evidence is fresh only
   before its expiry instant; at that instant it is expired. Expiry of one claim
   does not automatically invalidate unrelated supported claims for the candidate.

   Preserve publication/update dates, retrieval dates, actual review dates and
   relevant underlying data periods separately. Retrieval is not review; review
   checks the relevant source and applicability. Reopening stored evidence does
   not renew it. Missing publication/update dates stay unknown: a documented
   review of a current provider page may establish an observation date for its
   scoped statement. If an underlying data period matters and cannot be established,
   temporal applicability remains unverified. An old environmental study's data
   does not become contemporary through a new review; check method, baseline,
   geography and data period. Do not invent missing timestamp precision; if needed
   to establish freshness/expiry but unavailable, leave that assessment unresolved.

   Increment 1 uses prepared, reviewed evidence without automatic refreshing.
   Future automated review may qualify only under a separately approved validation
   procedure; perpetual manual review is not required by this decision. Expired
   essential evidence cannot establish a current requirement; optional information
   may be omitted or labelled unknown, leaving unrelated claims/candidates intact.
   Insufficient coverage follows the approved increment-1 fallback below.

   Approved overall sufficiency (2026-10-10): existing knowledge is sufficient
   when at least one candidate addresses the recognisable subject, supports all
   explicit goals/constraints, passes the approved essential-evidence, source-quality
   and per-claim freshness checks, and has supported search-location applicability
   wherever necessary for usability. It must meet the minimum comparison content
   below. Assess candidates individually: unsupported/unverified essential evidence,
   unresolved essential conflict or a contradicted requirement prevents that
   candidate from qualifying; other qualifying candidates can establish sufficiency.

5. Research when needed: If knowledge is insufficient, the system
   uses an approved research integration with minimized,
   non-identifying queries. Sufficient existing knowledge is reused
   without new research.

   Increment 1 boundary: if no candidate qualifies, explain that existing knowledge
   cannot support a comparison and research is unavailable in this increment.
   Explain the relevant limitation and allow explicit editing/resubmission without
   relaxing constraints or claiming that no alternatives exist. Retain the valid
   request and insufficient-coverage outcome with minimal justified location and
   no invented alternatives or selection. Do not persist invalid submissions as
   application search records. This authorizes no background research, automatic
   retry, saved-history interface or additional collection; the mandatory approved
   research route remains increment 2 scope. Save-failure handling is in Errors.

6. Prepare comparison: The system prepares a small set of alternatives
   with financial and environmental/resource information, explanations,
   evidence references and confidence/validation labels. Unknown values
   and assumptions are identified explicitly.

   Distinguish verified availability from unknown availability. Label estimated
   prices and relevant geographic limitations. Do not invent availability,
   prices, exchange rates or local coverage; increment-1 currency follows the policy below.

   Every displayed factual claim requires supporting evidence, whether essential
   for matching or optional. Optional information may be omitted or labelled
   unknown; its absence must not imply a financial or environmental advantage.

   Present scoped statements with their checked-at time, not as guaranteed live
   prices or availability. Freshness alone does not establish source quality,
   applicability, independent verification or overall sufficiency.

   Approved descriptive labels (2026-10-10): keep evidence support, freshness and
   requirement satisfaction distinct, not mutually exclusive states. Supported
   evidence can establish a contradicted requirement. “Evidence-supported” alone
   means neither fresh, independently verified nor satisfying every constraint.
   Apply the essential/optional rules to unknown, disputed or contradicted
   information; labels cannot turn failed candidates into qualifying matches.
   Exact UI wording and internal representations belong in DESIGN.

   Approved minimum content: explain what the alternative is and why it addresses
   the request. Show financial and environmental/resource implications as supported
   information or explicitly unknown; at least one dimension must contain useful,
   evidence-backed information specific to that alternative. Generic statements
   do not qualify. Include evidence references, source attribution, checked-at times,
   assumptions, availability status and relevant geographic limitations. An advantage
   is not mandatory unless explicitly requested; “cheaper” needs evidence establishing
   that comparison. If the current choice/baseline is insufficiently specified, show
   supported alternative information without inventing a baseline, savings or impact
   advantage. Clearly identify a single result without implying exhaustive coverage
   or “best” status. Failed candidates must not appear as qualifying matches;
   UC-003 eligibility remains pending.

   Approved display policy: show up to three qualifying alternatives in stable
   alphabetical order with deterministic ties. This is presentation order, not
   ranking. Explain when additional qualifying results are omitted by the limit.
   Preserve displayed identities in the persisted comparison for subsequent selection.

   Approved currency policy: retain source currency without conversion. Calculate
   differences only from supported, comparable inputs (currency, units, periods
   and cost basis); disclose comparison basis, assumptions and material exclusions.
   Unknown charges are not zero and cannot support total-cost or “cheaper” claims
   where they could change the conclusion. Otherwise the difference/advantage
   remains unknown and cannot satisfy an explicit cheaper goal.

7. Persist and present: The system persists the original request,
   normalized interpretation, alternatives prepared for display and
   their supporting evidence, then presents the comparison. Newly
   acquired knowledge becomes available for future retrieval, subject
   to the same quality checks.

   Persist only the search-location granularity justified for this comparison.

   Search results are saved before selection. If the user leaves without
   choosing, the saved request and results remain; no selection is
   inferred.

   Required persistence must succeed before successful comparison presentation;
   partial writes must not appear as a completed result. Preserve entered fields
   on the current page and allow explicit retry, reassessing applicability,
   evidence and freshness. Transaction/retry implementation belongs in DESIGN.

Outcome/boundary: a persisted, evidence-backed comparison is presented without
requiring a choice. Original steps 8–9 continue in
[UC-003](UC-003-SELECT-DISPLAYED-ALTERNATIVE.md#flow) when the user explicitly
selects. Both existing-knowledge and research journeys use this same boundary.

Deferred: optional permission-based “Use my location”, with a manual fallback,
may be considered later. It is neither implemented nor authorized for
implementation. Location remains part of UC-001, not a separate use case.

### Language amendment — owner-approved 2026-10-10

The earlier proposal was accepted with refinements on 2026-10-10. Target written
standard German (`de`), French (`fr`), Italian (`it`) and English (`en`).
Support remains **unverified until tested**. Swiss standard German spelling may be
evaluated within `de`; Swiss-German dialects, other languages and universal
understanding are not promised. Mechanism remains provisional: reviewed aliases
and templates may support a bounded increment, not general automatic translation.

| ID | Approved behaviour |
|---|---|
| L-01 — Recognition/scope | Recognize language automatically; allow unknown/out-of-scope rather than force all input into four labels. Clear supported requests need no routine language selection. Names/places/shared words alone do not establish language. |
| L-02 — Interpretation | Preserve original request and raw spans; distinguish interpreted/translated content from it. Preserve names/place identities, exact amounts/currencies/units, negation, explicit goals/constraints. Clarify uncertainty affecting interpretation, constraints or correctness; never guess numeric meaning or invent missing goals. |
| L-03 — Short/mixed/unsupported input | An understandable short subject can begin retrieval despite uncertain language. Prefer an existing user-selected explanation language or a supported browser language, with easy correction, rather than require clarification solely for language ambiguity. Understood mixed text retains every constraint; use its clear primary language, otherwise that preference path. If meaning remains uncertain, clarify it. If no supported explanation language can be established, offer a one-time choice with a brief DE/FR/IT/EN prompt. Failure to interpret language is a capability limitation with rephrasing/clarification, distinct from invalid input, insufficient application knowledge and technical processing failure; preserve fields. |
| L-04 — Cross-language knowledge | Retrieve suitable prepared evidence without a request/source-language equality filter, through reviewed meaning mappings. Apply all existing relevance, essential-evidence, quality, freshness, location and content checks. Unreviewable original meaning leaves the affected claim unverified; assess other candidates independently. No universal evidence-language support claim. |
| L-05 — Result language/provenance | Produce explanations, assumptions, unknown/availability/estimate labels and request-specific outcomes in the recognized or clarified request language, or the preference/correction language used for understandable language-ambiguous input. Keep original source/reference/language available; mark translated paraphrases as derived, not original quotations, corroboration or independent verification. Translation never renews review/freshness or invents facts; language certainty and evidence validation remain separate. Full UI localization/static navigation/initial controls are separate scope. |
| L-06 — Country/privacy/persistence | Recognition, browser language and explanation choices never determine search country; CH default and explicit location remain independent. All recognition/interpretation/rendering stays within Resolena-controlled processing; no user/request-derived text to external translation services or LLM providers. Existing evidence/data/privacy rules remain binding. Prepare faithful explanations before required persistence; save necessary language/derivation context with the original request/comparison, without introducing a user language profile. |

At this language acceptance, O-1/O-2 were still pending; their later approval is below.
Scoped language acceptance does not approve a model/mechanism or final DESIGN,
authorize implementation, relax evidence/privacy or complete research/UC-003.

### Locality and recovery — owner-approved 2026-10-10

O-1: explicitly clarified locality may remain reference-unverified. User confirmation
establishes intended locality, not verified geographic applicability; qualification
still requires supporting evidence under all existing constraints.

O-2: explicit recovery uses the same submission identity and unchanged captured
payload. If committed, return save acknowledgement without historical claims as
fresh; clearly offer a separate explicit fresh-search action with new identity and
reassessment. If not committed, reassess applicability/evidence/freshness before
saving under the same identity. An absent record does not itself prove rollback
while an earlier attempt may run. No automatic retry or public history interface.

Concurrent same-key submissions cannot create duplicate completed search records;
the same key with changed payload is rejected. Recovery is scoped to the originating
client: knowing an identifier alone cannot expose another user's request, results
or save status. Loading covers handling/required persistence and ends on acknowledgement,
result (including clarification) or error; unknown commit state stays explicitly
unknown, never a saved/unsaved certainty. Ownership, concurrency and retry enforcement
belong to DESIGN; these approvals do not implement them or accept final DESIGN.

## Errors

Consolidated increment-1 Errors accepted by the owner on 2026-10-10.
Mandatory increment-2 research and UC-003 errors remain separate and pending.
All error responses preserve entered
fields; processing/save failures allow explicit retry, never automatic retry.
Retry that prepares a comparison reassesses applicability, evidence and freshness
without renewing cached review dates. O-2's committed recovery acknowledges saving
only; it does not assert a newly assessed/current comparison.

| Condition | Required observable handling |
|---|---|
| Blank/unclear subject; cleared/invalid country; malformed locality | Explain the field issue and allow correction without inventing a subject or restoring the default. Missing optional fields are valid; invalid submissions create no application search record. |
| Demonstrated country/locality mismatch | Explain the demonstrated inconsistency and allow correction; do not treat missing reference knowledge as proof of mismatch. |
| Ambiguous or unverifiable locality | Distinguish ambiguity from unavailable reference knowledge. Offer clarification or explicit country-only continuation; never silently drop location constraints or use external geocoding/detection. |
| Retrieval/interpretation/assessment/preparation technical fault | Report failed processing, not successfully assessed insufficient coverage or a completed comparison; preserve fields and allow explicit retry. |
| Successful assessment finds no qualifying candidate | Apply Flow step 5's increment-1 coverage outcome, retaining the valid request/outcome with justified location. Unknown availability/other-market evidence are assessment limitations, not automatically invalid input or proof of global unavailability. |
| Required comparison persistence fails, including partial writes | Report save failure; no successful comparison presentation or completed partial-write result. Preserve fields and allow explicit retry as specified in step 7. |
| Retaining a valid insufficient request fails | Show both the coverage limitation and save failure; never claim the request/outcome was saved. |

Separate pending scope: increment-2 research failure/privacy-review fallback,
provider and outbound query fields; UC-003 selection eligibility/errors; the
selection-versus-realized-savings clarification. Research minimization remains
binding; no unreviewed inputs may be sent. The earlier country-first/minimal
locality research recommendation remains a proposal for increment 2.
Increment 1 has no ranking formula; later ranking changes require approval.
DESIGN owns format/reference/matching mechanisms, transaction/retry mechanics,
deterministic tie-breaking and exact label wording/representations.

### Approved language handling

Owner-approved 2026-10-10: understandable language ambiguity uses L-03's preference/
correction path; uncertainty affecting meaning needs targeted clarification.
An inability to interpret language is a capability outcome with rephrasing, not
invalid input, insufficient knowledge or a technical processing failure. An actual
recognition/interpretation/rendering fault is a processing error with explicit retry.
Retain fields/constraints; no external-service fallback. Only a valid, understood,
successfully assessed request with no qualifying evidence follows persisted
insufficient coverage. No premature comparison/save success claims.

## Acceptance

Consolidated increment-1 Acceptance accepted by the owner on 2026-10-10,
including AC-14 and its clarified loading boundary. R-01–R-14 index requirements;
AC-01–AC-14 state acceptance boundaries. E identifiers reference examples;
T identifiers refer to the accepted planned Tests, not executed checks.
Earlier scoped approvals/dates remain intact; research and UC-003 are not accepted here.
The subsequently approved language amendment adds AC-15/LAC/TL and extends
AC-01/03/04/10–14 where language, provenance, outcome meanings and loading apply;
it changes neither the settled evidence checks nor the earlier approval dates.

| Requirement / canonical location | Acceptance criterion | Example references | Planned tests |
|---|---|---|---|
| R-01 — Input, Flow 1–2 | AC-01: recognisable subject/valid country starts retrieval; optional omissions stay unspecified and explicit constraints survive. Unclear subject needs correction; absent knowledge is not invalid input. | E-IN-01–07, E-EV-05 | T-01, T-11 |
| R-02 — Manual location/validation, Flow 1–2 and Errors | AC-02: visible editable default needs no extra confirmation; chosen country/locality governs the search. Distinguish malformed/mismatch/ambiguous/unverifiable input; correction or explicit country-only choice preserves user control. | E-IN-05–07, E-LO-01–04, E-CL-01–03 | T-02, T-11 |
| R-03 — Retrieval/applicability, Flow 3–4 | AC-03: retrieve before assessment; apply product delivery, service coverage or habit applicability to the search location. Other-market knowledge is not automatically sufficient; no universal distance or Swiss-only filter. | E-EV-04/06, E-LO-02/03/05/07 | T-03, T-10, T-11 |
| R-04 — Essential/optional evidence and source quality, Flow 4/6 | AC-04: every displayed factual claim is traceable to competent scoped support or documented calculation; explicit goals/constraints need essential evidence. Compare scopes before conflict; missing, disputed and contradicted information cannot establish qualifying requirements. | E-EV-01–09, E-SQ-01–07 | T-03, T-11 |
| R-05 — Freshness, Flow 4/6 | AC-05: per-claim approved windows/earlier expiry apply, with expiry at the boundary and dates/data periods kept distinct. Reopening evidence never renews review; checked-at statements are not live guarantees. | E-FR-01–08 | T-04, T-09, T-11 |
| R-06 — Sufficiency/minimum content, Flow 4/6 | AC-06: one qualifying candidate suffices; both dimensions are supported/explicitly unknown and at least one has useful candidate-specific evidence. No invented baseline/advantage; failed candidates stay excluded. | E-SU-01–06, E-EV-08/09 | T-03, T-11 |
| R-07 — Increment-1 coverage, Flow 5 and Errors | AC-07: successful assessment with zero qualifiers retains the valid request/outcome, explains the limitation and permits explicit editing/resubmission without invented matches, research, history UI or automatic retry. Invalid submissions are not search records. | E-IN-03, E-OP-01–03, E-LO-07 | T-01, T-08, T-10, T-11 |
| R-08 — Display/identity, Flow 6–7 | AC-08: up to three qualifiers appear in stable alphabetical order with deterministic ties and an omission explanation. Single results imply neither best nor exhaustive coverage; displayed identities remain tied to the persisted comparison. | E-SU-01/05, E-OP-04/05 | T-05, T-08, T-11 |
| R-09 — Currency/comparable costs, Flow 6 | AC-09: retain source currencies; supported differences disclose comparable basis/assumptions/material exclusions. Unknown charges are never zero or grounds for an unjustified total-cost/cheaper claim. | E-SQ-07, E-OP-06/07 | T-06, T-11 |
| R-10 — Persistence boundary, Flow 7 and Errors | AC-10: request, interpretation, displayed alternatives/identities and evidence persist before successful presentation. Partial/save failures never appear completed/saved; a coverage-save failure is separately identified. Results remain without inferred selection. | E-OP-03/05/08, E-SU-06 | T-08, T-09, T-11 |
| R-11 — Processing failure/retry, Errors and Flow 7 | AC-11: processing failure, assessed coverage limitation and save failure are distinct; fields survive and retry is explicit. Retry reassesses applicability/evidence/freshness without renewing cached review dates. | E-OP-03/08/09, E-CL-04 | T-09, T-11 |
| R-12 — Descriptive labels, Flow 6 | AC-12: evidence support, freshness and requirement satisfaction remain separate meanings. Labels retain source attribution/uncertainty/estimates/limitations and cannot turn failed candidates into matches. | E-EV-06/07, E-SQ-01/02/06, E-FR-08, E-LO-06, E-CL-05/06 | T-07, T-11 |
| R-13 — Privacy/bounded collection, Preconditions and Flow 1/5/7 | AC-13: retain only justified country/locality in Resolena-controlled persistence; identifying combinations remain sensitive. No external LLM forwarding, geocoding, detection, coordinates/tracking, research or automatic refresh in increment 1. | E-OP-01, E-LO-01–03 | T-08, T-10, T-11 |
| R-14 — Loading feedback, Flow 1 and [accepted scope](../ARCHITECTURE.md#accepted-scope) | AC-14: indicate request processing including required persistence; end loading on comparison, insufficient coverage, clarification or error. Never imply successful saving or invent progress percentages. | E-LD-01 | T-12 |
| R-15 — Multilingual amendment, L-01–06 and approved language handling | AC-15: automatically handle targeted standard languages without routine selection; preserve meaning and original provenance, use preference/correction for understood language ambiguity, distinguish interpretation capability limits, retrieve reviewed cross-language evidence and render faithful explanations locally without setting country. Support requires validation. | LAC-01–13 | TL-01–04; extensions of T-01/08/10–12 |
| R-16 — Clarified locality, O-1 | AC-16: user-confirmed intended locality remains reference-unverified; only supporting applicability evidence permits qualification. | O-1; E-EV-04/06 | T-13 |
| R-17 — Recovery/identity/ownership, O-2 | AC-17: explicit same-identity/unchanged-payload recovery produces committed save acknowledgement or reassessed same-key save; distinct fresh search is offered. Same-key races cannot duplicate records, changed payload is rejected, identifier-only access reveals nothing belonging to another client. Loading ends truthfully; uncertain commits remain unknown. | O-2; E-OP-08/09 | T-13 |

Approved decision 1 input examples — owner-approved on 2026-10-09:

| Scenario | Given / When / Then |
|---|---|
| E-IN-01 — Recognisable subject, optional fields absent | Given “Repair my bicycle” and Switzerland with no goal, budget, current price or locality, when submitted, then input validation permits retrieval and absent fields remain unspecified; no cheapest/lowest-impact goal is inferred. |
| E-IN-02 — Blank or unclear subject | Given whitespace-only text or “something better” without a recognisable subject, when submitted, then ask for a subject correction rather than retrieve or invent one. |
| E-IN-03 — Recognisable subject, no knowledge | Given a recognisable product/service/purchase/habit and valid country but no matching knowledge, when processed, then input is valid and the outcome is insufficient coverage; the increment-1 fallback was subsequently approved below. |
| E-IN-04 — Explicit constraints | Given “Repair my bicycle without replacing it” and a valid country, when interpreted, then preserve the repair/no-replacement constraint rather than silently substitute buying a bicycle. |
| E-IN-05 — Ambiguous locality | Given a locality that cannot be uniquely resolved, when submitted, then ask for clarification or the user's explicit choice to continue country-only; retain it until that choice is made. |
| E-IN-06 — Explicit country-only continuation | Given ambiguous locality, when the user explicitly chooses country-only, then proceed using the chosen country without assuming a locality. |
| E-IN-07 — Cleared country | Given the user clears the default country, when submitted, then request a valid country without silently restoring Switzerland. |

Approved decision 2 evidence examples — owner-approved on 2026-10-09;
synthetic situations, not claims about actual products/services:

| Scenario | Given / When / Then |
|---|---|
| E-EV-01 — Optional price unknown | Given a laptop alternative with evidence supporting equivalent purpose and Swiss delivery, but no price and no budget/cheaper goal, when assessed, then price may remain omitted/unknown without implying cheaper or environmentally better; this passes only the essential-evidence check. |
| E-EV-02 — Explicit budget | Given the same alternative and an explicit budget constraint with price unknown, when assessed, then budget compliance is unverified and the candidate cannot be claimed to satisfy that constraint. |
| E-EV-03 — Explicit cheaper goal | Given “a cheaper alternative” without a numeric budget, when a supported cost comparison is missing, then the cheaper goal is unverified; no financial advantage is inferred. |
| E-EV-04 — Local service coverage | Given a service needed in a stated town but no supporting coverage evidence for that town, when assessed, then local applicability is unverified rather than a verified local match. |
| E-EV-05 — Missing current-price baseline | Given no current price and no cheaper goal, when interpreting/assessing, then the input remains valid and the missing baseline does not itself invalidate relevance; it cannot support a numerical savings claim. |
| E-EV-06 — Unknown versus contradicted delivery | Given a delivery constraint, when delivery evidence is missing, then label the requirement unverified; when evidence confirms non-delivery to that location, then it fails the delivery constraint. Neither outcome decides UC-003 selection eligibility. |
| E-EV-07 — Optional factual claim unsupported | Given no evidence for an optional environmental advantage, when preparing the comparison, then omit it or mark it unknown; do not display an unsupported advantage or infer one from missing information. |
| E-EV-08 — Candidate independence | Given an unsupported candidate and another with supported relevance/goals/constraints, when assessed, then the first does not disqualify the second. |
| E-EV-09 — Partial check only | Given a candidate passes this evidence distinction, when assessing overall sufficiency, then still apply the separately approved source-quality, freshness, applicability and minimum-content checks below; this partial check alone does not establish sufficiency. |

Approved claim-specific source-quality examples — owner-approved on 2026-10-09;
synthetic situations, not claims about actual providers/products:

| Scenario | Given / When / Then |
|---|---|
| E-SQ-01 — Provider coverage statement | Given a stored provider page explicitly covers the requested town, when assessed, then it supports that scoped provider-stated coverage, labelled accordingly; source acceptance does not mean independent verification or guaranteed availability, and freshness/applicability remain separate. |
| E-SQ-02 — Retailer listing | Given a retailer listing for a specific variant, currency, market and conditions, when assessed, then it supports that scoped retailer-stated price; do not imply guaranteed price/stock/availability or a universally cheapest option. |
| E-SQ-03 — Unsupported environmental slogan | Given “eco-friendly” marketing without supporting analysis, when assessed, then it cannot support a factual environmental advantage; omit the advantage or label it unknown. |
| E-SQ-04 — Documented environmental comparison | Given a report with supporting data, documented method, baseline and scope, when assessed, then it passes the source-quality check for the comparison it supports; freshness and applicability to the request remain separate. |
| E-SQ-05 — Different scoped claims | Given differing statements about different variants, geographies, conditions or applicable dates, when compared, then do not declare a conflict merely because their values differ. |
| E-SQ-06 — Same scoped claim conflicts | Given unresolved disagreement about the same variant, geography, conditions and applicable dates, when assessed, then do not label the disputed claim verified until reviewed; other supported candidates remain unaffected. |
| E-SQ-07 — Calculated comparison | Given traceable source inputs plus a documented calculation, baseline and assumptions, when assessed, then they may support the calculated result even if no source states that exact result; currency/content policies, freshness and applicability remain separate. |

Approved freshness examples — owner-approved on 2026-10-10;
synthetic timestamps/claims, checked with a controlled clock when tests are implemented:

| Scenario | Given / When / Then |
|---|---|
| E-FR-01 — Exact expiry boundary | Given price reviewed at 2026-10-10T10:00:00+02:00 without earlier expiry/change, when assessed at 2026-10-11T09:59:59+02:00, then it passes freshness; at 2026-10-11T10:00:00+02:00 or later it is expired. Stock/availability uses the same 24-hour window. |
| E-FR-02 — Earlier source expiry/change | Given that source instead expires at 2026-10-10T18:00:00+02:00, when assessed at that instant, then it is expired despite the default window; a known invalidating change overrides the window for the affected claim too. |
| E-FR-03 — Unrelated claims | Given an expired price and a separately reviewed product specification still within its 365-day window with no invalidating change, when assessed, then the specification remains usable for its supported scope; expired price cannot establish a current budget requirement. |
| E-FR-04 — Cached evidence reopened | Given stored evidence with recorded publication/update, retrieval and review dates, when reopened or retrieved again without checking the source/applicability, then its actual review date and expiry do not change. |
| E-FR-05 — Elapsed days and precision | Given a coverage review timestamp, when assessed at review plus 90 elapsed 24-hour periods, then it is expired regardless of calendar/clock changes. If review/expiry precision or time zone is insufficient to determine the instant, then freshness remains unresolved rather than inventing precision. |
| E-FR-06 — Missing publication/update date | Given an undated current provider page and a documented source/applicability review, when assessed, then the publication/update date stays unknown and the actual review may establish the scoped observation date; mere retrieval does not. |
| E-FR-07 — Environmental data period | Given an environmental report reviewed within 365 days but a necessary underlying data period is unknown, when assessed, then temporal applicability stays unverified. A new review does not make historical data contemporary or remove its original dates/limitations. |
| E-FR-08 — Checked-at statement | Given usable retailer/provider evidence, when its scoped price/availability statement is presented, then show its checked-at time and attribution without claiming guaranteed live price/stock/availability. |

Approved increment-1 sufficiency/content examples — owner-approved on 2026-10-10;
synthetic situations with other required checks passing unless stated otherwise:

| Scenario | Given / When / Then |
|---|---|
| E-SU-01 — One qualifying alternative | Given one repair option with supported applicability and a fresh attributed quoted cost, while environmental information is unknown, when assessed/presented, then knowledge is sufficient and the single result is identified without best/exhaustive-coverage claims. |
| E-SU-02 — Generic information only | Given candidates with only generic cost/environmental statements and no useful supported information specific to them, when assessed, then minimum content is unmet even if subject matching passes. |
| E-SU-03 — Explicit advantage goal | Given an explicit cheaper goal with no supported cost comparison, when assessed, then the candidate does not qualify; without an explicit advantage goal, no advantage is mandatory. |
| E-SU-04 — Unspecified baseline | Given a recognisable request but an insufficiently specified current choice/baseline, when presenting a qualifying alternative, then show its supported financial/environmental information without invented baseline, savings or environmental advantage. |
| E-SU-05 — Mixed candidates | Given one qualifying candidate and others failing essential evidence/constraints, when assessed, then knowledge can be sufficient through the qualifying candidate and failed candidates are not presented as qualifying matches. |
| E-SU-06 — Scope boundary | Given increment-1 comparison sufficiency is established, when tracking completion, then UC-003 selection eligibility and the full mandatory research journey remain unresolved/incomplete; complete Errors/Acceptance/Tests are not approved by this check. |

Approved increment-1 outcome/display/currency/persistence examples — 2026-10-10;
synthetic scenarios; Acceptance/Tests were pending at this scoped approval,
then accepted for increment 1 in the consolidated review on 2026-10-10:

| Scenario | Given / When / Then |
|---|---|
| E-OP-01 — Valid insufficient request | Given valid input and no qualifying candidate, when persistence succeeds, then retain the request and coverage outcome with only justified location, show the limitation without invented matches, and permit explicit editing/resubmission; no research, automatic retry or selection is inferred. |
| E-OP-02 — Invalid submission | Given invalid input, when validation fails, then request correction without creating an application search record. |
| E-OP-03 — Coverage plus save failure | Given a valid insufficient request whose retention fails, when responding, then distinguish insufficient coverage from save failure and never state that the request/outcome was saved. |
| E-OP-04 — Display cap and ties | Given four qualifying alternatives, when presented, then show three in stable alphabetical order, use deterministic ties and explain the omission; order conveys no best/ranking claim. |
| E-OP-05 — Display identity | Given a persisted displayed comparison, when an alternative is subsequently referenced for selection, then it refers to that comparison's displayed identity, not a different live/reordered alternative. UC-003 selection eligibility remains pending. |
| E-OP-06 — Currency/basis | Given a CHF baseline and EUR alternative, when presenting costs, then retain each source currency without conversion or numerical cross-currency difference. Comparable supported calculations disclose baseline, units, period, assumptions and material exclusions. |
| E-OP-07 — Unknown charges | Given an apparently lower listed price with unknown charges that could change the conclusion, when comparing, then do not treat them as zero or assert total cost/cheaper status; disclose the limitation. |
| E-OP-08 — Comparison save failure | Given a qualifying prepared comparison but failure in a required save, when responding, then show a save error, preserve entered fields and offer explicit retry; no successful comparison or completed partial-write result is shown. |
| E-OP-09 — Retry reassessment | Given an explicit retry after evidence expires or applicability changes, when processing it, then reassess applicability/evidence/freshness and use the new qualifying set or approved coverage outcome without renewing cached review dates. |

Location examples retained from the amendment — reconciled and accepted for
increment 1 on 2026-10-10. E-LO-08 is deferred mandatory research,
not an increment-1 acceptance criterion.

| Scenario | Given / When / Then |
|---|---|
| E-LO-01 — Default country | Given a new request, when location is shown, then Switzerland is visible/editable and labelled as a default, valid without an additional confirmation click unless changed/cleared, without detection or a coverage promise. |
| E-LO-02 — Changed country | Given another country is chosen, when the request is assessed, then that country governs relevance/sufficiency without automatic Swiss fallback or promised research coverage. |
| E-LO-03 — Country-only search | Given no town/postcode, when searching, then country-level comparison is possible without requiring locality; finer availability uncertainty stays explicit. |
| E-LO-04 — Ambiguous town/postcode | Given ambiguous locality input, when validated, then offer clarification or explicit country-only continuation without silently removing locality; matching mechanisms belong in DESIGN. |
| E-LO-05 — Different-market knowledge | Given relevant-looking knowledge from another market, when assessed, then applicability/evidence for the search location is checked rather than automatically judged sufficient. |
| E-LO-06 — Unknown availability | Given availability lacks supporting evidence, when presented, then it is labelled unknown, distinct from verified availability; estimated prices and geographic limitations are labelled, without invented rates/coverage. |
| E-LO-07 — Unsupported market | Given research coverage is unsupported and no stored candidate qualifies, when processing increment 1, then use the approved coverage/save outcome without a global unavailability claim; increment-2 research fallback remains pending. |
| E-LO-08 — Minimized research | Given research is needed after retrieval/assessment, when a query is prepared, then only reviewed, necessary non-identifying detail is sent; identifying combinations are not assumed anonymous and raw inputs/location do not go to external LLMs. |

Additional location/error/label examples accepted in the 2026-10-10
consolidated increment-1 review; synthetic fixtures:

| Scenario | Given / When / Then |
|---|---|
| E-CL-01 — Malformed locality | Given locality input demonstrated to violate its applicable format, when validated, then explain the format issue and allow correction; do not silently remove it. |
| E-CL-02 — Demonstrated mismatch | Given reviewed reference knowledge establishes that the locality belongs to a different chosen country, when validated, then explain the mismatch and allow correction, rather than silently substituting country/locality. |
| E-CL-03 — Reference knowledge unavailable | Given no reference knowledge can verify the locality, when validated, then do not declare it invalid; distinguish this limitation from ambiguity and offer clarification or explicit country-only continuation. |
| E-CL-04 — Failed processing | Given retrieval or assessment fails, when responding, then report processing failure rather than assessed insufficient coverage or successful saving; retain fields and permit explicit retry, never automatic retry. |
| E-CL-05 — Supported contradiction | Given fresh, source-supported evidence proves non-delivery under a delivery constraint, when assessing, then evidence support/freshness coexist with failed requirement satisfaction; the candidate does not qualify. |
| E-CL-06 — Support is not freshness | Given source-supported but expired evidence, when labelling, then support alone implies neither freshness, independent verification nor satisfaction of all constraints; essential/optional rules still determine use. |

AC-14 and loading example accepted with clarifications on 2026-10-10:
E-LD-01: given request handling is underway, including required persistence,
when waiting for an outcome, then indicate processing without invented progress
percentages or implied save success; when a comparison, insufficient coverage,
clarification or error is presented, end loading. Exact appearance/wording
belongs in DESIGN; no implementation is established by this approval.

UC-001 increment-1 acceptance ends at the persisted comparison or the defined
coverage/clarification/error outcome. It does not accept UC-003 selection policies, mandatory
increment-2 research, or the complete UC-001 specification. E-LO-08 preserves
the approved research/privacy guarantee for subsequent specification work;
research fallback/provider/outbound fields remain pending. Comparison-to-selection
journey validation remains pending across both UCs; no selection is inferred when
the user leaves, and evidence integrity remains UC-003's boundary.
The selection-versus-realized-savings clarification remains proposed, not approved.

### Language acceptance examples

LAC/AC-15 accepted as the scoped amendment on 2026-10-10, extending AC-01–14.
Synthetic requests;
assume a genuinely reviewed qualifying prepared record for examples requiring a
comparison, without asserting that such application knowledge already exists.

| ID / input situation | Approved observable outcome |
|---|---|
| LAC-01 — DE: “Ich möchte mein Fahrrad reparieren, ohne es zu ersetzen.” | Recognize standard German; preserve repair/no replacement; render German explanations without a language selector. With the same CH context/evidence, qualification matches the parallel FR/IT/EN requests. |
| LAC-02 — FR: “Je veux réparer mon vélo sans le remplacer.” | Recognize French, retain the negative replacement constraint, and explain in French; do not change CH to France. |
| LAC-03 — IT: “Vorrei riparare la mia bicicletta senza sostituirla.” | Recognize Italian, retain repair/no replacement, and explain in Italian; no inferred Italian country/currency. |
| LAC-04 — EN: “I want to repair my bicycle without replacing it.” | Recognize English and explain in English with the same preserved meaning; language does not imply UK/US location or market coverage. |
| LAC-05 — Short “Velo”/valid country | Preserve the recognisable subject and retrieve. With an existing French choice, explain in French; otherwise with supported browser German, explain in German, expose easy correction and do not claim German was detected. CH remains unchanged. Ask about meaning only if it affects correctness; without a supported preference, offer a one-time language choice. |
| LAC-06 — “Please repair my bicycle, sans remplacement”; balanced “Fahrrad repair, sans remplacement” | If the first has reliably understood meaning/primary English, explain in English while retaining the French no-replacement clause. For understood balanced text, use a supported existing/browser preference with correction; clarify only unresolved meaning or absent supported explanation choice. Never discard another-language constraint. |
| LAC-07 — “Réparer le vélo Acme X-2 à Genève, sans le remplacer; budget 49,90 CHF pour une réparation.” | Preserve Acme X-2, entered Genève plus any reviewed place identity, 49,90 CHF's magnitude, per-repair basis and negation. Derived labels do not rename the product, convert currency/units or weaken the budget/constraint. |
| LAC-08 — “1,200 CHF” has unresolved magnitude | Ask for amount clarification; do not resolve the separator using detected language or the CH default and then assert budget compliance. |
| LAC-09 — FR request, suitable reviewed EN evidence | Retrieve/assess the original source under the same location/freshness rules; provide French evidence-bound explanation marked as translated/paraphrased, retaining original citation/excerpt/language and review date. A translated copy is not another independent source. |
| LAC-10 — Spanish request or unvalidated Swiss-German negation such as “nöd neu” | Do not promise unsupported-language/dialect interpretation or guess away negation. Retain input and request supported-language rephrasing; capability limitation is distinct from invalid input, insufficient knowledge and technical processing failure. |
| LAC-11 — Meaning cannot be preserved or processing fails | Clarify uncertain meaning; if interpretation capability cannot handle it, explain that limitation and invite rephrasing. If the adapter crashes, report processing failure instead. None is invalid input or assessed insufficient knowledge. Unusable essential source meaning affects only the relevant candidate; no invented explanation or external fallback. |
| LAC-12 — Language processing/result persistence | No outgoing request/translation/embedding call sends user text or collected evidence to external providers. Preserve original request and evidence, distinguishing interpretation/derived explanation. Persist actual result language and source/provenance context before presentation; render failure/save failure cannot look successful. |
| LAC-13 — Preference, browser and correction | Clear French text is explained in French without routine selection despite browser German. For understandable “Velo”, use the existing supported choice before browser preference, allow correction, and keep country fixed. Unsupported/missing browser language causes no forced English or country-based fallback; ask once if no supported explanation language exists. |

## Tests

Consolidated increment-1 planned Tests accepted by the owner on 2026-10-10;
no production tests from this plan are implemented or run. The separately authorized
isolated DESIGN spike is recorded in ARCHITECTURE.md; it does not validate this UC.
Use synthetic fixtures.
Scenario groups trace to the AC
identifiers and existing E examples above; grouping is not a choice of test
framework or internal representation.

| ID / level | Planned scenarios and assertions |
|---|---|
| T-01 / Unit | AC-01/07: recognisable versus unclear subject; optional omissions; preserve goals/constraints; valid default/cleared country; recognise absent knowledge as coverage, not invalid input. |
| T-02 / Unit | AC-02: default without confirmation, changed country, country-only; distinguish malformed, demonstrated mismatch, ambiguity and unavailable reference knowledge; clarification/explicit country-only, never silent constraint loss. |
| T-03 / Unit | AC-03/04/06: prepared evidence for product delivery, service coverage and habit applicability, including another market; essential versus optional evidence/goals, scoped attribution, calculations, same-scope conflicts, missing versus contradicted requirements; zero/one/mixed qualifiers and both comparison dimensions, useful specific content versus generic, unknown baseline/advantages. |
| T-04 / Unit, controlled clock | AC-05: all five claim categories/windows, before/at/after expiry, earlier source expiry/known changes, unrelated claims, elapsed days/time zones/missing precision; publication/update/retrieval/review/data-period distinctions, missing dates and environmental applicability; cached reopening never changes review. |
| T-05 / Unit | AC-08: one, three and more than three qualifiers; stable alphabetical order and deterministic ties; failed candidates excluded, omission explanation and no best/ranking/exhaustive claims. DESIGN selects the tie-break mechanism. |
| T-06 / Unit | AC-09: retain currencies without conversion; comparable versus differing currencies/units/periods/cost basis; supported calculations and disclosed material exclusions; unknown charges cannot become zero or justify cheaper/total cost. |
| T-07 / Unit | AC-12: supported/fresh/contradicted and supported/expired combinations; independent label meanings, disputed/unknown essential versus optional claims; no label promotes a failed match or implies independent verification/live guarantees. |
| T-08 / Integration | AC-07/08/10/13: persist request/interpretation/displayed identities/evidence and justified location before presentation; zero-qualifier valid request/outcome retention; no invalid application search records; persisted results remain without a selection. |
| T-09 / Integration, controlled clock | AC-05/10/11: fault injection at processing and required persistence stages, including partial writes and coverage-save failure; no false completed/saved outcome; fields retained, explicit retry only; retry reassesses evidence/applicability/expiry and preserves cached review dates. |
| T-10 / Integration | AC-03/07/13: retrieval then assessment using prepared evidence; zero/unsupported-market coverage versus retrieval failure; no research, external LLM transmission/geocoding/detection, tracking/coordinate collection, extra collection or automatic refresh; location/request combinations are not assumed anonymous. |
| T-11 / E2E | AC-01–13: default/changed-country/country-only successful journey, product/service/habit fixtures, ambiguous/unverifiable locality clarification or explicit continuation, single/limited comparisons with evidence/unknowns/currencies/labels; processing/coverage/save failures distinguished with preserved fields and explicit retry; presentation waits for required persistence. |
| T-12 / E2E | AC-14/E-LD-01: keep processing feedback during handling, including a deliberately delayed required save; end it on comparison, insufficient coverage, clarification or processing/save error. No invented progress percentages or implied saving success. |
| T-13 / Planned integration/component, controlled clock | AC-16/17: confirmed intended locality with absent versus supporting/contradicting applicability evidence; lost response after commit, same-key concurrent delivery and unchanged-payload recovery, changed payload rejection, different-client/identifier-only denial, rollback then reassessment, expiry before new save, explicit fresh identity and loading/unknown-status truth. Recovery acknowledgement must contain no historical comparison presented as current. No recovery/persistence test is implemented by the multilingual experiment. |

DESIGN determines test tooling, approved format/reference mechanisms,
storage/failure injection and clock/transaction/retry details; DEVELOP implements
meaningful tests before code.

Deferred mandatory plans: D-RESEARCH (original Flow step 5 and E-LO-08) must
cover retrieval before approved research, empty/insufficient knowledge,
unsupported markets, privacy-reviewed minimized queries, research failure and
the same comparison/persistence guarantees in increment 2. D-SELECT is owned by
[UC-003](UC-003-SELECT-DISPLAYED-ALTERNATIVE.md#tests): explicit persisted selection,
saving confirmation and unchanged factual validation; eligibility/errors and
selection-versus-realized-savings remain pending. These are not asserted complete
by this UC-001 increment-1 plan. Full journey validation and UC-002 remain deferred.

### Language scenario plan

Scoped planned scenarios accepted on 2026-10-10; no production tests or verified
application language support. The isolated DESIGN spike covers only exploratory samples. Extend T-01/08/10–12 rather than repeat every matrix at each layer.

| ID / criteria | Planned coverage |
|---|---|
| TL-01 / AC-01/15; LAC-01–04/07/08 | Reviewed parallel DE/FR/IT/EN meaning fixtures, ordinary paraphrases, original spans, names/numbers/currencies/units, negation/goals/constraints and ambiguous numeric meaning. |
| TL-02 / AC-01/11/14/15; LAC-05/06/10/11/13 | Short/mixed/unsupported/dialect cases; preference before supported browser fallback, easy correction, no country inference or routine selector; meaning clarification versus capability limitation versus actual adapter fault. Loading terminates on these clarification/error outcomes. No invented confidence thresholds. |
| TL-03 / AC-03–05/12/13/15; LAC-09/11/12 | Four request languages against reviewed sources in each target language; faithful derived/original provenance and checked-at dates, no invented facts or external calls, unusable essential meaning and candidate independence. |
| TL-04 / AC-10/11/14/15; LAC-01–06/12/13 | Focused API/browser journeys, language preference/correction with unchanged country, preserved fields/original request, local rendering before atomic persistence and loading through save/clarification/errors. |

Meaning review requires demonstrably competent source/target-language review;
reviewer availability is not assumed. DESIGN defines the practical review gate.
Synthetic success alone establishes neither runtime knowledge, general translation,
dialect coverage nor verified application support.
