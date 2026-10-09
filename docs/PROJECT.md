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

UC-001 supports text requests, knowledge reuse before research, evidence-backed
comparison, explicit selection and persistence. Image-assisted input (UC-002)
may be considered only after UC-001 is validated. The canonical
[accepted scope](ARCHITECTURE.md#accepted-scope) defines the included capabilities,
optional-input constraints and exclusions; its
[privacy boundary](ARCHITECTURE.md#strict-runtime-privacy) remains binding.

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
UC-001 is not implemented.

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
| `frontend/src/` | Frontend source code, currently the starter application |
| `frontend/public/` | Static frontend assets |

The backend and test directories were created during BOOTSTRAP and
are initially empty. Git does not track empty directories; they will
be included as implementation and test files are added.

The recorded bootstrap checks cover the frontend starter build, ESLint and
browser startup. UC-001 functionality and automated application tests
have not yet been implemented; these checks were not rerun during migration.

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
| Start frontend development server | `npm --prefix frontend run dev -- --host 0.0.0.0` |

The frontend development server normally uses port 5173.
Open it through Codespaces port forwarding with visibility set to Private.
Stop the server with Ctrl+C.

Backend startup, unit tests and integration tests are not yet configured.
Frontend automated tests and end-to-end tests are not yet configured.
The frontend build creates `frontend/dist`; deployment is not yet configured.

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
- Frontend and end-to-end test tooling remain undecided.

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
