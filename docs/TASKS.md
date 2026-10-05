PHASE: 0
STATUS: done

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

No active implementation use case during BOOTSTRAP.

BOOTSTRAP is complete.
Next: UC-001 — Find and select an alternative from a text request.
Its specification will be created during SPECIFY.
Phase 1 has not started yet.

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
- UC-002: consider image-assisted input only after UC-001 is validated.

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artifact.
- Follow the scope and privacy boundaries in docs/PROJECT.md.
- Keep detailed acceptance criteria and design decisions in SPECIFY/DESIGN.
- Guide the project owner one step at a time and wait for confirmation
  before proceeding to the next step.

## Evidence

- Scope, architecture, versions and setup checks: docs/PROJECT.md.
- Bootstrap work branch: setup/phase-0-bootstrap.
- Initial bootstrap checkpoint committed and pushed on 2026-10-04.
- Final bootstrap review completed on 2026-10-05.
- Project owner explicitly accepted BOOTSTRAP as complete on 2026-10-05.
- Acceptance covers project initialization and the documented baseline.
- UC-001 functionality, database connectivity, automated application
  tests and deployment remain pending.