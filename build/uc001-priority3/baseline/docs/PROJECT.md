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
Normal composition remains unconfigured; no real-world knowledge coverage,
language validation, research, held-out access, model execution, CI or delivery
is claimed. Phase 3 stays in-progress; stop after Priority 2.

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
