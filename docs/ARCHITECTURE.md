# Architecture

This document owns the accepted scope and architecture boundaries. The
[project baseline](PROJECT.md) owns setup commands and historical evidence;
[UC-001](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md) owns its detailed behaviour
and acceptance. Accepted architecture describes intended behaviour, not
implemented capabilities.

## Accepted scope

Resolena Alternative Finder is a standalone FHNW capstone module, with future
integration into Resolena's website or mobile app. It helps users compare
practical alternatives to purchases and habits using financial savings and
environmental/resource information, transparently and without judgment.

UC-001 accepts natural-language text, normalizes/categorizes it, reuses supported
knowledge before researching, presents a small evidence-backed comparison,
allows explicit selection and persists requests, shown results, evidence and
selections. Basic loading, validation and error states are in scope; their
details remain pending SPECIFY. Existing knowledge may initially be empty.

UC-002 image-assisted input may be considered only after UC-001 is validated.
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
- Application: coordinates UC-001 and defines ports for persistence, retrieval,
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

No OpenAI or Gemini API key is required for UC-001 runtime. Development
authentication does not grant permission to transmit collected application data.

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

BOOTSTRAP was accepted as complete on 2026-10-05. Its recorded checks cover the
dependency setup and React starter build, lint and browser startup. Backend/test
directories were initially empty; UC-001 functionality, database connectivity and
automated application tests remain pending. See [PROJECT.md](PROJECT.md#historical-setup-evidence)
for the recorded versions and checks; they were not rerun in this migration.
Bootstrap integration into main, application CI, MCP and deployment have not
been verified by this documentation task.

## Pending decisions and proposed improvements

Errors, Acceptance and Tests remain pending in UC-001. Retrieval thresholds,
ranking formula, semantic retrieval, research provider, local runtime AI model,
evidence schema, frontend/E2E test tooling and deployment target remain open.
Hosting, persistent storage and recovery need DESIGN decisions before delivery.

Maintain a synthetic evaluation set as behaviour is specified; evaluate meaningful
changes to interpretation, retrieval, ranking, research decisions and optional AI.
Record material experiments. Promote significant behaviour changes only after
testing and human approval, retaining the previous validated version through Git.
These are required improvement practices, not claims that evaluation exists.

Course follow-up proposals, including application CI, a Context7 development MCP
pilot and reproducible Docker delivery, are tracked in
[DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md#proposed-follow-up-work) and
[TASKS.md](TASKS.md). They authorize no installation or implementation.
