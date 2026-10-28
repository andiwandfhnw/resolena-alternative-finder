# FHNW capstone source snapshot — 2026-10-28

Resolena Alternative Finder explores practical alternatives to purchases and habits,
with transparent cost/resource comparisons and retained evidence. This submission
captures the current development source, including unfinished work. **PHASE: 3 /
STATUS: in-progress.** It is not application completion, production readiness or
deployment. Start with the synthetic demo below; Windows acquisition/build tooling
is unnecessary for inspection or demonstration.

## Scope and implementation status

- Implemented: bounded UC-001 request/comparison/coverage flows; qualification and
  source-bound rendering contracts; React forms and outcome display; atomic
  SQLite request/options/evidence snapshots before presentation; explicit retry,
  ownership/payload-bound recovery and fresh-search handling. Tests exercise
  language/locality clarification, error and persistence boundaries with substitutes.
- Development reference releases: GeoNames country choices and exact CH/LI
  swisstopo locality/postcode associations. Matching does not prove provider coverage.
  Outside CH/LI, honest unverified/country-only continuation is available;
  worldwide locality matching remains deferred. See [ADR-005](adr/ADR-005-country-reference-development-release.md),
  [ADR-006](adr/ADR-006-locality-association-development-release.md) and the scoped
  Priority 5 decision and evidence limits in [ADR-007](adr/ADR-007-increment-1-locality-matching-scope.md).
- Partial: Priority 3 real multilingual interpretation/model integration and
  Priority 4 reviewed real knowledge/freshness and DE/FR/IT/EN renderings.
  Local interpreter adapters and offline assessment tooling exist; no successful
  Granite inference or model suitability is established. Real content drafts stay
  inactive; the normal API has no configured real adapters.
- Pending: Priority 6 integrated/qualified review, formal Phase 4 validation,
  production hosting/deployment and full mandatory research. [UC-003 selection](specs/UC-003-SELECT-DISPLAYED-ALTERNATIVE.md)
  is unimplemented; optional image input is deferred. UC-001 increment 1 and the
  complete user journey remain unfinished.

Requirements and history: [UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md),
[product context](PRODUCT_CONTEXT.md), [task ledger](TASKS.md),
[architecture](ARCHITECTURE.md), [ADRs](adr/) and [AGENTS.md](../AGENTS.md).

## Architecture and source map

Clean Architecture dependencies point inward: infrastructure/interfaces →
application → domain. FastAPI exposes the application boundary; SQLAlchemy/SQLite
implements persistence; React/TypeScript uses the API through Vite's local proxy.

| Path | Contents |
|---|---|
| `src/app/domain/` | Meaning, comparison and evidence rules |
| `src/app/application/` | Use-case orchestration, qualification/rendering and ports |
| `src/app/interfaces/` | FastAPI request/response handling |
| `src/app/infrastructure/` | SQLite/reference/interpreter adapters |
| `src/app/main.py` | Normal unconfigured composition |
| `frontend/` | React UI, TypeScript, Vite, ESLint and locked npm dependencies |
| `tests/unit/`, `tests/integration/`, `tests/e2e/` | Rule, adapter/API/SQLite and real-browser tests |
| `tests/support/` | Explicit synthetic interpreter/evidence/demo composition |
| `docs/reference/`, `docs/knowledge/` | Attributed reference releases and inactive knowledge/rendering drafts |
| `scripts/`, `experiments/` | Setup, offline assessment tooling and retained experimental history |
| `build/uc001-*/` (selected files) | Historical verification receipts and required test/package/reference fixtures |
| `skills/`, `.devcontainer/`, `.github/`, `environments/` | AI-SDLC workflow and existing development configuration |

## Setup and test commands (Codespaces/Linux Bash)

These commands were **checked against current source/configuration**, not executed
for this submission. Use Python 3.12 (historical environment 3.12.11), Node 24 and
npm; the [devcontainer](../.devcontainer/devcontainer.json) declares that baseline.
Python direct requirements are pinned, but transitive dependencies have no complete
lockfile; a fresh environment is not certified by this snapshot. npm has a lockfile.
From the repository root:

```bash
bash scripts/setup-python.sh
.venv/bin/python -m pip check
npm --prefix frontend ci
.venv/bin/python -m pytest
npm --prefix frontend run lint
npm --prefix frontend run build
PLAYWRIGHT_BROWSERS_PATH="$PWD/build/playwright" ./frontend/node_modules/.bin/playwright install chromium --only-shell
npm --prefix frontend run test:e2e
```

Browser tests start their own synthetic API/frontend on ports 8011/5175, use new
SQLite files under `build/test-only/`, one worker and zero retries. Chromium native
library prerequisites are listed in [PROJECT.md](PROJECT.md#browser-test-setup).
PowerShell-specific historical harness tests have separate platform prerequisites;
this is not a promise that every experimental test runs on a fresh Linux machine.
No Windows harness is required for the synthetic browser application.

## Synthetic full-stack demonstration

Run these in two repository-root Bash terminals after setup:

```bash
# Terminal 1
PYTHONPATH=src:. .venv/bin/python -m tests.support.demo --db build/test-only/capstone-demo.sqlite3
```

```bash
# Terminal 2
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open privately forwarded port 5173. Enter exactly `Repair my bicycle without
replacing it` with country `CH` to compare two synthetic providers. The same text
with `DE` demonstrates a saved insufficient-coverage outcome. The exact fixture
`Synthetic hourly bicycle repair` exercises synthetic source-bound rendering in
DE/FR/IT/EN; `Synthetic pending bicycle repair` demonstrates a review limitation.
Stop both owned servers with Ctrl+C. Demo databases remain local and ignored.

This is real React → API → SQLite wiring with exact-match test interpretation,
prepared evidence, artificial clock/review records and synthetic providers. It
has no real model inference, external research or UC-003 selection. Reference
catalogues are real development releases; they do not make fixture providers or
linguistic review real. `app.main` deliberately returns `configuration_unavailable`
without real adapter configuration. See [full demo limitations](PROJECT.md#test-only-local-demonstration--codespaces-bash).

## Verification evidence and provenance

Existing receipts record development checks at their original dates and source
states; they are not a fresh combined regression of this submission. Do not sum
these overlapping counts or reruns.

| Retained evidence | What it establishes and limits |
|---|---|
| [Priority 1](../build/uc001-slice1/verification.json), [Priority 2](../build/uc001-priority2/verification.json) | Initial saved-comparison and qualification/coverage development checks with synthetic substitutes. |
| [Rendering, 2026-10-19](../build/uc001-priority4-rendering/verification.json) | Recorded 150 backend checks (including 37 new rendering checks), 13 browser checks, lint/build; synthetic review is not qualified linguistic acceptance. |
| [Recovery 5A](../build/uc001-priority5a-recovery/verification.json), [fresh search 5B](../build/uc001-priority5b-fresh-search/verification.json), [collision 5C](../build/uc001-priority5c-concurrency/verification.json) | Focused saved-response loss, explicit action and one controlled real SQLite collision; no exhaustive timing/stress claim. |
| [5X evidence map](TASKS.md#priority-5x--current-exit-readiness-checkpoint-2026-10-23) | Eight obligation groups link later focused receipts; mocked UI/bounded observations retain their limits. See ADR-007 for the acceptance boundary. |
| [Granite v3 preparation](../build/uc001-granite-native-handoff-v3/verification.json) | Seven focused Codex Codespaces passes for package/entry wiring; static advisor review only. No Windows execution or successful Granite inference. Historical operational instructions are not submission run instructions. |

Owner-provided Windows observations are identified as such in the task ledger and
receipts; Codex did not perform those desktop runs. The [advisor attribution erratum](TASKS.md#priority-3--attribution-erratum-one-handoff-v2-windows-preflight-authorized-2026-10-27)
retracts independent-test claims: no retracted advisor probes are credited here.
Original failed experiments, consumed allowances and frozen receipts are preserved.

Submission checks are source/configuration inspection, exact path selection,
sensitive-content review, documentation links, staged-diff review, workflow-trigger
inspection, followed by Git commit/tag/remote identity verification. Preparation
checked 42 local entry-point links/anchors and existing literal test-fixture paths;
required ZIP fixtures passed CRC/member inspection. Pattern matches were synthetic
test literals or approval prose; no material disclosure issue was identified. The
staged whitespace check reports preserved historical whitespace/CRLF findings in
evidence, reference fixtures and harness source, plus the existing TASKS warning;
it is not a clean whitespace pass. Frozen bytes are retained. No application tests,
browser run, services, Windows commands, acquisition, compilation, GPU probe,
preflight, closed diagnostics or inference are executed for this submission.

## AI-assisted workflow reflection

Codex in VS Code/Codespaces is the primary development assistant; repository
Markdown records decisions, requirements, architecture, TDD evidence and scoped
human acceptance. [ADR-001](adr/ADR-001-codex-repository-workflow.md) explains the
choice over the earlier OpenCode/FHNW LiteLLM workflow; ChatGPT Work is optional
consultation. Phase skills and [workflow](DEVELOPMENT_WORKFLOW.md) keep approvals
and technical checks explicit. Development assistants are separate from runtime
AI and its Resolena-controlled privacy boundary.

The work demonstrates the value of small vertical slices, tests before fixes and
reviewable receipts. Model/tool selection remains an empirical constraint:
offline mocks and contract checks can establish wiring, while failed local-model
experiments and the advisor-test retraction show why execution provenance and
qualified semantic review must remain separate. This snapshot exposes those limits
instead of treating generated code or accumulated test counts as completion.

## Snapshot contents and exclusions

The snapshot includes current application/frontend source, tests, fixtures,
dependency manifests/lockfile, existing development configuration, AI-SDLC guidance,
ADRs/specifications and selected unchanged verification evidence. Required ignored
reference sources and source-only package fixtures are explicitly included despite
`build/` being ignored. GeoNames data are attributed under CC BY 4.0 in their
manifests; swisstopo attribution and redistribution terms remain with its manifests
and pinned source documentation. The retained GitHub CLI source fixture is covered
by its [MIT notice](reference/GITHUB-CLI-v2.81.0-LICENSE.txt), copied from the
[pinned upstream license](https://github.com/cli/cli/blob/v2.81.0/LICENSE).
No model weights or SDK/runtime redistribution.

Excluded: credentials/real environment secrets, private tool state, generated
databases, environments, node_modules, caches, browser/runtime binaries, SDK
installers, unnecessary build output, machine/transport raw records and redundant
historical archives. Small source-only archives required by package tests and the
pinned swisstopo reference ZIP are evidence fixtures, not compiled runtimes.
Excluded artifacts remain local; frozen originals are not silently sanitized.
Some historical links/hash inventories refer to excluded archives, machine state
or owner-retained files: those are unavailable evidence, not reproducible execution
proof. This snapshot does not certify every historical artifact inventory complete.

The submission branch/tag identify the exact source tree; publication changes no
repository visibility or access grants. Lecturer access has not been verified.
