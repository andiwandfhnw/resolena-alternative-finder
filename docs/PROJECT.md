# PROJECT.md

Complete this document during **BOOTSTRAP**. Keep it concise and specific to
the project created from this template.

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

### Mandatory scope: UC-001

- Accept a natural-language text request.
- Normalize and categorize the request.
- Retrieve existing Resolena knowledge before initiating new research.
- Assess whether stored knowledge is relevant, sufficiently supported
  and fresh enough to reuse.
- Obtain and persist new structured results when knowledge is
  insufficient, through a research adapter reviewed during SPECIFY/DESIGN.
- Present a small set of alternatives with financial and environmental
  or resource information, evidence references and confidence/validation
  labels.
- Allow the user to select a preferred alternative.
- Persist the request, shown alternatives, evidence and selection.
- Provide basic loading, input-validation and error states.

User selections may influence relevance, but must never automatically
increase factual confidence or change validation status.

Collected application data must not be sent to external LLM providers.
Development agents use synthetic or deliberately non-sensitive examples.

### Optional scope: UC-002

Image-assisted request creation may be considered only after UC-001
is validated. Extracted information requires user confirmation.
Raw images are not retained by default.

### Out of scope

- User accounts, login and personalized account history.
- Banking, payments, savings transfers and investment integration.
- The complete Saver and dual piggy-bank ecosystem.
- Community features, rewards and Resolena Coin.
- Automatic model training or reinforcement learning from selections.
- Autonomous rewriting or deployment of prompts, ranking rules or code.
- Complex analytics dashboards and production-scale web crawling.

### Specification boundary

Acceptance criteria, retrieval thresholds, ranking rules and detailed
adapter behaviour are defined during SPECIFY/DESIGN.
This section records scope; it does not claim these features exist.

## Architecture

### Architecture style

Use Clean Architecture with ports and adapters.
Source-code dependencies point inward toward the application and domain.

- Domain: business concepts and rules, independent of FastAPI,
  SQLAlchemy, external services and AI frameworks.
- Application: coordinates UC-001 and defines interfaces (ports) for
  persistence, retrieval, interpretation, research and explanations.
- Interfaces: FastAPI routes and request/response handling translate
  web requests into application calls.
- Infrastructure: implements database, research and optional AI adapters.
- Frontend: React/TypeScript communicates with the backend through
  an API; it does not access the database directly.

Concrete adapters are connected to the application at startup.
Business logic must not depend on a particular database or AI provider.

### UC-001 workflow

Interpret -> retrieve -> assess sufficiency -> research only if needed
-> compare and explain -> persist results -> record user selection.

Future requests reuse stored knowledge where appropriate.
The application controls this sequence and permission to research.
Optional AI components assist bounded tasks; they do not control
the workflow autonomously.

### Data and evidence

Separate these concepts:

- SearchRequest: original and normalized request and its context.
- Alternative: reusable alternative information.
- RequestAlternative: which alternatives were shown for a request.
- Evidence: sources and metadata supporting factual claims.
- Selection: the user's explicitly selected alternative.

These are conceptual entities; detailed schemas are defined in DESIGN.

Material factual claims must be traceable to supporting evidence.
Preserve source/reference, relevant dates and confidence/validation
metadata. Selection frequency measures relevance, not factual validity.

### Privacy boundary

- Keep collected application data in Resolena-controlled persistence.
- Do not send original or normalized requests, stored alternatives,
  evidence records, selections, identifiers or images to external
  LLM providers, including for embeddings, classification or ranking.
- Development and review agents use synthetic or deliberately
  non-sensitive examples; never production/user data.
- External search/research requires minimized, non-identifying queries
  and explicit review during SPECIFY/DESIGN before implementation.
- Use anonymous request identifiers; no user account is required.
- Free-text input may still contain personal information. Anonymous
  identifiers alone do not make its contents anonymous.
- Any relaxation of the privacy boundary requires explicit owner
  approval and an updated specification before implementation.

### Controlled improvement

Maintain a synthetic UC-001 evaluation set as behaviour is specified.
Evaluate meaningful changes to interpretation, retrieval, ranking,
research decisions and optional AI against it.

Record material experiments and their results.
Promote significant behaviour changes only after testing and human
approval, with the previous validated version recoverable through Git.

### Remaining design decisions

Retrieval thresholds, ranking formula, semantic retrieval, research
provider, local AI model and detailed evidence schema remain open.
The current architecture describes intended boundaries, not
implemented functionality.

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

The frontend starter application builds, passes ESLint and loads in
the browser. UC-001 functionality and automated application tests
have not yet been implemented.

### Project guidance and setup

- `AGENTS.md`: shared agent instructions and lifecycle routing.
- `docs/PROJECT.md`: project scope, architecture and development setup.
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

Accepted by the project owner on 2026-10-04 during BOOTSTRAP:

| Component | Selected technology |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python 3.12 + FastAPI |
| Initial database | SQLite |
| Database access / ORM | SQLAlchemy |
| Backend testing | pytest + httpx |
| Development environment | GitHub Codespaces with a devcontainer |

Rationale: reuse the course template's Python foundation, support a
full-stack web application, and keep business logic independent of
frameworks and database implementations.

### Current setup evidence

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

### Secrets

No OpenAI or Gemini API key is required for UC-001 runtime.
Never commit credentials or secrets.
Any future secret requires a documented purpose and explicit owner approval.