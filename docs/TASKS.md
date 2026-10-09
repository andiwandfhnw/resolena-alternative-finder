PHASE: 1
STATUS: in-progress

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

UC-001 — Find and select an alternative from a text request.

Specification: `docs/specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md`.
The specification is an incomplete draft. Intent, Actors and Preconditions
were approved by the owner on 2026-10-07. Flow was approved by the owner
on 2026-10-07, including persistence before selection. Errors, Acceptance
and Tests are pending definition and owner review.

The owner selected SPECIFY on 2026-10-07.

Specification execution is in progress.

## Documentation migration — 2026-10-09

Separate owner-authorized maintenance; UC-001 remains PHASE: 1 / STATUS:
in-progress. This task does not complete SPECIFY or authorize UC-001 code/tests.

- Decision approved: Codex in VS Code in Codespaces is primary; repository
  Markdown is maintained as the source of truth. See [ADR-001](adr/ADR-001-codex-repository-workflow.md).
- Scope: create canonical architecture/workflow documentation and the ADR;
  reconcile PROJECT.md, AGENTS.md and README.md while preserving previous work.
- Acceptance: preserve product/privacy decisions, bootstrap acceptance and
  October 7 UC approvals; distinguish historical evidence and follow-up proposals.
- Checks: review full documents/diffs, relative links, stale active guidance,
  tracked whitespace, new documents and unchanged UC-001 content.
- Documentation implemented on 2026-10-09. Full changed/new Markdown and tracked
  diffs reviewed; stale-role search found only optional or historical references.
  All 48 relative links/anchors across 17 maintained Markdown documents passed.
  Tracked `git diff --check` and separate new-document whitespace checks passed.
  UC-001 SHA-256 matches the pre-task fingerprint; phase/status and approvals
  are preserved. Branch/HEAD are unchanged and nothing is staged.
- Inspected unchanged: UC-001, UC-TEMPLATE.md, frontend/README.md,
  .github/copilot-instructions.md and all six canonical phase skills. The
  templates/pointer and linked phase procedures require no workflow rewrite.
- Verification is assistant self-review, not independent validation. No
  application, CI, MCP, Docker or deployment checks were run; documentation-only
  scope requires content/link checks rather than code tests. No credentials read.
- Migration review: initially pending; accepted by the owner on 2026-10-09,
  including AGENTS.md routing, the repository architecture/workflow documents,
  ADR-001 and the DESIGN skill correction. The correction routes architecture
  to ARCHITECTURE.md and shortens duplicated PROJECT.md scope without changing
  constraints; affected links, whitespace and preservation checks passed.
- Owner authorized a documentation checkpoint on the current branch, including
  UC-001 as an explicitly incomplete draft. This acceptance does not complete
  Phase 1, approve unresolved UC-001 behaviour or authorize CI/CD/MCP proposals.

## Proposed course follow-up work

These proposals authorize no installation, configuration or implementation.
Details and phase placement: [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#proposed-follow-up-work).

- Application CI: frontend lint/build and meaningful automated tests.
- Reviewed PRs and verification of bootstrap integration into main; merge
  status has not been established.
- One useful development MCP pilot, initially Context7, with permissions and
  a synthetic comparison with/without the tool.
- Reproducible Docker release and human-authorized deployment.
- Hosting, persistent storage and recovery decisions during DESIGN.

## Bootstrap progress

- [x] Create the repository and bootstrap branch.
- [x] Configure Codespaces with Python 3.12 and Node.js 24.
- [x] Record the accepted scope, architecture and privacy boundaries.
- [x] Create the initial backend and test directories.
- [x] Initialize the React/TypeScript frontend with Vite and ESLint.
- [x] Verify frontend build, lint and browser startup.
- [x] Install backend dependencies, including SQLAlchemy.
- [x] Pin direct backend dependency versions and check compatibility.
- [x] Document setup commands and verification evidence.
- [x] Commit and push the initial bootstrap checkpoint.
- [x] Complete the final bootstrap review and resolve any findings.
- [x] Record owner acceptance and close BOOTSTRAP.

## Backlog

- UC-001: specify text input, knowledge reuse, research when needed,
  evidence-backed alternatives, selection and persistence.
- UC-001 pending SPECIFY clarification, proposed on 2026-10-09: comparison
  estimates and explicit selection must not be presented as proof of realized
  savings, completed behaviour or achieved environmental impact. Resolve with
  the owner before changing approved behaviour/acceptance; no Saver entities,
  logging features or integration contracts are authorized. Context:
  [PRODUCT_CONTEXT.md](PRODUCT_CONTEXT.md#pending-specify-clarification).
- UC-002: consider image-assisted input only after UC-001 is validated.

## Product-context documentation — 2026-10-09

Owner-authorized documentation only: add concise product context and discovery
links; preserve approved scope/privacy, UC-001, phase/status and existing work.
Acceptance/checks: 400–600 words, correct glossary/provenance, working local
links, consistent boundaries, tracked/new-document whitespace and unchanged UC.
Review: initially pending; accepted by the owner on 2026-10-09, including
PRODUCT_CONTEXT.md and the concise AGENTS.md routing addition.
The selection/realized-savings proposal remains pending SPECIFY, not approved
feature behaviour. Verification: product context is 561 whitespace-delimited
words; all 58 local links/anchors across eight integrated documents passed.
Content, terminology and tracked diffs reviewed; no scope/privacy conflicts
found. Tracked and new-document whitespace checks passed. UC-001, architecture,
workflow and ADR fingerprints, phase/status, approval history and branch/HEAD
are unchanged. No application checks run; nothing staged or committed.

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artifact.
- Follow the baseline in [PROJECT.md](PROJECT.md), the scope/privacy boundaries
  in [ARCHITECTURE.md](ARCHITECTURE.md) and [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md).
- Keep detailed acceptance criteria and design decisions in SPECIFY/DESIGN.
- Guide the project owner one step at a time; obtain required confirmation
  for unresolved decisions and phase transitions. Continue already-authorized
  work within its scope.

## Evidence

- Baseline, versions and historical setup checks: [PROJECT.md](PROJECT.md).
- Canonical scope and architecture: [ARCHITECTURE.md](ARCHITECTURE.md).
- Bootstrap work branch: setup/phase-0-bootstrap.
- Initial bootstrap checkpoint committed and pushed on 2026-10-04.
- Final bootstrap review completed on 2026-10-05.
- Project owner explicitly accepted BOOTSTRAP as complete on 2026-10-05.
- Acceptance covers project initialization and the documented baseline.
- Project owner selected SPECIFY for UC-001 on 2026-10-07.
- UC-001 functionality, database connectivity, automated application
  tests and deployment remain pending.
