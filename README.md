# Resolena Alternative Finder

[![AI-SDLC](https://img.shields.io/badge/AI--SDLC-v1.0.0-blue)](https://ai-sdlc.aisl.science)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22833065.svg)](https://doi.org/10.5281/zenodo.22833065)
[![arXiv](https://img.shields.io/badge/arXiv-2609.24348-b31b1b.svg)](https://doi.org/10.48550/arXiv.2609.24348)

Standalone FHNW AI-assisted Software Development Capstone module for exploring
practical alternatives to purchases and habits. This repository was initialized
from the AI-SDLC project template; BOOTSTRAP was accepted on 2026-10-05.

The current source snapshot implements a bounded UC-001 comparison flow with a
React frontend, FastAPI backend and atomic SQLite persistence. The synthetic
full-stack demo uses prepared test substitutes; real model integration and the
complete application remain unfinished. **PHASE: 3 / STATUS: in-progress.**

For the FHNW submission, start with [SUBMISSION_STATUS.md](docs/SUBMISSION_STATUS.md):
setup, synthetic-demo commands, source map, evidence provenance and limitations.
No Windows acquisition/build harness is needed to inspect or demonstrate it.
The method is documented in [AISL Docs](https://docs.aisl.science/learning-and-resources/ai-sdlc).

For Resolena's users, product principles and comparison guidance, see
[PRODUCT_CONTEXT.md](docs/PRODUCT_CONTEXT.md); approved specifications govern behaviour.

## Work on this project

Codex in VS Code against this repository in GitHub Codespaces is the primary
assistant for reasoning, planning, implementation and review. Repository
Markdown is the maintained source of truth. ChatGPT Work is optional consultation;
OpenCode/FHNW LiteLLM is an optional comparison route and historical setup evidence.
See the owner-approved [tooling decision](docs/adr/ADR-001-codex-repository-workflow.md).

Read [AGENTS.md](AGENTS.md), then [TASKS.md](docs/TASKS.md),
[PROJECT.md](docs/PROJECT.md) and the active specification in that order. Follow
the linked [architecture](docs/ARCHITECTURE.md),
[development workflow](docs/DEVELOPMENT_WORKFLOW.md) and selected phase skill.
Every feature/UC follows SPECIFY → DESIGN → DEVELOP → VALIDATE → DEPLOY with
existing approval rules; do not repeat bootstrap for each UC. Tool modes do not
select phases. DEVELOP uses TDD; review actual diffs and evidence before required
human acceptance. Release/deployment require authorization.

GitHub Copilot instructions are provided in `.github/copilot-instructions.md`.
The included GitHub Actions files are template baselines for AI-SDLC structure
checks and a technology-neutral source release. Their presence does not prove
successful CI, application readiness or bootstrap integration into main.
Application CI, tests and reproducible release remain
[proposed follow-up work](docs/DEVELOPMENT_WORKFLOW.md#proposed-follow-up-work).
`.github/workflows/cd.yml` is included as an inactive template and must be
configured during DEPLOY, after the deployment platform, required secrets and
post-deploy checks have been decided.

## Agent setup

The existing devcontainer configuration provisions Python, Pylance, debugging
and GitHub Copilot extensions and prepares `.agents/skills` and the Python
environment. It does not install/configure Codex through the skill setup script.
The current primary workflow is recorded above; no devcontainer changes are
part of this migration. The default terminal locale is English;
the VS Code UI uses its own user display-language setting.

Run `bash scripts/setup-skills.sh` from the repository root when another agent
is used. Run `bash scripts/setup-python.sh` again when the Python environment
needs to be recreated or refreshed.
Choose `copilot`, `codex`, `claude`, `cline`, `opencode`, `cursor`, `kiro`,
`junie`, `devin` or `all`. The script links to the canonical `skills/` directory and
falls back to copying if links are unavailable. Existing destinations are kept;
copies must be refreshed manually after skill changes. Verify discovery in your
agent; setup does not install or configure the agent itself.

For non-interactive skill discovery setup, use `bash scripts/setup-skills.sh codex`.
The existing `.agents/skills` link already points to canonical `skills/`; do not
create duplicate Codex instruction files or edit linked copies. The `claude` and
`all` selections create a missing `CLAUDE.md` containing `@AGENTS.md`; an existing
file is preserved. Setup is documented here, not executed by this migration.

## Repository artefacts

- `AGENTS.md` — lifecycle router and guardrails
- `docs/PROJECT.md` — project baseline, commands and historical setup evidence
- `docs/ARCHITECTURE.md` — accepted scope, architecture and privacy boundaries
- `docs/DEVELOPMENT_WORKFLOW.md` — development/review workflow and proposals
- `docs/adr/` — owner-approved decisions and rationale
- `docs/TASKS.md` — current lifecycle state
- `docs/specs/` — executable use-case specifications
- `skills/ai-sdlc-*` — phase-specific execution guidance
- `.devcontainer/` — Codespaces and VS Code baseline
- `environments/python/` — Python environment profile, including the source
  VS Code debug configuration
- `scripts/setup-python.sh` — Python environment and dependency setup
- `.github/` — Copilot instructions, CI, release and CD workflow templates
