# Architecture

This document owns the accepted scope and architecture boundaries. The
[project baseline](PROJECT.md) owns setup commands and historical evidence;
[UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md) and
[UC-003](specs/UC-003-SELECT-DISPLAYED-ALTERNATIVE.md) own detailed behaviour
and pending acceptance. Accepted architecture describes intended behaviour, not
implemented capabilities.

## Accepted scope

Resolena Alternative Finder is a standalone FHNW capstone module, with future
integration into Resolena's website or mobile app. It helps users compare
practical alternatives to purchases and habits using financial savings and
environmental/resource information, transparently and without judgment.

UC-001 accepts natural-language text, normalizes/categorizes it, reuses supported
knowledge before researching, persists requests, shown results and evidence,
then presents a small evidence-backed comparison. UC-003 records explicit
selection against that persisted comparison without changing factual validation.
Basic loading, validation and error states are in scope; UC-001 increment-1
behaviour/test planning was accepted on 2026-10-10. Remaining scope is pending. Existing knowledge may initially be empty.

Owner-approved UC-001 amendment on 2026-10-09 adds manual search-location
awareness within finding/comparing alternatives. Detailed behaviour, scoped
approvals and deferred policies belong in
[UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#flow); no implementation is claimed.

Owner-approved decomposition on 2026-10-09 maps original steps 1–7 to UC-001
and 8–9 to UC-003; see [ADR-002](adr/ADR-002-use-case-decomposition.md).
The full mandatory journey remains incomplete across both delivery increments:
sufficient existing knowledge, then insufficient/empty knowledge with approved research.

UC-002 optional image input is deferred until the full mandatory UC-001 + UC-003
journey, including research, is validated.
Extracted information requires user confirmation; raw images are not retained
by default.

Out of scope: accounts/login and personalized account history; banking,
payments, savings transfers and investments; the complete Saver and dual
piggy-bank ecosystem; community features, rewards and Resolena Coin; automatic
training or reinforcement learning from selections; autonomous rewriting or
deployment of prompts, ranking rules or code; complex analytics and
production-scale crawling.

## Accepted technology baseline

Owner accepted on 2026-10-04 during BOOTSTRAP:

| Component | Baseline |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python 3.12 + FastAPI |
| Initial persistence | SQLite through SQLAlchemy |
| Backend testing | pytest + httpx |
| Development environment | GitHub Codespaces with a devcontainer |

This reuses the course template's Python foundation for a full-stack application
while keeping business logic independent of frameworks and database providers.
PostgreSQL is a possible later migration, not an initial dependency.

## Clean Architecture boundaries

Use ports and adapters; source dependencies point inward toward application
and domain.

- Domain: business concepts and rules, independent of FastAPI, SQLAlchemy,
  external services and AI frameworks.
- Application: coordinates UC-001/UC-003 and defines ports for persistence, retrieval,
  interpretation, research and explanations.
- Interfaces: FastAPI routes translate web requests into application calls.
- Infrastructure: database, research and optional AI adapter implementations.
- Frontend: React/TypeScript accesses the backend API, never the database directly.

Connect concrete adapters at startup. Business logic must not depend on a
particular database or AI provider. The application controls the workflow and
permission to research; optional AI assists bounded tasks, without autonomous
control of the sequence.

## Retrieval, persistence and evidence

Interpret → retrieve → assess relevance, evidence quality and freshness →
research only if needed → compare and explain → persist and present →
record explicit selection.

Reuse sufficient existing knowledge without research. Do not invent missing
facts; identify unknown values and assumptions. Persist the original request,
normalized interpretation, shown alternatives and supporting evidence before
presenting the comparison and before selection. Results remain if the user
leaves; no selection is inferred. Store an explicit choice against its request
and confirm saving. Newly acquired knowledge is reusable subject to the same
quality checks.

Keep these conceptual entities separate; detailed schemas remain for DESIGN:

| Concept | Responsibility |
|---|---|
| SearchRequest | Original/normalized request and context |
| Alternative | Reusable alternative information |
| RequestAlternative | Alternatives shown for a particular request |
| Evidence | Sources and metadata supporting factual claims |
| Selection | Explicitly selected alternative |

Material factual claims must be traceable to evidence. Preserve source/reference,
relevant dates and confidence/validation metadata. Selection frequency can
affect relevance; it must never automatically increase factual confidence or
change validation status.

## Strict runtime privacy

- Keep collected application data in Resolena-controlled persistence.
- Do not send original/normalized requests, stored alternatives, evidence
  records, selections, identifiers or images to external LLM providers,
  including for embeddings, classification or ranking.
- Use synthetic or deliberately non-sensitive examples for development and
  review, never production/user data.
- External research requires minimized, non-identifying queries and explicit
  SPECIFY/DESIGN review before implementation.
- Use anonymous request identifiers without accounts. Free text may contain
  personal information; anonymous identifiers do not anonymize its contents.
- Relaxing this boundary requires explicit owner approval and an updated
  specification before implementation.

Location retention is limited to comparison needs; location plus request text
may identify someone. Automatic detection/tracking and exact-coordinate collection
are excluded from this increment. The approved amendment does not relax external
LLM restrictions or research minimization; see
[UC-001 privacy](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#preconditions).

No OpenAI or Gemini API key is required for UC-001 runtime. Development
authentication does not grant permission to transmit collected application data.

## UC-001 increment 1 design — accepted 2026-10-15

**Accepted implementation baseline, 2026-10-15:** the owner accepted this integration
design and authorized Phase 3 DEVELOP, priority 1. A pre-entry check of the approved
UC and ADR-003 found no material conflict; their evidence, language, privacy and
recovery contracts are retained. Earlier proposal/pending-acceptance wording records
design history, not an outstanding entry gate. Interpreter selection, production
hosting, reviewed knowledge and qualified linguistic validation remain open delivery
dependencies. Acceptance is not implementation, verified language support or increment
completion; the current scope/status is in [TASKS.md](TASKS.md).

Refined on 2026-10-10 against the repository and accepted
[AC-01–14/T-01–12](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#acceptance).
At that refinement, the owner accepted the direction but not final DESIGN or
implementation. The later 2026-10-15 baseline acceptance is recorded above; accepted
behaviour remains in the UC.
The owner approved the scoped language requirement amendment on 2026-10-10
(AC-15/LAC/TL); support is unverified. The complete DESIGN was then proposed; production interpreter selection remains
open. The refinement below incorporates that requirement without reopening
settled evidence/location/currency rules.
[ADR-003](adr/ADR-003-persisted-comparison-boundary.md) records persistence/retry rationale.

### Repository basis and responsibilities

Pre-implementation inspection: React 19.3.0, Vite 8.3.2, TypeScript 6.0.3;
the frontend was the starter and backend/test directories were empty.
The pinned FastAPI/SQLAlchemy/pytest/httpx baseline exists, but there is no
application knowledge catalogue, reference dataset, API or comparison store.
Dependency presence is not runtime verification.

Domain owns interpretation values, claim/candidate assessments, amounts and order;
application coordinates interpretation, reference/knowledge retrieval, clock and
atomic-result ports. FastAPI translates requests/outcomes; React owns page fields
and loading. SQLAlchemy/SQLite implements local reads/transactions; dependencies
remain inward. Sequence: interpret/resolve → retrieve → assess → prepare →
commit → present. Correction/clarification and failed processing bypass successful
presentation. Research remains mandatory increment-2 work; no runtime external
LLM, geocoding, location-detection or automatic-refresh adapter is part of increment 1.

### Interpretation, retrieval and application knowledge

Use a local `RequestInterpreter` application port; its production adapter is not
selected. Preserve original text and spans alongside normalized English concepts,
explicit goals/constraints, exact amounts/currency/units/basis and unresolved meaning.
Keep country/locality resolution separate; absent optional fields stay absent.
Deterministic patterns/aliases and protected-value checks can support an adapter,
but do not establish ordinary-language understanding. Exact quotes and structurally
valid output likewise do not prove that negation or every clause was understood.

A subject need not occur in the catalogue or parser vocabulary. For a recognisable
novel subject, retain its literal terms and retrieve; category is a hint, not an
input gate or a restriction to alternatives of the same type. An unclear subject
needs correction/clarification. Multiple recognised items do not themselves make
input invalid: preserve the stated scope; clarify ambiguous meaning rather than
silently selecting one item or inventing a bundle. Unsupported joint matching
remains valid insufficient coverage. Unsupported or ambiguous goal/constraint syntax stays
verbatim/unresolved: clarify meaning or explain interpretation capability limits,
never ignore a clause or infer a cheaper/environmental goal. Do not turn an inability
to understand the request into assessed insufficient application knowledge.
Only understood requirements can enter qualification; technical adapter failure
is a separate processing error. An intelligible subject need not be invalid.
There is no mandatory selection from predefined subjects or confirmation of clear input.

Use a small local catalogue of reviewed subject aliases/purpose links and normalized
terms. Retrieve their union across alternative types, then assess every retrieved
candidate; do not pre-limit to three or hard-filter unknown geography/cost.
For unmapped subjects, scan the small reviewed catalogue for literal/purpose matches;
failure to establish relevance is explicit coverage limitation, not proof of global
absence. Full text, explicit requirements and location go to assessment independently
of retrieval terms. Qualify claims using AC-03–06/09/12; missing/disputed claims are
assessment outcomes, whereas adapter faults are processing errors.

Store money as exact decimals with source precision, currency/unit/period; preserve
user-reported baseline provenance as input assertions, not invented reviewed market
evidence. Unsupported/materially uncertain comparisons remain unknown under AC-09.
Use an injected UTC clock for final assessment/retry; keep assessed-at separate
from publication/update, retrieval, review and data periods. Missing precision stays
unknown. Explanations draw only on supported claims/calculations and explicit
limitations. Reviewed templates and claim-specific narrative renderings are the
proposed explanation path; their fidelity is separate from request interpretation.
No numeric relevance score is proposed.

Synthetic fixtures live only in isolated test stores and cannot seed runtime facts.
Recommend a separately reviewed public-source repair/reuse knowledge release:
named alternatives, subject/purpose mappings and claim evidence with real provenance,
scope and actual review dates. A runtime-use flag requires that review; expired
essential claims still fail current qualification. No such release exists yet.
At least one genuinely qualifying alternative is needed for a usable validated
application journey; passing synthetic tests does not establish market coverage.

### Multilingual interpretation and explanation — provisional mechanism

Canonical requirements: [approved L-01–06/AC-15](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#language-amendment--owner-approved-2026-10-10).
**Integration baseline accepted, 2026-10-15:** ordinary written DE/FR/IT/EN
remain required; application support is **not implemented or verified**. The owner
stopped standalone detector experiments and exact unsupported-language identification
tuning. [ADR-004](adr/ADR-004-multilingual-interpretation-scope.md#product-integration-refocus--owner-direction-2026-10-15)
records this direction. Lingua is an advisory candidate, not a selected dependency
or independently trusted capability gate. No additional detector screen is a
prerequisite for implementing the application contracts.

Keep three responsibilities distinct, without requiring three services or model calls:

| Responsibility | Proposed contract and boundary |
|---|---|
| Original-input recognition | An optional local recognizer returns supported/unsupported/mixed/unknown hypotheses about the original text, possibly a language code. It may abstain. A top-ranked label, score or agreement with the interpreter proves neither language reliability nor meaning; it cannot alone allow or reject a request. |
| Request interpretation and normalization | `RequestInterpreter` reads the entire original request, retaining each meaning-bearing clause, verbatim spans, names, negation, amounts and constraints. Normalized English concepts are separate from original language and exact original quotes. Ambiguous quantities remain unresolved; no locale-derived numeric guess. Missing normalization vocabulary must not invalidate a recognisable novel subject. |
| Application policy and evidence rendering | Application code selects the approved outcome and explanation-language origin below; the interpreter is not an evidence authority. A separate local renderer uses reviewed source claims and faithful target-language artifacts, retaining original citations, qualifications and review dates. Recognition never sets country, prices or evidence validity. |

Protected-value/span checks reject demonstrated loss or alteration; clause coverage
and semantic fidelity also need reviewed tests, not merely an adapter's assertion.
An advisory-label conflict is a diagnostic signal, not automatic rejection or proof
of understanding. Resolve actual language/meaning uncertainty through the paths below;
do not add routine language selection to otherwise clear supported requests.

| Input/meaning state | User-visible policy before retrieval |
|---|---|
| Clear DE/FR/IT/EN, complete meaning understood | Proceed normally and explain in the recognized supported language, with an explicit correction available. Browser preference does not override clear input. No routine language selector or confirmation. |
| Clearly unsupported input | Give a limitation and ask for rephrasing in DE/FR/IT/EN. An internal unsupported-language name is optional: Spanish versus Portuguese is immaterial to this route. Preserve the existing `unsupported` / null supported-language / nonempty limitation contract, projected as `interpretation_unavailable`; no application search record. |
| Understood short/shared subject, uncertain input language | Retrieve normally; keep recognition uncertain. Use an existing supported page preference, then one supported browser language, with easy correction. With neither, request a one-time DE/FR/IT/EN explanation choice. A name or top out-of-scope label alone cannot make this input unsupported. |
| Mixed input, all meaning established | Retain every clause/constraint; use a clear supported primary language or the same preference path. Never discard a minority-language clause. This does not promise general support for additional languages. |
| Genuine uncertainty about meaning, amount, negation or a clause | Ask a targeted clarification and preserve fields. If interpretation capability is unavailable, give the limitation/rephrasing route instead. A preferred language cannot resolve meaning; neither outcome is insufficient application knowledge. |
| Actual adapter/renderer fault | Report `processing_error` with explicit retry; do not relabel it as unsupported language, unclear input or insufficient coverage. |

Language context carries only supported `de/fr/it/en` preference/correction and one
supported browser language, not the full locale list/region. Country/locality stays
the independently supplied/defaulted search location, including for shared/mixed
words. No permanent language profile, external inference/translation/detection
service or external fallback is introduced. All request processing stays local or
on Resolena-controlled infrastructure; no production host is selected here.

Only an understood request reaches reviewed-knowledge retrieval/qualification.
Cross-language evidence is not filtered to match input language. Prepare faithful
explanations **before** the atomic save/presentation boundary; save the original,
interpretation, justified location and effective explanation language/origin/versions.
Clarification/capability outcomes create no application search record. A valid
understood request with no qualifying knowledge produces saved `insufficient_coverage`,
not a language failure. API/recovery/privacy contracts below remain unchanged.

| Synthetic example | Alias/template path and boundary |
|---|---|
| “Repair my bicycle without replacing it”; parallel “Fahrrad … ohne … ersetzen”, “vélo … sans … remplacer”, “bicicletta … senza … sostituire” | Reviewed action/subject aliases map to shared repair/bicycle concepts; a language-aware grammar retains no-replacement separately. A word hit alone cannot prove negation or full interpretation. Qualify the same reviewed candidates under the unchanged evidence checks. |
| “Velo”, CH, browser `fr-CH` | If bicycle meaning is understood, retrieve and explain in French using the browser preference, marked as a preference rather than detected language; easy correction. Country stays CH. |
| “Repair Acme X-2 in Genève, budget 49,90 CHF per repair; do not replace it” | Preserve literal identifiers/place and exact decimal/unit provenance. Parse the explicit budget/negation, without inferring a current-price baseline or currency conversion. If the amount's meaning is uncertain, ask rather than guess. |
| “Please repair my bicycle, sans remplacement” | Proceed only if the complete mixed-language meaning is understood; retain the French constraint. A balanced understandable mixture can use the preference path; an unresolved clause needs targeted clarification. |
| “Make it cheaper without reducing waterproofing”; unknown idiom or dialectal negation | Reviewed grammar/aliases must cover comparative scope and negation, not just keywords. If meaning cannot be established, clarify/rephrase; do not silently drop waterproofing or report insufficient knowledge. If understood but evidence cannot support it, assessed coverage is the correct outcome. |
| Recognisable novel product outside aliases | Preserve literal subject and search reviewed terms/purpose links across types. Catalogue absence alone is coverage; inability to interpret language remains a distinct capability outcome. No forced catalogue selection or repair-only input restriction. |

Prepared evidence admission, not runtime automatic translation, supplies faithful
cross-language meaning: retain original source language/reference/support passage
and immutable review metadata; extract scoped typed claims/calculation inputs.
Review a language-neutral claim representation against the original, then version
target-language renderings/terms for all four targets. Render known claim kinds
(price, scope, availability, environmental method/period, exclusions and unknowns)
with protected literal names/amounts/units, evidence links and attribution.

For narrative information outside predefined templates, prepare and review a
claim-specific target-language paraphrase with the same conditions, uncertainty,
geography, method and dates, linked to its original passage/claim version.
Never insert an untranslated source paragraph as if it were a request-language
explanation. Optional material may be omitted/unknown under approved rules; if
an essential condition or mandatory comparison content cannot be faithfully
rendered, preparation is incomplete: explain the interpretation/rendering limitation
or actual processing fault, not a successful comparison. Do not silently omit a
caveat or relabel a supported fact as unknown solely to fit a template.
This curated rendering path is not general automatic translation.

Bounded implementation, 2026-10-19: `SourceBoundRenderer` implements the existing
renderer port for prepared paraphrases. It binds source versions/typed meaning,
wording/language/version and qualified source/target review records; explicit
test composition alone permits synthetic review substitutes. Missing review gives
a rendering limitation; inconsistent bindings fail processing before saving.
Qualification still owns request-specific requirement labels. Existing application
language/version checks, authoritative claim snapshots and atomic saving remain.
The [bicycle drafts](knowledge/UC-001-BICYCLE-REPAIR-CH-RENDERINGS.json) bind the
unchanged factual packet and stay inactive/pending. Checks enforce review metadata
and protected values, not semantic correctness or reviewer competence. No genuinely
qualified comparison, general rendering coverage or TL-03 acceptance is established.

Synthetic source-to-explanation checks (not actual application knowledge):

- EN provider statement “Labour CHF 45 per repair; parts excluded” → proposed FR wording
  for later review: “Main-d’œuvre: 45 CHF par réparation; pièces non comprises.” Typed amount/basis,
  provider attribution and actual checked-at stay linked to the original; the price
  is not a total or proof of cheaper service.
- IT narrative “Valido solo per biciclette non elettriche; il ritiro non è incluso.”
  → proposed EN wording for later review: “Applies only to non-electric bicycles;
  collection is not included.”
  Prepare a claim-specific rendering when generic templates lack those conditions.
  An electric-bicycle request fails that requirement; do not hide the exclusion.

No production recognition, translation or generation dependency is selected by this
proposal. The application ports permit a suitable local adapter without coupling
domain qualification to a detector/model. Processing and review of identifying
combinations must respect Resolena control; no external translation/LLM fallback.

**Sufficiency of the mechanism:** this integration contract is reviewable without
another standalone detector experiment. Aliases/templates do not establish adequate
ordinary-request interpretation coverage; a real local interpreter must still meet
the approved semantics, and reviewed narrative rendering must cover essential
conditions. Test substitutes establish application wiring only. Restricting requests
to listed subjects/fixed phrases, English-only results, or omitting untemplated
essential evidence would reduce scope; none is proposed or accepted. Interpretation
and faithful evidence rendering require separate validation.

Practical review gate: identify review capacity before claiming support; no bilingual
reviewers are assumed. Arrange demonstrably competent source-language review plus
target-language semantic checks (one multilingual reviewer may cover several roles).
An owner may review only languages they can competently assess; an unreviewed language
stays unverified. If capacity is unavailable, report the acceptance dependency and
seek review resourcing rather than substitute machine-only approval or reduce scope.
Use synthetic parallel requests and non-sensitive public evidence; do not send actual
requests/identifying context to outside reviewers/services. Retain reviewer role,
review date, artifact version and corrections for aliases, grammars, templates and
claim-specific paraphrases, separately from factual source review dates.

Test allocation: TL-01/02 own semantic/preservation/preference matrices and out-of-scope
negatives; TL-03 uses a small reviewed four-request-by-four-source-language matrix,
including a narrative condition outside templates and shared baseline calculation.
Target-language reviewers check preserved meaning, omissions and natural explanation
wording; source review checks original support. Include Swiss standard spelling,
short/mixed input and dialect negatives without promising dialect support.
TL-04 owns a few real API/browser journeys for preference/correction, original context,
no country inference, loading and atomic saved-language provenance. Existing T-04
controls expiry; T-08–10 own immutable evidence/no-outbound/persistence faults.
Do not replicate every linguistic fixture at each browser layer. Keep held-out ordinary
paraphrases separate from curated examples; no numeric accuracy threshold is invented.
Package/license/resource and observed failure checks precede mechanism selection;
tests/review remain planned, never passing evidence.

### Multilingual feasibility experiment — 2026-10-10

The isolated parser/renderer prototype demonstrated gaps in ordinary four-language
requests and unprepared narrative evidence. Its complete historical assessment is
preserved in the [experiment record](../experiments/uc001_multilingual/qwen_spike/REPRODUCE.md#archived-design-experiment-assessment--2026-10-11).
These exploratory results do not establish approved multilingual support.

### Local multilingual interpreter assessment — proposed 2026-10-10

The assessment is now closed. The tested pinned Qwen3-1.7B Q8_0 configuration
is **not accepted for production**: 0/12 strict calibration passes, including
0/6 at temperature zero. Build/compatibility/readiness succeeded separately;
operational checks do not establish model success. See [findings/closeout](../experiments/uc001_multilingual/qwen_spike/portable_2026_10_11/REPRODUCE.md#experiment-closed--verified-return)
and [per-case evidence](../experiments/uc001_multilingual/qwen_spike/portable_2026_10_11/CASE_REPORT.md).

Semantic classification/constraint/language errors, exact quote-grounding failures
and normalized-label mismatches remain distinct. A label mismatch alone does not
prove a different underlying object/action. This finding does not reject all local
models or other configurations. The six cases are calibration data; all 55 frozen
evaluation cases remain model-unexposed. Original machine resources were restored,
workspace hashes verified, and artifacts/results preserved.

### Local interpreter experiment — interrupted; reviewed 2026-10-11

The [archived history](../experiments/uc001_multilingual/qwen_spike/REPRODUCE.md#local-interpreter-experiment--interrupted-reviewed-2026-10-11)
retains the initial interruption, renewed attempt, restart, failed smoke, memory
preflight and subsequent portable calibration with their original authorization
boundaries. Earlier unexecuted cases are not reported as semantic failures.

### Multilingual interpretation scope — direction A accepted

[ADR-004](adr/ADR-004-multilingual-interpretation-scope.md): the owner retained A
on 2026-10-11, preserving approved multilingual free text and Resolena-controlled
processing; B's scope changes are not adopted. Development experiment limits are
not production requirements. Detailed approvals, operational repairs, resources
and failures remain in the experiment records:

- [Windows v1](../experiments/uc001_multilingual/qwen_spike/windows_results_2026_10_13/REVIEW.md):
  2/6 strict passes; DE/FR/IT canonical-label mismatches alone do not prove incorrect
  meaning. Spanish, an unsupported-language negative control, failed limitation handling.
- [Windows v2 operational failure](../experiments/uc001_multilingual/qwen_spike/windows_v2_results_2026_10_14/REVIEW.md)
  preceded any evaluation; [v2.0.1](../experiments/uc001_multilingual/qwen_spike/windows_v2_0_1_results_2026_10_14/REVIEW.md)
  then passed 5/6 known cases but incorrectly treated unsupported C6 as understood
  English with no uncertainty. All six quote checks passed; twelve requests did not
  run. Required instructions and schema were present; root cause remains unproven.
  Logged GPU offload is not measured acceleration or language capability. The
  labelled archive supplement preserves the original incomplete export and failed gate.
- [Lingua runner 1.0.2](../experiments/uc001_multilingual/lingua_B_runner_v1_0_2/RESULTS.md):
  completed two passes over 25 contexts; its frozen raw-identity gate failed on C6
  (Spanish ranked Portuguese). Both labels are outside product support. That error
  alone is **not a product acceptance blocker**; no application limitation response
  was implemented/tested. Short-word, mixed-clause and dialect findings caution
  against using detector labels as capability gates or meaning evidence.

Previously failed frozen gates/results remain unchanged; no diagnostic criterion
is retroactively rescored. The product blocker exposed by Qwen C6 is inappropriate
limitation handling, not inability to name Spanish. Exact quotes likewise do not
establish preserved meaning. Closed configurations are not accepted for production;
the findings reject neither all local models nor the approved language requirements.
The owner stopped further standalone detector experiments/tuning on 2026-10-15.
All 55 held-out cases remain unopened; no new execution is proposed here.
Interpreter/hosting selection and qualified linguistic validation remain pending.
The owner accepted the integration baseline and ADR-003 on 2026-10-15; only the
priority-1 synthetic vertical slice is authorized for implementation now.

### Location reference data and matching

Recommend pinned local extracts, with source/release/hash, preparation/review dates
and attribution. Never send user input to these publishers at runtime.

| Reference | Chosen source / explicit coverage |
|---|---|
| Country selector | [GeoNames countryInfo](https://download.geonames.org/export/dump/): reviewed current country/territory codes/names; exclude obsolete/non-country entries and retain legitimate current territories. All listed countries permit country-only input regardless of alternative/research coverage. |
| Worldwide town names | GeoNames cities500 extract plus admin1 labels: cities over 500 inhabitants or specified administrative seats, not every settlement; retain source IDs/names/aliases/country/admin labels only. GeoNames attribution applies; it is not authoritative proof of completeness. |
| CH/LI town/postcode pairs | [swisstopo directory](https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities): official locality/address postcodes for Switzerland/Liechtenstein. It excludes some non-address postcodes (e.g. PO boxes); absence cannot prove invalidity. |

Import only non-spatial reference columns; exclude coordinates/perimeters/full
addresses. Reference presence never verifies product delivery or service coverage.
Keep a reviewed snapshot fixed for a release; replacement is explicit maintenance,
not automatic freshness renewal. Source/data dates and limitations travel with it.

Owner-approved 2026-10-23, [ADR-005](adr/ADR-005-country-reference-development-release.md):
the separate [country release](reference/COUNTRIES-GEONAMES-2026-10-23.json) and
[approval manifest](reference/COUNTRIES-GEONAMES-2026-10-23-MANIFEST.json) retain
the 249 source-name draft entries plus XK/Kosovo; obsolete AN/CS are excluded.
XK remains a documented GeoNames temporary/source-specific code, without an ISO or
political-status claim. Approval covers the source-based policy/release basis,
not independent factual verification of every entry or qualified language review.
The original inactive 5Q draft/manifest remains historical and unchanged.

The development/test composition injects a local country-reference port. Its loader
enforces the approved release identity, source/output hashes and development-only
approval scope. Normal app.main remains unconfigured. `GET /api/countries` exposes
that same release's code/name choices and attribution for the accessible selector;
no second UI list or runtime publisher call. CH starts selected; an explicit empty
choice stays empty, with no country inference or automatic comparison submission.
Source names remain verbatim, including BQ's disclosed boundary whitespace.

For a new submission, after checked committed-record recovery, the application
loads that reference and validates country membership before interpretation.
Missing/blank/nonmember country is invalid input; absent/corrupt/unapproved
reference is `configuration_unavailable`, never inferred invalidity. Valid members
can yield saved insufficient coverage independently of language/knowledge coverage.
Persist the validated reference as server-derived
`interpretation.provenance.reference_versions.country:{source,release,sha256}` in
the existing JSON metadata. No client payload/digest, SQL column or historical
record changes. Committed acknowledgements consult neither the current reference
nor fresh membership; country editing still creates new intent. Existing 5H
unavailable-locality and explicit country-only behavior stays separate.

Priority 5T prepares an [inactive swisstopo CH/LI draft](reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-DRAFT.json)
and [pending review manifest](reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-MANIFEST.json)
from the pinned 2026-10-01 CSV snapshot. Each row retains one locality/postcode/
municipality association, not a consolidated locality. `ZIP_ID` identifies PLZ6;
the CSV supplies no locality GUID. Country is derived from documented canton
semantics; source spelling and postal strings stay separate from matching keys.
No loader, resolver or application integration is enabled by this preparation.

Owner-approved 2026-10-23, [ADR-006](adr/ADR-006-locality-association-development-release.md):
Priority 5U uses the separate [development association release](reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01.json)
and [approval metadata](reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-APPROVAL.json).
Release bytes equal the accepted 5T draft; original preparation artifacts remain
unchanged. Approval covers source policy/release basis, not independent factual
verification of every association or linguistic approval. Activation is limited
to this development slice and isolated demo/tests; no automatic replacement.

The application locality port loads one pinned local release through an infrastructure
adapter. For new provided-locality intent, after country validation and interpretation,
match within the selected country using exact normalized town and trimmed postcode
strings together. One association proceeds; multiple associations return unsaved
`clarification_required` with source-backed `clarification.associations`, separate
from language `choices`. No match/out-of-CH/LI scope is reference-unknown, not invalidity.
An absent capability retains the unavailable clarification; an unusable configured
loader is configuration failure and unexpected processing failure stays distinct.

Selection uses only `search_location.reference:{source:swisstopo,release,source_record}`
with existing `location_choice:provided`. Validate pointer, country and every entered
field server-side; stale/fabricated/edited pointers clarify, while demonstrated
selected-country mismatch is invalid input. Selection alone sends nothing; labelled
continuation captures fresh key/proof/payload. Country/town/postcode edits clear it.
Keep the separate country-only and confirmed/reference-unverified fallbacks.

Persist raw fields and `locality:{verification:matched_in_reference,selection:single_match|explicit,
normalized,association}` with one necessary source-backed association, never its candidate
list. The association pointer is release-bound; ZIP_ID is postal identity, not a locality
GUID. Derive `interpretation.provenance.reference_versions.locality:{source,release,sha256,snapshot_at}`
server-side without modifying the captured payload. Canonical selected town/postcode
guide applicability assessment while raw input remains separate; a reference match
does not qualify unsupported ordinary in-CH evidence or remove textual constraints.
The atomically saved `search_scope` drives precise matched-in-this-reference wording,
identity labels and source credit. Checked recovery precedes both reference loaders
and returns only the original acknowledgement. Normal app.main stays unconfigured.

Trim boundary whitespace and use Unicode NFC/casefold for name matching; preserve
entered spelling and postcode leading zeros. Match within the selected country,
using exact normalized names/reviewed aliases and exact postcode strings; town plus
postcode intersects compatible records. Prefer swisstopo for CH/LI and GeoNames
elsewhere; do not create cross-source duplicate choices. Collapse postcode rows
only for the same reviewed locality identity, never merely the same name. Return
one match, ambiguous choices (with admin labels), or reference unknown.
No fuzzy automatic correction, distance filtering or inferred physical location.
CH/LI postcode-format checks apply only to a declared postcode; other countries
without reviewed format rules remain unverified. A selected reference ID from a
different country demonstrates mismatch; a failed lookup/name shared elsewhere does not.

Unresolved ambiguity uses the approved clarification/explicit country-only path.
For absent reference knowledge recommend explicit manual clarification retaining
country/town/postcode as **user-confirmed, reference-unverified** (O-1 scoped approval,
2026-10-10), or explicit country-only continuation. Candidate applicability must still
have scoped supporting evidence; matching text alone never establishes coverage.
Safeguards: record raw clarified locality and `reference_unverified` separately
from candidate applicability. A provider's current explicit named-locality coverage
can support that exact intended scope only when geographic identity/conditions are
unambiguous; independent country-wide coverage can apply if no narrower condition
matters. Same-name-only evidence, assumed postcode identity or unresolved geographic
scope leaves essential applicability unverified. User confirmation establishes intent,
not existence, geocoding, delivery or coverage. Do not generalize to nearby places;
do not erase an independent locality constraint. O-1 is owner-approved; bounded
Priority 5S enforcement below does not establish factual matching or all O-1 cases.
Changing country keeps entered locality text and re-resolves it. Country-only
choice clears the location fields, not an independently stated location constraint
in text; conflicting meaning needs clarification rather than silent constraint loss.

The bounded Priority 5H implementation has no locality reference capability. After
understanding the input, supplied optional locality/reference values produce an
unsaved `locality_reference_unavailable` clarification before retrieval/assessment.
In 5H, only explicit `country_only` continuation derived an effective location containing
the selected country alone, used by retrieval, qualification and persistence.
Original text and represented textual requirements/provenance remain unchanged.
Committed lookup and binding to the captured payload precede this policy; normalization
does not change that digest or require recovery to consult current references.
Factual matching remains unimplemented. Priority 5S adds the bounded O-1 branch:
explicit `location_choice:confirmed_unverified` binds the current raw country/town/
postcode and choice to a new intended submission, without changing an older captured
or committed attempt. Country/locality edits reset that choice to `provided`; editing
never submits. The unsaved clarification and explicit country-only option remain.

The effective and persisted search location retains country plus nonempty raw town/
postcode only, with `locality:{confirmation:user_confirmed,verification:reference_unverified,
normalized:{town,postcode}}`. Town normalization is boundary trim and Unicode NFC/
casefold; postcode normalization trims boundaries without changing leading zeros.
Original strings remain distinct. No supplied locality reference ID, invented match
or review date is retained as verification. Country-release provenance remains in
its existing separate server-derived interpretation metadata. A newly saved confirmed
outcome includes this effective location as `search_scope` in its committed projection;
UI intent/status comes from that saved scope, not a recovered historical comparison.
Acknowledgement still returns only saved identity/outcome/assessment time.

Qualification requires independent geographic support for the essential applicability
claim. Ordinary country-tagged evidence does not establish coverage at an entered
locality. Named-locality support still needs unambiguous geographic identity and
matching normalized town/exact trimmed postcode; same-name text alone fails.
Explicit source-backed `country_wide:true` can support intended locality only after
the existing country, narrower-scope, condition, support and freshness checks. It is
never inferred from `country_code` alone. Independent textual locality constraints
remain essential. The new positive evidence is synthetic; no real provider acceptance,
factual town/postcode matching or complete O-1 verification follows.

### Persistence model and atomic boundary

Use SQLite/SQLAlchemy with foreign keys enabled, UUID identities, immutable evidence
versions and a JSON saved projection. Nullable values mean unknown, never zero or
an invented date. Fields below are logical requirements, not generated schemas.

| Record / relationship | Required content |
|---|---|
| SearchRequest; one to many RequestAlternative | Request UUID; unique submission-key digest, originating-proof binding digest and canonical payload digest; original text; interpretation/goals/constraints with span provenance; justified country/locality, reference version and confirmation/resolution state; language recognition/meaning status, effective explanation language and its origin, explicit correction and interpretation/render versions; assessed-at, policy/catalogue versions; comparison or insufficient outcome, limitation codes and omitted-qualifier count. |
| Alternative; one to many alternative-specific Evidence versions and RequestAlternative | Stable UUID, display name/type/description, reviewed subject/purpose aliases and knowledge-release provenance/runtime-use status. Current catalogue content is separate from saved display content. |
| Evidence; append-only versions | Version UUID, logical evidence identity/revision, claim identity and optional alternative identity (shared method/baseline sources may be standalone) and typed value/unit/currency; publisher/source reference/support passage or input references/calculation; variant/geographic/condition scope, applicable/data periods; publication/update/retrieval/review timestamps with precision; review basis, earlier expiry/known invalidation, attribution and preparation provenance; original source language and support, immutable typed meaning and separately versioned reviewed renderings/paraphrases. Translation review never replaces factual source review. Missing metadata remains explicit. |
| RequestAlternative; belongs to one request and alternative | Own displayed-option UUID; unique request/alternative and request/display-position; persisted name/order; immutable claim values, evidence-version IDs, independent support/freshness/requirement assessments, availability/unknowns, baseline/currency/calculation/assumptions and geographic limitations, actual explanation language/text and derivation/rendering version references in snapshot JSON. |
| RequestAlternativeEvidence association | Composite request-option/evidence-version references with foreign keys; every referenced version is retained unchanged. This supporting relation is not a new user goal or rubric-compliance claim. |
| Selection | Existing concept only; no selection writes, endpoint or eligibility decision in this increment. Future UC-003 references the saved request/option identities. |

Assessment precedes a short transaction. Insert the SearchRequest and either all
displayed option snapshots/evidence associations or the valid insufficient outcome;
commit once, then serialize that saved projection. No committed “pending” search
record, partial result or invalid/clarification search record. Foreign-key/unique
constraints protect identity; source versions referenced by snapshots cannot be
overwritten/deleted. Prepared knowledge writes/reviews are separate maintenance.

The internal reader returns a committed request and its option/snapshot/evidence
context; it never joins mutable catalogue values to rebuild historical display.
Use its request/option membership boundary for future UC-003; no public history
endpoint follows. Failed/uncertain commits do not produce successful comparison
responses. A unique-key race rolls back the losing transaction and reads the committed
winner only after originating-proof/payload checks: acknowledge matching payload,
reject changed payload or unauthorized access. Unknown commit state remains unknown.

### API, same-submission recovery and deliberate fresh search

Recommend synchronous `POST /api/comparisons`; no polling, job queue or automatic
retry. One in-flight page action; hold its payload stable, dispatch from explicit
events rather than effects. Transport/country validation never treats catalogue
absence or interpretation capability limits as invalid input.

| Request field | Shape / meaning |
|---|---|
| `submission_key` | Opaque identity for one intended submission, retained with its captured payload/proof in originating-page memory and digested in the completed record. Recovery reuses it; it is not a user/device identifier or an authorization credential. |
| `text` | Original string, never overwritten by interpretation/translation. Goals/constraints/baseline remain optional derived text information. |
| `search_location` | Required `country_code`; optional `town`, `postcode`, `reference:{source,id,release}`. CH default is sent unchanged; browser/request language never sets it. |
| `location_choice` | `provided` or explicit `country_only`; `confirmed_unverified` follows approved O-1 and its evidence safeguards. |
| `language_context` | Optional supported `preferred_language`, one supported `browser_language`, and explicit `explanation_language_choice` for clarification/correction. No full browser locale list, compulsory selector or permanent profile. Capture the context with the submitted payload. |

Originating-client safeguard (accepted baseline; complete enforcement unverified): use a
separate high-entropy per-submission proof retained only by the submitting page;
cryptographically bind the opaque identity to that proof and captured payload.
Carry proof in a dedicated request header, outside the canonical payload; require
verification before lookup, processing or any save acknowledgement;
identifier knowledge alone gives no status, request or result access. Store only
necessary digests, never echo/log the proof or put it in URLs. Reuse proof/payload
for recovery; fresh search creates a new proof/identity. No accounts, device tracking,
public history or persistent browser profile. Losing page-held proof means recovery
is unavailable. Binding and uniform unauthorized responses must be verified before
production use; the language spike does not test this security design.

Interpretation output separates `recognition:{language?,status}` and
`meaning_status:understood|needs_clarification|unsupported`, plus original spans/
typed requirements. The saved projection holds effective `explanation_language`,
`language_origin:detected|user_choice|browser_preference`, interpretation/render
versions and claim/source-language/derivation references. A rendering choice is
not evidence of detected language. Recovery uses saved context, not changed browser
preferences or mutable current templates.

Common response: `outcome`, `persistence:{state,request_id?}`,
`issues:[{code,field?}]`, language context, optional clarification and comparison.
Persistence: `saved|not_attempted|failed|unknown`. A comparison carries saved
request/option IDs, order/name, typed claims with units/source currencies,
`price_basis:quoted|estimated|unknown`, citations/attribution/checked-at and independent
`support:supported|missing|disputed`, `freshness:fresh|expired|unverified`,
`requirement:satisfied|contradicted|unverified|not_applicable`.
Include actual derived explanations/assumptions/limitations and omitted count.
No fabricated values, inferred baseline or unsupported translated conditions.

| HTTP / outcome | Meaning and presentation |
|---|---|
| 201 / `comparison` or `insufficient_coverage` | Newly assessed valid outcome committed and acknowledged; `saved`. Only comparison contains the prepared option payload. |
| 422 / `invalid_input` | Demonstrated field issue/unclear subject, not language inability; no search record, `not_attempted`. |
| 200 / `clarification_required` | Meaning/locality uncertainty or no supported explanation preference; targeted choices, preserved fields, `not_attempted`. Pure understood language ambiguity uses preference/correction first. |
| 200 / `interpretation_unavailable` | Language/grammar capability limitation with rephrasing; no application search record. Distinct from invalidity, assessed coverage and technical failure. |
| 500 / `processing_error` | Actual interpretation/retrieval/assessment/rendering fault; no completed result. Current execution `not_attempted` does not prove a previous unknown save failed. |
| 503 / `persistence_error` | Confirmed rollback `failed`, or ambiguous commit acknowledgement `unknown`. Carry assessed insufficient coverage separately; no successful comparison payload. |
| 200 / `submission_recovered` (approved O-2) | Same identity/payload already committed: saved request ID, outcome and original assessed-at acknowledgement only. No cached claims or historical comparison presented as current; offer separate fresh search. |
| 403 / `recovery_not_authorized` | Missing/invalid originating-client proof: uniform denial, no record existence/status/request/result disclosure and no write. |
| 409 / `submission_key_conflict` | Authorized same key/different payload: reject, no write; preserve fields. Correction/editing is a new intentional submission, not recovery under that identity. |
| Client transport error / `delivery_unknown` | Save status unknown, not “unsaved” or insufficient coverage. Stop loading, preserve captured fields/key and offer explicit recovery or fresh search. |

Canonical payload digest covers original text, location/explicit choices and captured
language context, excluding transport key/proof and dynamic interpretation/reference
results. SHA-256 digests do not anonymize stored contents. Look up committed key/
payload before current-reference interpretation; same key/different payload conflicts.
If already committed, acknowledge that saved submission only. No source review date
renewal or current-freshness claim follows; no historical comparison is displayed.

**Recovery** sends the same key and unchanged payload on explicit user action.
If no committed record is found, absence alone is not proof of rollback (the earlier
attempt may still run). Reassess interpretation/applicability/evidence/freshness and
render before attempting the same atomic commit under that key. Concurrent executions
can compute twice; the unique key allows at most one committed record. A losing
transaction rolls back, checks winner ownership/payload and acknowledges only a
match; otherwise reject. Never present the loser's unsaved projection. If it commits a newly assessed result, respond 201 normally; if uncertain,
keep uncertainty and the same key for later explicit recovery. No automatic retry.

**Fresh search** is a separate explicit action with a new key/current fields and
complete reassessment, even after acknowledgement of an older save. Edited input/
language correction also defines a new intent; after uncertainty explain that the
earlier submission may already be saved. A fresh search can deliberately create a
separate record; recovery cannot. Remove the former `previous_submission_key`/
new-key-on-every-retry proposal. No public history endpoint, account tracking or
browser persistent storage is introduced.

O-2's user-visible recovery/fresh-search distinction was approved on 2026-10-10.
Loading boundary: loading spans recovery handling/persistence, then ends on
acknowledgement, comparison, coverage, clarification/capability response or error.
A recovery acknowledgement confirms saving, not present-day applicability/freshness.
The accepted reassessment rule applies whenever a comparison is newly prepared;
acknowledgement-only recovery is not a fresh comparison attempt. This scoped
clarification is canonical in the approved UC; the DESIGN/ADR baseline was accepted
on 2026-10-15, without claiming complete recovery implementation.

### Presentation and test allocation

Order only after qualification: compare `NFKC(display_name).casefold()` by Unicode
code-point order, then the canonical stable Alternative UUID string. Preserve
display spelling; persist positions and let React use them without locale resorting.
This is deterministic presentation, not ranking; accent order is deliberately
locale-neutral. Use exact decimal arithmetic and serialized decimal strings, with
currency/unit/period and material exclusions carried into the snapshot.

Choose existing pytest/httpx for domain/API; [Vitest](https://vitest.dev/guide/)
with [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/),
user-event and jsdom for focused component interaction; [Playwright Test](https://playwright.dev/docs/intro)
with Chromium for browser journeys. Official Vitest/Playwright requirements include
the recorded Vite 8/Node 24 baseline; React/TypeScript/package integration is not
tested here. Pin compatible development-only versions/lockfile in later authorized
setup; priority 1 subsequently installed only Playwright 1.64.1/Chromium.
Component tools remain unused; no CI/CD or Windows compatibility is claimed.

| Layer / accepted identifiers | Primary checks; avoid duplicating exhaustive matrices |
|---|---|
| Pure rules — AC-01–09/12; T-01–07 | All input/reference/claim/money/order boundary matrices, independent label dimensions, cross-type relevance and unknown catalogue; injected clock for every expiry/precision rule. Synthetic sources remain non-runtime fixtures. |
| SQLite/API — AC-03/07–11/13; T-08–10 | Real isolated SQLite transactions/foreign keys; rollback at each write/commit stage, immutable evidence/option membership, zero-candidate retention versus retrieval failure, response shapes/status and no outbound calls. Include T-13 same-key recovery races/lost responses, changed payload and originating-client proof denial, plus separate fresh-search cases; none are implemented in the language spike. |
| React component — AC-01/02/10/11/14; parts of T-11/12 | Accessible fields, explicit clarification/country-only action, retained inputs, one in-flight action, indeterminate loading through delayed persistence and terminal states; stub the API rather than repeat evidence matrices. |
| Browser — AC-01–14; T-11/12 | Thin real API/SQLite journey using synthetic prepared evidence: comparison, changed-country/clarification, insufficient outcome, processing/save failure with explicit retry, delayed commit/loading and stable saved identities. No full rule/freshness matrix at every browser layer. |

DEVELOP uses tests before implementation; the accepted broad T-11/T-12 groups
are allocated across component/browser checks, not waived. Reviewed application
knowledge needs separate evidence-based validation; no production tests/fixtures
are created by this refinement. The separately authorized language spike above
has executable synthetic checks; it validates no application or recovery implementation.

### Owner decisions and material trade-offs

- O-1 and O-2 are scoped owner-approved requirements (2026-10-10), including
  originating-client recovery and payload/concurrency integrity. Complete mechanisms
  and security enforcement remain unverified. The earlier new-key-on-every-
  retry recommendation is preserved as superseded history, not accepted behaviour.
- Language behaviour is already approved; the integration contract above was
  accepted on 2026-10-15. Lingua is advisory only. Exact unsupported-language identity, another
  detector benchmark and a production hosting choice do not block core application
  implementation. Do not promote a failed configuration or substitute fixture-only
  behaviour for the approved free-text requirements.

Concrete remaining gates/dependencies for increment 1:

| Dependency | Acceptance basis / what it actually prevents |
|---|---|
| DESIGN/ADR-003 and entry to DEVELOP | Satisfied by explicit owner acceptance on 2026-10-15 after the UC/ADR/architecture check. Only priority 1 is currently authorized; no further detector experiment is required. |
| Selection and verification of a suitable local interpreter adapter | AC-15, LAC-01–08/10/11/13: ordinary four-language meaning, constraints and correct clarification/limitation behaviour are not established. Prevents claiming or delivering the real language path; ports, policy, storage and an explicitly test-only vertical slice can be implemented without selecting the adapter first. |
| A small genuinely reviewed application-knowledge release with faithful target renderings | AC-03–06/09/10/15, LAC-09/12: none exists. Prevents a verified usable comparison with real qualifying alternatives and source-bound explanations. It does not block synthetic integration tests; reviewed-data preparation can accompany implementation. |
| Qualified source/target-language review capacity | AC-15, TL-01–04: no reviewers are assumed available. Prevents accepting DE/FR/IT/EN semantic fidelity and faithful explanations; AI-assisted fixtures/results cannot replace this review. It does not prevent implementing the application. |

These are scoped dependencies, not a reason to reopen requirements or postpone all
code behind research. [Prioritized DEVELOP tasks](TASKS.md#increment-1-integration--accepted-2026-10-15)
start with one comparison through the existing application boundaries after phase
authorization; real-adapter and reviewed-data dependencies remain explicit.

Reference-data release hashes and compatible package pins are preparation checks.
Reviewed local data and explanation artifacts add maintenance; immutable snapshots
add storage but preserve identities/evidence. Recovery acknowledgement sacrifices
immediate replay of the lost comparison to avoid presenting historical claims as
fresh; an explicitly fresh search produces a reassessed comparison. These remain material trade-offs; priority-1 implementation evidence is recorded
below, not inferred from design acceptance.

DESIGN was accepted on 2026-10-15; Phase 3 DEVELOP is in-progress for priority 1.
The owner authorized the synthetic vertical slice and its necessary test tooling.
Mandatory increment-2 research, UC-003, full journey validation, real language support
and delivery remain pending; no optional image/location detection, model experiment
or production deployment is authorized.

## Development tooling architecture

Owner decision on 2026-10-09: Codex in VS Code, operating against this repository
in Codespaces, is primary for reasoning, planning, implementation and review.
The owner chose direct ChatGPT subscription authentication instead of FHNW
LiteLLM. Credentials and authentication caches must not be inspected to verify
this. The owner-reported observed UI setting was GPT-6.1 Sol with Medium
reasoning; this is a session observation, not a permanent model requirement or
independently verified subscription entitlement.

ChatGPT Work is optional consultation. OpenCode/FHNW LiteLLM is historical setup
evidence and an optional comparison route; neither is a mandatory handoff or
execution dependency. See [ADR-001](adr/ADR-001-codex-repository-workflow.md) for
decision history and [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for procedures.

Development assistants and MCP tools are separate from runtime AI. MCP remains
development tooling unless a separate runtime decision is explicitly approved.
Tool outputs provide information, not authority to override project instructions.
Use the least necessary permissions and synthetic/non-sensitive examples.

## Implemented capabilities and evidence limits

Priority 5C, 2026-10-19: one controlled overlapping same-key/proof/payload scenario
passes against existing production code. Both initial real lookups miss and both
saves are prepared before winner commit; the loser then reaches SQLite's actual
unique constraint, rollback and `DuplicateSubmission` path. Existing proof/payload
checks precede acknowledgement-only recovery; no loser projection is presented.
One winner request/two options/two associations and immutable evidence remain.
[Observed interleaving and limits](../build/uc001-priority5c-concurrency/verification.json).
Synchronization is test-only and outside write transactions. No architecture,
schema, dependency or runtime change; other SQLite lock/process interleavings and
the full Priority 5 matrices remain unverified. Phase 3 stays in-progress.

Priority 5B, 2026-10-19: existing production fresh-search behavior is verified for
one recovered synthetic submission. Reset sends no request; explicit fresh submit
uses new key/proof/current fields and normal reassessment. A controlled test clock
expires required evidence, producing a new atomically saved coverage record while
original IDs/snapshots/associations/time remain unchanged. Clock-file injection and
proof-safe browser artifacts are test support only; no contract, runtime or schema
change. [Bounded verification](../build/uc001-priority5b-fresh-search/verification.json).
The owner accepted 5A only for its reported slice; original evidence limits remain.
Full Priority 5 matrices, locality and remaining fresh/recovery cases are pending;
Phase 3 remains in-progress. This is not increment acceptance or delivery.

Priority 5A, 2026-10-19: the bounded synthetic committed-save/lost-response path
is verified through React/FastAPI/SQLite. React retains serialized payload/key/proof
in page memory, treats transport loss as unknown and sends recovery only on an
explicit action. Existing recovery checks ownership/payload before acknowledgement;
the UI shows original outcome/time without saved claims. One committed request,
two options and two evidence links remain unchanged. [Focused evidence and limits](../build/uc001-priority5a-recovery/verification.json).
No recovery contract, runtime adapter or schema change. Full concurrency/fault/
disclosure matrices, locality and complete fresh-search work remain pending;
Priority 5 partial, Phase 3 in-progress. This does not accept real language/knowledge,
increment completion or delivery; historical descriptions below retain their scope.

On 2026-10-16 the owner subsequently authorized offline preparation of the retained
Qwen3-8B Q8_0 / llama.cpp b11429 test candidate. The opt-in infrastructure HTTP
adapter implements the existing port with strict decoding and exact quotation/
occurrence mapping. Trusted input/version metadata is local; schema/grounding
success does not establish semantic completeness. A separate development harness
injects synthetic evidence/English-only rendering, disables recognition and leaves
normal composition unconfigured. [Prepared controls/cases](../scripts/uc001_contract_check/README.md)
separate structural validation, qualified semantic review and application routing.
No model execution, transport installation or suitable-interpreter acceptance
follows from offline preparation. Qualified review and live suitability remain open;
Priority 3 is partial, Phase 3 in-progress. Accepted contracts/requirements are unchanged.

Earlier on 2026-10-16 the owner authorized the first bounded priority-3 step:
application language policy and interpreter/optional recognizer contracts with test
substitutes. Implementation fields refine the accepted L-01–06/API design:

- Ports receive original text only. `InterpretationResult` keeps original-input
  `recognition:{status,language,version}` separate from `meaning_status`, versioned
  normalized clauses and typed items (subjects/actions/goals/constraints, literal
  names/places, quantities and budget/baseline). Optional recognizer hypotheses are
  recorded separately; they cannot grant/deny meaning or choose country/language.
- Spans use half-open Python Unicode code-point offsets plus exact quotations.
  Every reported item belongs to one clause; understood input has complete source
  coverage. Negation and quantity/currency/unit/period/basis spans remain explicit.
  Numeric checks validate an adapter-declared reading, never select separators from
  language/country. Reported ambiguity clarifies. Literal place names are distinct
  from explicit locality constraints; this creates no reference resolver.
- Application policy resolves meaning/cost-basis uncertainty before explanation
  choice. Explicit correction precedes clear supported primary language; ambiguous
  language uses page preference then one supported browser language, otherwise the
  one-time choice. New text turns an earlier correction into a page preference.
  Country is unchanged. Represented actions and constraints remain essential.
- Only understood, structurally valid output reaches retrieval. Clarification,
  capability limitations and actual contract/adapter faults are distinct unsaved
  outcomes. Comparison/coverage rendering must declare the selected language and a
  version before the existing atomic save; original/provenance and language choice
  accompany committed snapshots. Existing English coverage text now belongs to the
  test renderer; normal composition remains unconfigured, with no test imports.

These checks can reject demonstrated structural loss/alteration. They cannot detect
an adapter's unreported semantic loss, wrong polarity, misleading language label or
incorrectly asserted numeric reading. Successful stubs are not proof of meaning or
source-target fidelity. Only English synthetic rendering exists; other targets
return a rendering limitation. Adapter selection and qualified semantic validation
remain later priority-3/6 dependencies, real knowledge/renderings priority 4/6.
Priority 3 is partial; Phase 3 stays in-progress. [Evidence](PROJECT.md#priority-3-partial-verification--2026-10-16).

On 2026-10-15 the owner separately authorized priority 2, Qualification & Coverage.
Domain qualification now precedes ordering/limiting and supplies assessed values
to rendering; the application saves valid insufficient-coverage outcomes through
the same atomic boundary. Priority-1 evidence/snapshots and test isolation remain.
57 backend and four real browser/API/SQLite tests plus frontend lint/build pass;
see [scope and limitations](PROJECT.md#priority-2-verification--2026-10-15).
This verifies prepared synthetic policies, not real source admission, reference
coverage, interpretation or semantic fidelity. Phase 3 remains in-progress;
priorities 3–6 and full increment validation remain pending. Dated priority-1
authorization statements above record the earlier scope; no requirements changed.

BOOTSTRAP was accepted as complete on 2026-10-05. Its recorded checks cover the
dependency setup and React starter build, lint and browser startup. Backend/test
directories were initially empty. On 2026-10-15 priority 1 implemented the React →
FastAPI/application/domain → isolated SQLite → committed-display slice. Eight
backend tests and two real Chromium/API/database journeys pass; lint/build pass.
Tests cover stable saved identities/order, immutable source versions, preparation
failure before saving and a required-write rollback without partial result/success UI.
Only test support supplies the exact-match English interpreter, two synthetic
providers, artificial review metadata and fixed clock. Normal runtime imports none
of them; this verifies wiring, not real interpretation, qualification or knowledge.
Basic ownership/payload-bound duplicate acknowledgement is present; complete
recovery races/faults and language contracts remain later tasks. See
[PROJECT.md](PROJECT.md#priority-1-verification--2026-10-15) for actual checks/limits and
[historical setup](PROJECT.md#historical-setup-evidence) for the older baseline.
Bootstrap integration into main, application CI, MCP and deployment have not
been verified. Increment 1, real language support and qualified review are incomplete.

## Pending decisions and proposed improvements

UC-001 increment-1 Errors, Acceptance and planned Tests were accepted on
2026-10-10; its integration DESIGN was accepted on 2026-10-15. Mandatory increment-2 research
specification/fallback, UC-003 eligibility/errors and selection-versus-realized-savings
remain pending. Full UC-001/journey scope is incomplete. Behaviour stays canonical
in [UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md); current lifecycle status
is in [TASKS.md](TASKS.md).
The increment-1 design now recommends the logical persistence/API contracts,
reference sources, deterministic matching/order and test tools; baseline acceptance
is recorded, not increment completion. O-1/O-2 requirements are owner-approved; their enforcement is unverified. The scoped multilingual requirement
is approved, but support and mechanism remain unverified/provisional. Semantic retrieval, later ranking,
research provider/runtime AI and delivery remain deferred choices.
Increment 1 proposes no numeric retrieval threshold or ranking score.
Hosting, storage/recovery and delivery still need their appropriate review/authorization.

Maintain a synthetic evaluation set as behaviour is specified; evaluate meaningful
changes to interpretation, retrieval, ranking, research decisions and optional AI.
Record material experiments. Promote significant behaviour changes only after
testing and human approval, retaining the previous validated version through Git.
These are required improvement practices, not claims that evaluation exists.

Course follow-up proposals, including application CI, a Context7 development MCP
pilot and reproducible Docker delivery, are tracked in
[DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#proposed-follow-up-work) and
[TASKS.md](TASKS.md). They authorize no installation or implementation.
