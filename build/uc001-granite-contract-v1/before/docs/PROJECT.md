# PROJECT.md

Project baseline, structure, commands and historical setup evidence.
Accepted scope/architecture/privacy: [ARCHITECTURE.md](ARCHITECTURE.md).
Development and review procedures: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).
Product context for requirements, UX and comparisons: [PRODUCT_CONTEXT.md](PRODUCT_CONTEXT.md).

## Purpose

### Project

Resolena Alternative Finder — a standalone module developed as a solo
FHNW AI-assisted Software Development Capstone, with future integration
into Resolena's website or mobile app.

### Problem and intended users

People seeking practical alternatives to everyday purchases and habits
need understandable comparisons of financial savings and environmental
or resource implications.

The module helps them explore better choices while building a reusable
Resolena knowledge base. Guidance should be practical, transparent and
non-judgmental.

### Scope summary

[UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md) supports text/location requests,
knowledge reuse before research, evidence-backed comparison and persistence.
[UC-003](specs/UC-003-SELECT-DISPLAYED-ALTERNATIVE.md) records explicit selection.
Optional image input (UC-002) is deferred until the full mandatory UC-001 + UC-003
journey, including research, is validated. The canonical
[accepted scope](ARCHITECTURE.md#accepted-scope) defines the included capabilities,
optional-input constraints and exclusions; its
[privacy boundary](ARCHITECTURE.md#strict-runtime-privacy) remains binding.
On 2026-10-11 the owner retained approved multilingual free text and controlled
processing (A in [ADR-004](adr/ADR-004-multilingual-interpretation-scope.md)); no
structured-input scope reduction. The integration DESIGN/ADR-003 baseline was
accepted on 2026-10-15; interpreter selection, production hosting, reviewed knowledge
and qualified linguistic validation remain open delivery dependencies.

### Specification boundary

Acceptance criteria, retrieval thresholds, ranking rules and detailed
adapter behaviour are defined during SPECIFY/DESIGN.
This section records scope; it does not claim these features exist.

## Architecture

Use Clean Architecture with ports and adapters and inward dependencies.
React/TypeScript accesses the FastAPI API; infrastructure implements database,
research and optional AI ports without coupling domain rules to providers.

UC-001 retrieves and assesses existing knowledge before research. Persist
requests, shown alternatives and evidence before presentation and selection;
selection affects relevance, never factual validation. Keep collected data in
Resolena-controlled persistence and out of external LLM providers. Development
and review use synthetic/non-sensitive examples only.

The full boundaries, conceptual entities, strict privacy rules, controlled
improvement practices and pending decisions are maintained in
[ARCHITECTURE.md](ARCHITECTURE.md). These describe intended behaviour;
UC-001's first synthetic saved-comparison slice is implemented/verified; it does not
implement verified interpretation, reviewed knowledge or the full increment.
UC-003 remains unimplemented.

## Structure

### Application and tests

| Directory | Responsibility |
|---|---|
| `src/app/domain/` | Business concepts and rules |
| `src/app/application/` | Use-case orchestration and adapter ports |
| `src/app/interfaces/` | API routes and request/response handling |
| `src/app/infrastructure/` | Database and external-service adapters |
| `tests/unit/` | Tests of individual rules and components |
| `tests/integration/` | Tests of components working together |
| `tests/e2e/` | Tests of complete application flows |
| `frontend/` | React/TypeScript frontend and Vite configuration |
| `frontend/src/` | React comparison form and committed-result display |
| `tests/support/` | Explicit test-only interpreter, synthetic evidence and demo composition; never normal runtime adapters |
| `frontend/public/` | Static frontend assets |

The backend/test directories were empty after BOOTSTRAP. Priority 1 now introduces
the saved-comparison application ports, SQLite adapter and isolated tests below.

The recorded bootstrap checks covered the starter only. Current priority-1 checks
are recorded below; these are separate from the historical migration evidence.

### Project guidance and setup

- `AGENTS.md`: shared agent instructions and lifecycle routing.
- `docs/PROJECT.md`: concise project baseline, commands and setup evidence.
- `docs/ARCHITECTURE.md`: canonical scope, architecture and privacy boundaries.
- `docs/DEVELOPMENT_WORKFLOW.md`: canonical development/review workflow.
- `docs/adr/`: approved decisions and preserved decision history.
- `docs/TASKS.md`: current phase, status and work queue.
- `docs/specs/`: use-case specifications and the specification template.
- `skills/`: canonical AI-SDLC phase instructions.
- `.agents/skills`: agent discovery link to the canonical skills.
- `.devcontainer/`: reproducible Codespace configuration.
- `scripts/`: environment and agent setup scripts.
- `environments/python/`: source Python environment profile.
- `requirements.txt`: root-level Python dependency manifest.
- `.github/workflows/`: CI, release and deployment workflow templates.

## Commands

Run these commands from the repository root in the Codespace.

| Activity | Command |
|---|---|
| Install backend dependencies | `.venv/bin/python -m pip install -r requirements.txt` |
| Check backend dependency compatibility | `.venv/bin/python -m pip check` |
| Install frontend dependencies | `npm --prefix frontend install` |
| Lint frontend | `npm --prefix frontend run lint` |
| Build frontend | `npm --prefix frontend run build` |
| Start frontend development server | `npm --prefix frontend run dev -- --host 127.0.0.1` |
| Backend unit/integration tests | `.venv/bin/python -m pytest` |
| Real browser/API/SQLite tests | `npm --prefix frontend run test:e2e` |
| Start normal API (no real adapters configured) | `PYTHONPATH=src .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |

The frontend development server normally uses port 5173.
Open it through Codespaces port forwarding with visibility set to Private.
Stop the server with Ctrl+C.

The frontend proxies `/api` to loopback port 8000; browser tests use separate ports
8011/5175 and a new SQLite file per invocation. The frontend build creates
`frontend/dist`; deployment is not configured. Normal API startup has no fixture
imports, database seed or real interpreter and returns `configuration_unavailable`.

### Test-only local demonstration — Codespaces Bash

Run from the repository root in two Codespace terminals (not Windows PowerShell):

```bash
# Terminal 1: isolated synthetic API; database retained under Git-ignored build/
PYTHONPATH=src:. .venv/bin/python -m tests.support.demo --db build/test-only/manual-demo.sqlite3
```

```bash
# Terminal 2: React, with loopback API proxy
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open forwarded port 5173 with visibility **Private**. Use only synthetic text:
`Repair my bicycle without replacing it`, country `CH`. The exact-match test
interpreter and two synthetic repair providers are not real language/knowledge
support; their fixed clock/review metadata is artificial. Other inputs/configurations
are explicitly unavailable, not classified as unsupported languages or coverage.
Country `DE` with the same exact synthetic text demonstrates saved insufficient
coverage; this establishes no real German-market coverage or absence.
The exact synthetic `Velo` fixture exercises explanation-language preference/choice;
`Synthetic unsupported input` and `Synthetic unclear clause` exercise distinct
unsaved outcomes. Only English synthetic rendering is configured. A missing target
renderer returns a limitation and permits explicit correction; no translation is
fabricated. Choices/preferences live only in current-page memory, with one supported
browser language captured separately from country.
The additional exact `Synthetic hourly bicycle repair` fixture exercises the new
source-bound renderer in DE/FR/IT/EN using synthetic review substitutes;
`Synthetic pending bicycle repair` remains an unsaved review limitation.
These establish application/display wiring, not real linguistic competence.
There is no model, external inference, research, selection or history endpoint.
Stop both owned servers with Ctrl+C; the isolated database remains. CLI database
paths must be separate `.sqlite3` files beneath `build/test-only/`.

### Browser test setup

Only Playwright Test 1.64.1 was added (development dependency, pinned/locked).
Existing pytest/httpx exercise backend rules and real file-backed SQLite; no new
Python test dependencies, Vitest or component-test packages are needed for this slice.
Browser artifacts/results stay under Git-ignored `build/`.

```bash
PLAYWRIGHT_BROWSERS_PATH="$PWD/build/playwright" ./frontend/node_modules/.bin/playwright install chromium --only-shell
```

On a fresh Debian 12 Codespace, Chromium also needs native libraries. The initial
launch identified missing libraries; only these packages and their dependencies
were installed, with no system upgrades:

```bash
sudo apt-get install -y --no-install-recommends libatk1.0-0 libatk-bridge2.0-0 libdbus-1-3 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libasound2 libatspi2.0-0
```

This records remote Linux setup, not Windows/laptop compatibility. See publisher
[browser prerequisites](https://playwright.dev/docs/browsers) and
[owned test-server lifecycle](https://playwright.dev/docs/test-webserver).
Tests use one worker, zero retries and refuse to reuse existing servers.
The browser configuration creates a unique synthetic clock JSON beneath
`build/test-only/`, initially at the fixture instant. Test-only
`RESOLENA_E2E_CLOCK_FILE` / demo `--clock-file` can select a controlled file there;
this never changes normal `app.main`. Tracing is disabled to exclude proof headers
from artifacts; recorded proof comparisons are booleans, never raw headers.

### Priority-1 verification — 2026-10-15

- TDD RED: backend collection failed on absent application modules; 8 backend tests
  then passed. Browser launch initially failed on missing native libraries (setup
  failure, not an application assertion); after installing them, both assertions
  failed against the untouched starter, then passed against the implementation.
- `.venv/bin/python -m pytest`: 8 passed. Real temporary SQLite files verify exact
  committed projections/IDs/order, original text/no-replacement spans, evidence
  associations/immutability, rollback on the second evidence link, normal-runtime
  fixture isolation and basic same-key/proof/payload acknowledgement guards.
  A rendering failure never enters saving. The existing FastAPI/Starlette stack
  emits an httpx TestClient deprecation warning; tests pass without dependency changes.
- `npm --prefix frontend run test:e2e`: 2 passed. Real React → Vite proxy → FastAPI →
  SQLite, without mocked API responses. Success matches displayed/stored IDs/order;
  a real SQLite trigger failure shows no comparison, preserves fields and rolls back
  all new request/option/evidence-link rows. Reloading does not delete saved results
  or introduce a history replay. Test servers stop after the run.
- `npm --prefix frontend run lint` and `npm --prefix frontend run build`: passed.
  Reports and isolated databases are under `build/uc001-slice1/` and `build/test-only/`.

This is partial coverage of AC-01/08/10/11/13/14 and T-08/09/11, not completion of
those matrices or increment 1. Production interpreter/hosting, real reviewed
knowledge, qualification/freshness/location matrices, multilingual/preference/
clarification/faithful-rendering behaviour, qualified review, exhaustive recovery
faults/races and UC-003 remain pending. No model/detector execution or held-out-case
inspection occurred. No CI, production deployment or Windows compatibility is claimed.

### Priority-2 verification — 2026-10-15

Qualification & Coverage only; priority 1 and the existing uncommitted work remain.
TDD started with missing-domain-module and coverage/expiry API failures; the new
browser coverage assertion failed before UI implementation. Focused regressions
preceded cost, scope, JSON round-trip and component-price corrections.

- `.venv/bin/python -m pytest -q`: **57 passed**; existing Starlette/httpx
  deprecation warning remains. Focused AC-03–09/12 and domain AC-16 coverage:
  exact scoped support/competence, conflict versus contradiction, essential/optional
  unknowns, all five expiry windows/boundaries, earlier expiry/invalidation,
  timestamp precision/time zones and distinct data periods; independent country/
  intended-locality applicability; useful content; exact source-currency/unit/
  period/basis/charges, user-reported baselines, budget and cheaper comparisons;
  qualification before normalized alphabetical ordering, UUID ties and limit.
  AC-01/07/10/11 boundary tests distinguish valid coverage, invalid input,
  clarification, interpretation limitation, processing and coverage-save failures.
  Real SQLite verifies saved zero-option coverage/recovery, immutable evidence,
  saved projections, partial-write rollback, reopening and retry after expiry.
- `npm --prefix frontend run test:e2e`: **4 passed**, real React/API/file-backed
  SQLite. Priority-1 success/rollback plus changed-country saved coverage and
  coverage-save failure, preserved fields, terminal loading, exact committed
  projections and explicit unknown amounts/availability/resource information.
- `npm --prefix frontend run lint` and `npm --prefix frontend run build`: passed.
  Browser reports remain under `build/uc001-slice1/`; isolated databases under
  `build/test-only/`. Priority-2 verification is recorded in
  `build/uc001-priority2/verification.json`; the priority-1 verification file is retained.
  Owned browser servers stopped. No dependencies changed.

Claims depend on prepared, reviewed typed mappings (competence, exact scope,
assertions, temporal applicability and calculation inputs); these checks cannot
independently establish factual or linguistic truth. All exercised knowledge,
interpretation and rendering remain synthetic/test-only. No real catalogue,
reference-data release, interpreter or faithful four-language renderer is supplied.
AC-01/02/15/16 input/reference/language journeys, exhaustive recovery/security and
fault/loading matrices, qualified review and later priorities remain incomplete.
The [2026-10-16 scope mapping](TASKS.md#localitypersistence-scope-clarification--2026-10-16)
distinguishes implemented geographic qualification from these remaining input and
reference/recovery cases; it uses this existing evidence without rerunning checks.
Normal composition remains unconfigured; no real-world knowledge coverage,
language validation, research, held-out access, model execution, CI or delivery
is claimed. Phase 3 stays in-progress; stop after Priority 2.

### Priority-3 partial verification — 2026-10-16

Bounded contracts/application policy only (AC-01/09/10/11/13–15; TL-01/02/04);
no verified four-language semantics. Accepted UC/ADRs remain unchanged. The
priority-2 locality/persistence mapping is in TASKS.md; no separate unfinished
geographic qualification requirement or material conflict was found.

RED: absent contract module; then seven initial API failures before routing;
three browser failures before choice/correction/targeted messages. Focused RED/GREEN
checks exposed ignored action metadata, clarification precedence, unavailable-target
correction and prior correction incorrectly overriding a new clear request.

- `.venv/bin/python -m pytest -q`: **113 passed**, including all 57 priority-1/2
  checks; existing Starlette/httpx deprecation warning remains. Tests cover original
  hypotheses versus normalized English, all four synthetic language-policy labels,
  mixed clauses, source offsets/quotations/negation, exact amounts/currency/units/
  basis and ambiguous `1,200`, novel/joint subjects, essential actions/textual
  locality constraints, preference/correction precedence and country independence.
  Real isolated SQLite checks saved provenance/coverage, unchanged payload binding,
  unsaved uncertainty/capability/faults and selected rendering language before saving.
  A fresh-process check confirms normal composition imports no test adapters.
- `npm --prefix frontend run test:e2e`: **8 passed** through real API/SQLite:
  four priority-1/2 journeys plus choice, correction/preference, unavailable rendering
  and distinct meaning/capability outcomes. Fields/country survive; no automatic
  resubmission or initial compulsory selector. Browser preference stores no region
  or full locale list and never determines search country.
- Frontend lint and TypeScript/Vite build: passed. No dependencies changed.
  Detailed scope/results: `build/uc001-priority3/verification.json`; earlier
  priority-1/2 verification files remain. Browser reports use the existing
  `build/uc001-slice1/` directory; isolated databases remain under `build/test-only/`.

Only test support supplies exact fixtures and synthetic English narratives.
Source assertions were extended with new immutable synthetic evidence versions,
not overwritten. Contract completeness is structural: a dishonest/wrong adapter can
still misreport meaning, polarity, numeric reading or original language. Real
interpreter/recognizer selection and qualified DE/FR/IT/EN review remain pending;
neither a stub label nor agreement between adapters validates semantics. Real
knowledge, reference-data integration, faithful four-language rendering and complete
recovery/fault/loading matrices remain at their mapped later work. No real adapter,
experiment, held-out access, knowledge release, delivery or phase transition occurred.
Priority 3 remains partial; Phase 3 stays in-progress. Stop after this bounded step.

### Priority-3 offline candidate preparation — 2026-10-16

Owner authorized offline preparation of the retained Qwen3-8B Q8_0 / llama.cpp
b11429 test candidate, not interpreter acceptance or a live run. No dependency,
normal composition, domain/application policy, SQLite, frontend, UC/ADR or
historical-result changes. New adapter/tests and an explicitly isolated development
composition use the existing interpreter contract and synthetic knowledge/English
renderer. Original text/versions stay trusted; country/preferences are never sent
to interpretation. The optional recognizer stays disabled.

The [prepared bundle](../scripts/uc001_contract_check/README.md) contains the exact
next Windows read-only preflight command, frozen 14-case manifest/prompt/schema/
configuration, retained hashes, transport package plan, separate scripts, qualified
review gate and fixed generation/time/resource controls. `Velo` requires meaning
clarification without context; mixed and numeric uncertainty follow L-02/03.
Expectations are AI-generated, not qualified approval. No requirement conflict found.

TDD RED: absent HTTP adapter/control modules; protected-authentication helper absent;
an assertion demonstrated that an unverified thinking template could reach generation
before the effective non-thinking guard was added. A missing read-only capacity
probe failed against mocked Windows metadata before implementation. Focused GREEN
also fixes a request-envelope assertion against the retained schema-constrained
`json_object` format before any runtime use. Final checks: **165 backend tests**
(52 new offline tests, all earlier 113 retained), **8 existing browser/API/SQLite
journeys**, frontend lint and build passed. Browser scenarios were unchanged;
no new user-visible flow needs additional browser cases. The existing Starlette/
httpx deprecation and historical TASKS.md whitespace warning remain. Verification
uses only MockTransport, synthetic metadata and offline PowerShell parsing/C#
compilation; it invokes no Windows preflight, native GPU calls or model binary.
PowerShell-specific checks used pre-existing `pwsh` in this Codespace; they skip
with an explicit unverified reason if it is absent, without installing a tool.
Full check counts and exact changed-file list are recorded separately in
`build/uc001-contract-preparation/verification.json`; earlier verification files remain.

Desktop asset/tool/resource confirmation, actual Windows script/runtime/schema/
context compatibility, approved transport installation/SSH binding, qualified
DE/FR/IT/EN review and live semantics remain unresolved. Public `/health` is not
authentication evidence. Structural validation cannot detect every semantic
omission; unavailable target rendering is separate from unsupported input. No
real model/detector execution, download, install, tunnel, held-out access, Priority-4
content or Git delivery occurred. Priority 3 stays partial; Phase 3 in-progress.

### Priority-3 adapter-association correction — 2026-10-16

The owner-reported Windows diagnostic establishes separate RX 6800 XT hardware
and Microsoft software adapter LUIDs/counters. The bounded
[v1.1.0 preflight package](../scripts/uc001_preflight_association_v1_1_0/README.md)
matches hardware descriptor/PCI/CIM/registry identity and capacity, obtains a fresh
unique DXGI LUID and requires one exact corresponding WDDM counter. Missing,
ambiguous, inconsistent and failed data still stop; measured zero remains valid.
Original frozen source/ZIP/failure evidence are preserved; this separate package
contains no launcher/runner and performs no model/runtime asset hashes.

TDD RED reproduced the global-counter defect and exposed invalid flags/multiple
physical counters. **56 focused association and existing run-control tests passed**
with synthetic Windows metadata and C# compilation/layout checks; no native reader
was called. All 30 protected hashes match, configuration/runtime pins are identical
and the resource-guard function is unchanged. The reported 13.651 GiB estimate
remains below the unchanged 14 GiB start threshold, independently of association.
Native DXGI calls and possible Windows Add-Type temporary files are documented.
Actual Windows verification is pending; Priority 3 remains partial, Phase 3
in-progress. Package hashes, changed files and limits of verification:
`build/uc001-preflight-association-v1_1_0/verification.json`.
No installation, transport, inference, held-out access or Git delivery occurred.

### Priority-3 DXGI capacity-source correction — 2026-10-16

Owner authorized [v1.2.0 preflight only](../scripts/uc001_preflight_capacity_v1_2_0/README.md):
the identified hardware adapter's DXGI dedicated-video bytes supply capacity.
Registry reading/path, availability, raw type/value and exact signed difference
remain diagnostics without fallback or tolerance. Supplied readings are preserved:
17130819584 DXGI versus 17163091968 registry, difference -32272384 bytes;
cause unknown. Earlier bundles/failures/evidence remain unchanged.

TDD starts with both unequal-reading directions and missing-registry failures.
Focused synthetic checks verify DXGI-only sampling, invalid capacity, identity/
counter stops, zero usage and exact threshold boundaries. Existing association
and run-control regressions are retained: **114 tests passed** (58 new, 44 earlier
association/package, 12 run-control). All 46 protected hashes match. Native reader, runtime/model pins,
configuration and every resource threshold remain unchanged. Full package extraction
and exact Windows command are in the linked instructions; Add-Type/native effects
remain disclosed. Final counts/hashes and offline limits:
`build/uc001-preflight-capacity-v1_2_0/verification.json`. Actual Windows verification
is pending; Priority 3 remains partial, Phase 3 in-progress. Application/browser
code is unchanged; no installation, transport, inference or Git delivery occurred.

### Remaining desktop readiness — 2026-10-16

Supplied raw v1.2.0 Windows JSON verifies **adapter identity and one resource
snapshot only**, with 13099008 bytes above the unchanged GPU start threshold.
Record: `build/uc001-desktop-readiness/windows-v1_2_0-result.raw.json`. Require a
fresh v1.2.0-policy check before future authorized startup; full preflight and
interpreter suitability remain unverified.

The original reported adapter stop follows all 54 retained integrity checks
(runtime ZIP, model, 52 extracted files). This is conditional historical code-order
evidence, without a per-file completion receipt or fresh content proof; preserve
it without repeating the large hash for this remaining check. Fresh integrity
validation remains required before execution. The
[new checker](../scripts/uc001_desktop_readiness/README.md) uses the unchanged
v1.2.0 preparation, queries local native OpenSSH/gh versions and desktop ports,
and starts no native GPU reader, resource monitor, transport or model.

Execution blocker: frozen original launcher/monitor retain weaker adapter selection
and counter/usage enforcement; alignment with v1.2.0 requires a separate correction.
DXGI capacity is already used by that launcher. Transport installation/binding,
authorization (not inspected), remote port 49188, effective runtime settings and
qualified semantic review remain pending. Offline results and preserved hashes:
`build/uc001-desktop-readiness/verification.json`: **124 offline tests passed**
(10 new, 114 retained); all 60 protected hashes match. Priority 3 partial; Phase 3
in-progress. No original bundle or historical result was changed.

### Launcher/monitor correction v1.3.0 — 2026-10-17

Separate [execution preparation](../scripts/uc001_execution_v1_3_0/README.md) applies
the v1.2.0 native identity/DXGI capacity/exact-counter policy at startup and every
runtime sample. Owned PID/LUID/phys_0 attribution and process-lifetime checks
distinguish missing data from zero; strict measurement bounds and robust owned
cleanup abort on failures. All resource thresholds, deadlines, cadence, startup/
generation limits, model/runtime pins, cases, prompt/schema and application remain.
Original native ownership helper and Python controls/composition are unchanged;
runner imports bind only to the versioned copy. The original attempt-directory
identity blocks restarts across versions, while receipts/review bind the new freeze.

TDD RED exposed missing/foreign owned rows becoming zero and absent runtime identity
revalidation. Tests invoke real launcher control flow with fake native/process/HTTP
operations, including aborts, cleanup failures and existing attempts. This is offline
evidence only. **174 tests passed** (50 new, 124 retained); all 76 protected hashes
match. Final command/counts, changed files and hashes:
`build/uc001-execution-v1_3_0/verification.json`. Windows owned-counter/cleanup
behaviour, fresh resources, tools/ports, transport setup and qualified review remain
pending. No execution/transport or phase advance is authorized; Priority 3 partial,
Phase 3 in-progress. Earlier raw snapshots/failures/bundles are preserved.

### Supplied desktop tools/ports result — 2026-10-17

Owner's raw remaining-check JSON is retained under
`build/uc001-desktop-readiness/results_2026_10_17/`: native/PATH OpenSSH
9.5p2 / LibreSSL 3.8.2, gh 2.81.0 and no observed TCP allocations at desktop
49187/49189 passed. It supplies no execution timestamp or fresh asset hashes and
does not check Codespace 49188, actual binds, transport or credentials. The raw
original-launcher blocker string is preserved; v1.3.0 separately corrects that
policy offline, with Windows owned-process runtime verification still pending.
Full preflight/startup authorization remain false; fresh startup integrity/resources
and qualified review remain required. Documentation/evidence checks only; no code
or package change, model/transport execution or phase advance. Priority 3 partial.

### Model-free native ownership diagnostic preparation — 2026-10-17

Separate [diagnostic and exact Windows command](../scripts/uc001_native_ownership_check/README.md)
exercise the unchanged v1.3.0 native owned-job/process helper, PID/creation-time
checks and abort/cleanup functions with a sleeping child. The 60-second supervisor
rejects unconfirmed cleanup and preserves each diagnostic result outside the model
attempt ledger. Offline substitutes verify failure paths; actual Windows results,
owned-GPU counters/allocation and authorized startup remain pending. No GPU data
is fabricated or queried. Tests/preservation: `build/uc001-native-ownership-check/verification.json`.
Priority 3 partial; Phase 3 in-progress. Existing tools/ports evidence is retained.

### Supplied native result and transport preparation — 2026-10-17

Owner's [raw Windows native result](../build/uc001-native-ownership-check/results_2026_10_17/windows-native-result.raw.json)
passes the tested identity/abort/job-close/confirmed-child-exit path in 919 ms;
no GPU monitoring or model readiness follows. Earlier preparation records and
failures remain historical. [Transport review instructions](../scripts/uc001_transport_preparation/README.md)
record Codespace 49188 unallocated, absent sshd, matching eight-package cached plan,
exact proposed setup/authentication commands and a separate bounded model-free
forwarding/owned-cleanup check. Accounted gh plus Debian archive bytes total
25825785, leaving 79031815 under 100 MiB before additional file transfers.
Provider-managed configuration/listener compatibility and actual connection remain
unverified. Windows tools/port evidence is reused. No installation/authentication,
connection, model attempt or frozen-bundle change occurred. Results/preservation:
`build/uc001-transport-preparation/verification.json`. Priority 3 partial; Phase 3 in-progress.

### Approved Codespace transport setup — 2026-10-17

The approved eight-package plan was rechecked, downloaded once (7508700 bytes),
verified and installed once; exact versions and clean package audit recorded.
The existing service-start denial remains unchanged. An exclusively created SSH
drop-in passed syntax and effective loopback/authentication/reverse-forward checks;
no daemon, connection, index refresh or restart was initiated. [Receipts and Windows
handoff](../build/uc001-transport-setup/README.md) preserve download accounting and
provide the two unchanged scripts, approved authentication/test commands and separate
post-test 49188 cleanup receipt. Actual provider-managed connection behaviour and
GPU/model readiness remain pending. Frozen sources/evidence/model ledgers are
unchanged. Priority 3 partial; Phase 3 in-progress.

### Failed model-free transport attempt — read-only diagnosis, 2026-10-17

Owner-supplied 7791 ms banner/refusal failure and confirmed gh authentication
metadata are [preserved separately](../build/uc001-transport-diagnosis/failed_attempt_2026_10_17/README.md).
The existing separate 49188 cleanup receipt passed. Live sshd PID 61844 binds
127.0.0.1:22; the drop-in is unchanged. Accessible broker logs predate the attempt,
so the exact refusing hop/target is unresolved. No server correction is justified
yet; a minimal Windows effective-client-config inspection is provided. Only
read-only inspection and evidence/content checks ran; no connection, daemon/config
action or retry. Earlier setup receipts/bundles remain historical and unchanged.
Priority 3 partial; Phase 3 in-progress; no GPU/model readiness conclusion.

### Logging-only transport preparation — 2026-10-17

[Windows ssh -G summary and logging variant](../build/uc001-transport-logging/README.md):
no proxy/IPv4 override; the unchanged model-free flow is sourced with logging-only
arguments, private local results and fixed-field sanitized sharing. Source review
shows unused gh debug-file flags and a discarded tunnel logger, so broker-target
visibility remains uncertain. Twelve new offline checks and fourteen retained
transport checks passed; actual Windows ACL/logging/transport are unverified.
Original attempt's Windows cleanup receipt remains missing; Codespace cleanup
passed. No endpoint/connection/native startup, service/config change or retry.
Priority 3 partial; Phase 3 in-progress. GPU/model/semantic readiness remains pending.

### Logging wrapper parser correction v2 — 2026-10-17

[Separate preparation and evidence](../build/uc001-transport-logging-v2/README.md)
preserve the second Codespace cleanup pass at 16:52:10.674073 UTC and supplied
sanitized Windows JSON: failed after 4062 ms with owned cleanup confirmed,
gh log present, separate SSH log missing and all reported stage/error markers
false. Its pending remote-cleanup field remains unchanged; the separate receipt
records the subsequent cleanup pass. These markers do not resolve the cause.
gh's pinned parser omits E, invalidating the earlier support claim and argument-only
check. V2 removes -E/path, preserves -vvv and all controls, and identifies combined
private stderr as its summary source. Source-derived parser/command construction
and synthetic flow/cleanup checks pass: 37 focused tests. No Go binary or Windows
native verification is claimed. Possible stray gh-bin `-p` log and original
banner refusal remain unresolved; metadata-only Windows inspection is prepared.
Old scripts/evidence/bundles remain intact; no connection, service/config change,
tool installation/download or model work. Priority 3 partial; Phase 3 in-progress.

### Third model-free transport attempt — evidence-only diagnosis, 2026-10-17

[Owner-pasted Windows JSON and targeted diagnosis](../build/uc001-transport-diagnosis/attempt_3_2026_10_17/README.md)
record 6771 ms failure after local bridge connection, then banner refusal; Windows
owned cleanup confirmed. The unchanged separate Codespace receipt passed at
18:08:04.291430 UTC. Current SSH binds 127.0.0.1:22; accessible prior broker log
locations supply no attempt-time target/error. No mismatch or exact refusing hop
is established. Diagnosis stops pending an existing host-side broker trace;
no further attempt, wrapper, regressions or service/config/model action. Prior
evidence remains intact. Priority 3 partial; Phase 3 in-progress.

### Fourth model-free transport attempt — evidence recording, 2026-10-17

[Owner-pasted JSON, unchanged cleanup receipt and unsent Support draft](../build/uc001-transport-diagnosis/attempt_4_2026_10_17/README.md):
5819 ms failure with the same markers as attempt 3; Windows owned cleanup
confirmed, Codespace cleanup passed at 18:30:57.818745 UTC. Owner-reported NordVPN
desktop/browser disconnection did not resolve the observed failure; other filtering
components remain unverified and the cause unknown. Historical diagnosis reused
without searches or regressions. Draft requests existing host-side broker traces,
distinguishing cleanup observations from unknown exact starts; availability unknown.
Nothing sent or executed; prior evidence preserved. Priority 3 partial;
Phase 3 in-progress.

### Windows shared-validator setup preparation

[Setup and offline check](../scripts/uc001_validator_setup/README.md) use explicit
Python 3.12.10 x64/venv executables and UTF-8 mode, 11 shared-validator dependencies
plus pytest's six-package test stack, with every wheel/version/hash pinned. Last
3.12 Windows installer; later 3.12 security fixes are not included. No global PATH
change or application/root-requirement change. External payload is 31,902,158 bytes;
remaining allowance is conditional on reconciled additional acquisitions, with
cache reuse and reservation retained on failure. [Preparation receipt](../build/uc001-validator-setup/verification.json):
7 unchanged existing tests and shared import/schema/decoder/case probes passed from
the source export in Codespace; command blocks parse offline. Actual Windows
installer/signature, dependency imports and compatibility tests remain owner-run.
SSH/Support work paused; no inference, connections, model-ledger reset or semantic
capability claim. Qualified review/live integration pending; Priority 3 partial,
Phase 3 DEVELOP in-progress.

### Windows-local capture / Codespace replay — offline implementation

[Instructions and model-free Windows handoff](../scripts/uc001_contract_local/README.md)
reuse the verified Python environment, unchanged adapter/domain/case checks and
v1.3.0 native ownership/monitoring/cleanup. Owner-pasted setup/compatibility results
are preserved separately; 46,845,816 bytes remain as reported, with no new dependency
acquisition. These results establish environment compatibility only.

The same original attempt directory and RunBudget prevent another startup/ledger
reset. A separate native-job deadline timer closes the owned job at 90 seconds
independently of Python validation or a blocked PowerShell measurement; late/unconfirmed
results stop. Bounded raw-body capture precedes parsing, with private incomplete/secret
captures and a scanned export. Replay has no network fallback, uses synthetic application
composition and explicitly leaves live API/real-adapter cases 1/5/10 open.

[Verification](../build/uc001-contract-local/verification.json): meaningful RED/GREEN,
**202 passing checks**, one retained deprecation warning; preserved parent settings,
application source and historical bundles. Windows native timing/job-close behavior,
fresh integrity/resource/owned-GPU checks and qualified linguistic/semantic validation
remain pending. No browser change, model startup, inference, connection or phase advance.
Priority 3 partial; Phase 3 DEVELOP in-progress; SSH/Support work paused.

Owner follow-up, 2026-10-18 (Europe/Berlin):
[Windows preparation passed as reported](../build/uc001-contract-local/owner-results/review_2026_10_18/windows-preparation.owner-pasted.json).
[Partial owner expectations review](../build/uc001-contract-local/owner-results/review_2026_10_18/partial-expectations-review.json)
is bound to the same local freeze: cases 2/5/10/11/13/14 and Swiss German case 12
confirmed; cases 1/3/4/6/7/8/9 unapproved. Overall review remains pending,
`expected_meanings_approved: false`, with no model-output validation or startup
authorization. Frozen files and prior evidence preserved; no tests or rebuilds.

Subsequent owner decision permits the original bounded technical feasibility check
while linguistic approvals remain pending. [v1.1.0 owner handoff](../scripts/uc001_contract_local_v1_1_0/README.md)
uses a separate decision gate in launcher/capture/replay, preserves the original review
and hash binding, and keeps expectations provisional, semantic approval false and
technical/policy results separate. [Verification](../build/uc001-contract-local-v1_1_0/verification.json):
48 focused checks passed after RED; original source/package/receipts, controls and
attempt allowance preserved. Reuses completed Python/dependency setup; fresh Windows
integrity/identity/resources, real native readiness/cleanup and semantic review remain
pending. Replay cannot satisfy live cases 1/5/10. Priority 3 partial; Phase 3 in-progress.

Current owner report consumes the original single startup allowance; no restart or
replacement attempt is authorized. [Reported evidence](../build/uc001-contract-local-v1_2_0/owner-reported-failure.json)
retains the pre-generation failure and separate parent-PID probe without reconstructing
raw files or an absent ledger. [v1.2.0 model-free handoff](../scripts/uc001_contract_local_v1_2_0/README.md)
corrects exact redirector/interpreter ownership and cleanup, separates pinned reported
defaults from CLI/request output limits, and emits safe stage/reason codes.
[Verification](../build/uc001-contract-local-v1_2_0/verification.json): 118 focused/relevant
checks passed after RED; Windows native proof remains pending. Saved receipt checks
cannot supply missing historical CLI/generation evidence. Previous bundles, reviews,
all pins/limits and partial semantic status are preserved; no new model allowance.

[v1.2.1 reporting follow-up](../scripts/uc001_contract_local_v1_2_1/README.md): the owner
reports a 680 ms model-free failure with no bound interpreter. Primary failure is now
independent of cleanup/deadline failures; retained interpreter identity no longer depends
on completed `LastProof`. Missing identity remains a failure, distinct from a known
identity with unconfirmed exit. The original initiating exception is unavailable;
one prepared model-free check records the missing native step/status and cleanup,
keeping raw detail private. [35 focused checks passed after RED](../build/uc001-contract-local-v1_2_1/verification.json).
Windows execution pending; failed v1.2.0 preserved. No new model allowance, dependencies,
transport or automatic rerun. Priority 3 partial; Phase 3 in-progress.

[v1.2.2 console-helper correction](../scripts/uc001_contract_local_v1_2_2/README.md)
records the owner-reported v1.2.1 rejection of an owned system console host. Native/Python
binding now accounts for all roles, retaining exact interpreter identity and at most one
strictly validated system-path helper. Helper-only startup waits; unknown/ambiguous members
fail. Held helper handles survive partial binding for confirmed-exit cleanup; missing
interpreter identity still fails. Independent failure channels/private detail are preserved.
[77 focused offline checks passed](../build/uc001-contract-local-v1_2_2/verification.json);
actual Windows behavior is pending one prepared model-free check. Prior packages/receipts,
settings/limits and consumed model allowance stay intact. No model/capture/SSH execution,
dependency acquisition or allowance reset. Priority 3 partial; Phase 3 in-progress.

### Native harness closure and proposed additional attempt — 2026-10-18

[Owner-pasted result/worker/cleanup receipts](../build/uc001-contract-local-v1_2_2/owner-results/results_2026_10_18/verification.json)
verify only the tested v1.2.2 native ownership/binding/cleanup path (1667 ms, all three
owned exits confirmed). Harness debugging is closed; model/GPU readiness and semantic
acceptance remain unverified. Earlier failures, frozen packages and missing historical
CLI/generation evidence stay unchanged; no passed Windows check is repeated.

[Separate proposed execution handoff](../scripts/uc001_contract_local_v1_3_0/README.md)
links a new identity to the consumed original and requests one additional startup/
at most 14 unchanged ordered generations under existing limits. Its default-false approval
gate blocks both launcher and capture pending explicit owner approval. Verified native and
settings code remains unchanged; new startup/argv and generation evidence is prospective,
with exclusive attempt reservation and no historical ledger reset. Focused offline wiring/
abort/cleanup/replay tests are recorded in [verification](../build/uc001-contract-local-v1_3_0/verification.json).
No actual additional startup or inference occurred. Pending linguistic review, technical-only
classification and deferred live cases 1/5/10 remain; SSH/Support paused. Priority 3 partial;
Phase 3 DEVELOP in-progress.

### Combined-job failure and model-free follow-up — 2026-10-18

The owner reports the additional v1.3.0 startup consumed its allowance and stopped at
`ownership/console_helper_ambiguous`; no failed-run helper identities or generation count
were supplied. No further startup/inference is authorized. The earlier v1.2.2 success
remains evidence for its tested Python branch, rather than the combined model job.

[Separate observation/cleanup correction and one Windows handoff](../scripts/uc001_combined_ownership/README.md)
reuse production launch primitives with a sleeping PowerShell server stand-in and idle
installed Python. Observed handles survive classification failure, without approving
unknown roles. Missing identity/job/handle evidence or unconfirmed exit still fails;
primary, cleanup and deadline records are independent. Global helper/ancestry acceptance
and the Python validator remain unchanged until actual Windows branch evidence arrives.
[Offline verification and the precise pending evidence](../build/uc001-combined-ownership/verification.json)
are separate from frozen packages/receipts. No original/additional attempt reset, model or
asset check, installation, transport, held-out or semantic work. Priority 3 partial;
Phase 3 DEVELOP in-progress.

### Combined branch correction and verification handoff — 2026-10-18

[Owner-pasted Windows records](../build/uc001-combined-ownership-v1_1_0/owner-evidence/provenance.json)
show one exact system conhost per stand-in branch and the base interpreter under the
redirector. All five observed exits are confirmed; the historical overall cleanup remains
false because interpreter role classification failed. Earlier evidence is unchanged.

[Separate 1.1.0 model-free check](../scripts/uc001_combined_ownership_v1_1_0/README.md) corrects
native/Python helper validation by branch and includes full server identity, trusted path,
ancestry/lifetime and fresh exact-job proof. Retained handles remain independent of role
approval. It must pass native binding, the actual owned Python validator and final native
revalidation, then exit-confirmation cleanup; a native-only pass is insufficient.
[Offline results/package/hashes](../build/uc001-combined-ownership-v1_1_0/verification.json)
do not establish Windows native success. No new model-attempt package; both startup
allowances consumed. Semantic review pending; Priority 3 partial, Phase 3 in-progress.

### Corrected execution handoff after Windows ownership pass — 2026-10-18

[Owner-provided transcript/receipts](../build/uc001-combined-ownership-v1_1_0/owner-results/results_2026_10_18/verification.json)
verify native binding, actual Python validation, fresh revalidation and five exits in
1180 ms for the combined stand-ins. That specific ownership issue is closed; historical
failures remain unchanged, model/GPU readiness remains unverified.

[Separate v1.4.0 handoff](../scripts/uc001_contract_local_v1_4_0/README.md) reuses verified
helpers byte-for-byte and updates actual launcher/capture/replay consumers for full server
identity, trusted pinned runtime path and both helper branches/cleanup. Its distinct
proposal links both consumed attempts and requests one further startup / <=14 unchanged
ordered generations, with execution approval pending. Matching source extraction and valid
existing approval may be reused; reserved attempts still stop. No ledger reset, standalone
Windows rerun or model execution. [Offline evidence and package](../build/uc001-contract-local-v1_4_0/verification.json).
Pins, cases, limits, deadlines, partial review bindings and deferred live cases 1/5/10 stay
unchanged. Technical feasibility is separate from pending semantic acceptance; Priority 3
partial, Phase 3 DEVELOP in-progress.

### v1.4.0 offline execution closure — 2026-10-18

[Owner export, findings and verification](../build/uc001-contract-local-v1_4_0/closure_daa09499fcd8486f91cc6696279e2633/README.md)
record one startup/one case-1 generation, zero accepted cases and five confirmed exits.
The bound approval, recorded settings and full server/helper cleanup identities validate;
this allowance is consumed. Original ZIP, frozen package and previous evidence are unchanged.
Full replay refuses incomplete supervision. Exact-byte forensic replay reproduces an
unreferenced meaning-item contract violation; raw output also attaches quantities to
non-quantity items and labels the Spanish control supported English/understood. The private
Windows exception is unavailable; top-level receipt says `worker/check_failed`.
No source fix, model/experiment/regression rerun or new allowance. Cases 2–14 untested,
qualified semantics pending, live API 1/5/10 deferred; Priority 3 partial, Phase 3 in-progress.

### Priority 4 — one scenario's evidence preparation, 2026-10-18

[Draft bicycle-repair / Switzerland packet](knowledge/UC-001-BICYCLE-REPAIR-CH-DRAFT.md)
records real provider evidence, precise cost basis, dates/scopes, accepted-criteria
mapping and review gaps. It is pending review and excluded from runtime; no knowledge
release or faithful four-language rendering is completed. Documentation/content/link
checks passed; no application tests rerun. Application code, frozen bundles and closed
interpreter evidence are unchanged.
Owner review on 2026-10-18 approves the service, published CHF 120.00 hourly rate
and Oberried location extractions as provider-stated, with all conditions/unknowns.
Applicability, qualification, multilingual review and runtime use remain unapproved;
day-only review precision does not establish freshness. No new research or experiment.
Priority 3 remains partial; Phase 3 DEVELOP in-progress.

### Priority 4 — bounded rendering verification, 2026-10-19

[SourceBoundRenderer](../src/app/application/rendering.py) reuses the comparison
renderer port, language/version checks, qualification and atomic persistence.
It requires version/content/source bindings and qualified source/target review
records; synthetic review is allowed only by explicit test composition. Review
metadata is a trusted curation record, not a machine test of linguistic competence.
[Four drafts](knowledge/UC-001-BICYCLE-REPAIR-CH-RENDERINGS.json) bind the unchanged
owner-reviewed packet and stay inactive, unqualified and pending linguistic review.
Interface labels remain English; prepared evidence content has separate language
tags, translated unknowns and original source citations/excerpts.

Verification: **150 backend checks**, including **37 new rendering checks**;
**13 browser checks**, frontend lint and build passed. Relevant regressions cover
language/country policy, qualification, immutable saving, rollback and rendering
failure before saving. [Exact commands, files and RED/GREEN evidence](../build/uc001-priority4-rendering/verification.json).
No new dependencies or runtime configuration. Real source admission/freshness,
applicability/qualification, faithful four-language review and TL-03 remain pending.
Closed interpreter evidence/allowances are preserved; Priority 3/4 partial, Phase 3
DEVELOP in-progress. No research, model, experiment, held-out access or delivery.

### Priority 5A — committed save / lost response recovery, 2026-10-19

React retains the serialized submission in page memory for explicit recovery and
shows unknown delivery separately from confirmed save failure. Recovery displays
the saved identity, original outcome and original assessment timestamp without
comparison claims. Existing backend proof/payload binding, atomic persistence and
immutable projections are reused; no runtime configuration or dependency changes.

Focused verification: **5 backend checks; 1 new real-browser/API/SQLite journey
and 3 directly affected browser regressions; lint/build passed**. The new journey
also passed alone after adding a standalone evidence artifact. It aborts delivery
after real 201/commit, observes no automatic retry, sends identical key/proof/body
on explicit recovery and verifies unchanged request/options/evidence snapshots.
[Exact commands, RED/GREEN, saved IDs/counts and scope limits](../build/uc001-priority5a-recovery/verification.json).
Other Priority 5 matrices, locality/reference and complete fresh-search work remain
pending; Priority 5 and Phase 3 are not complete. Stop pending human review.

### Priority 5B — explicit fresh search after recovery, 2026-10-19

The owner accepted 5A only for atomic save/lost-response/acknowledgement recovery;
its original verification and limits remain intact. Priority 5B verifies one fresh
search after that acknowledgement, using the existing production reset/submit code.
Only synthetic clock support, browser configuration and tests required extension.
Recovery retains its captured body/key/proof; reset sends nothing; explicit fresh
submit uses new key/proof/current fields and reassesses expired evidence at a later
controlled instant. The new saved coverage outcome has its own ID/time; original
request, options, evidence associations and snapshots remain unchanged.

**1 new backend check + 8 directly affected regressions; 1 new browser journey +
5A regression; frontend lint/build passed**. Targeted reruns addressed the same
clock/default-configuration failures and add no new scenarios. [Exact commands,
RED/GREEN, IDs/counts and remaining limits](../build/uc001-priority5b-fresh-search/verification.json).
Production code/dependencies and real data remain unchanged; Priority 5, increment 1
and Phase 3 are incomplete. Stop for human review.

### Priority 5C — one controlled same-submission collision, 2026-10-19

Owner acceptance of 5B covers only verification of existing fresh-search behavior
with test-support improvements; its original receipt and limits are unchanged.
For 5C, **1 new controlled integration scenario and 4 directly affected regressions
passed** against unchanged production code. No RED failure or production fix was
needed. Both overlapping executions miss their initial real SQLite lookup and
prepare before winner commit; a test-only gate outside write transactions then
forces the loser through real unique-insert rejection/rollback and checked winner
acknowledgement. Exactly one request/two options/two evidence links remain, with
authoritative winner IDs/snapshots and unchanged evidence. No raw proofs recorded.
[Exact commands, interleaving, responses/IDs and scope limits](../build/uc001-priority5c-concurrency/verification.json).
No browser/frontend checks were needed; those files and normal configuration are
unchanged. Only this interleaving is verified; full Priority 5 remains pending.
Phase 3 in-progress; stop for review. New session setting is owner-reported as
**GPT-6.1 Sol Ultra** only; historical/runtime labels remain unchanged.

## Dependencies and technology baseline

Owner accepted React/TypeScript, Python 3.12/FastAPI, SQLite/SQLAlchemy,
pytest/httpx and Codespaces on 2026-10-04. The canonical baseline and rationale
are in [ARCHITECTURE.md](ARCHITECTURE.md#accepted-technology-baseline).

### Historical setup evidence

Recorded during BOOTSTRAP, accepted complete on 2026-10-05. This preserves
prior evidence; no setup/application/CI/deployment checks were rerun in the
2026-10-09 documentation migration. Integration into main remains unverified.

- Python 3.12.11 verified in the Codespace.
- Backend dependencies installed in the project's `.venv` environment:
  FastAPI 0.142.2, Uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1
  and SQLAlchemy 2.1.3.
- `.venv/bin/python -m pip check` completed without reported
  dependency conflicts after installation.
- Direct backend dependency versions are pinned in `requirements.txt`.
  Transitive dependencies are not yet pinned.
- SQLAlchemy is installed; database connectivity and persistence
  behaviour have not yet been tested.
- Node.js v24.21.0 and npm 11.19.0 verified after the container rebuild.
- `.devcontainer/devcontainer.json` configures Node.js major version 24
  through the Node devcontainer feature.
- Frontend initialized in `frontend/` using Vite's React/TypeScript
  template with ESLint.
- Verified frontend versions: React and React DOM 19.3.0,
  TypeScript 6.0.3, Vite 8.3.2 and ESLint 10.12.0.
- `npm install` completed successfully and reported no known
  vulnerabilities at installation time.
- `npm run build` and `npm run lint` completed successfully.
- `npm run dev -- --host 0.0.0.0` started the development server.
  The React starter page loaded through Codespaces on private port 5173.
- Frontend dependency declarations are in `frontend/package.json`;
  resolved dependency versions are recorded in `frontend/package-lock.json`.
- These checks verify the initial development setup.
  UC-001 functionality has not yet been implemented.

### Open decisions

- PostgreSQL is a possible later migration, not an initial dependency.
- Local AI model, semantic retrieval implementation, external research
  provider and deployment target remain undecided.
- Playwright is selected for the scoped browser journeys; component-test tooling
  remains deferred until needed by a later task.

### Development tooling

As approved by the owner on 2026-10-09, Codex in VS Code against this Codespaces
repository is primary for reasoning, planning, implementation and review, using
the owner's choice of direct ChatGPT subscription authentication. Do not inspect
credentials to verify it. ChatGPT Work is optional consultation; OpenCode/FHNW
LiteLLM is an optional comparison route and historical setup evidence.

Historical record: the pre-migration planning draft assigned planning/review to
ChatGPT Work, execution to OpenCode/FHNW LiteLLM and left the coding model
provisional. Those mandatory roles are superseded by
[ADR-001](adr/ADR-001-codex-repository-workflow.md). The owner-reported observed
UI setting on 2026-10-09 was GPT-6.1 Sol with Medium reasoning; it is not a
permanent model requirement or independently verified subscription entitlement.

Repository Markdown owns decisions, architecture, workflow, specifications and
evidence. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for lifecycle,
review and proposed course follow-ups. Development tools are separate from
runtime AI; the runtime privacy boundary remains unchanged.

### Secrets

No OpenAI or Gemini API key is required for UC-001 runtime.
Never commit credentials or secrets.
Any future secret requires a documented purpose and explicit owner approval.
