# ADR-001 — Codex and repository-based development workflow

Date: 2026-10-09.
Decision status: approved by the owner in the documentation-migration request.
Implementation status: documentation migration accepted by the owner on
2026-10-09; verification evidence and review history are recorded separately
in [TASKS.md](../TASKS.md).

## Context

The pre-migration working-tree PROJECT.md assigned requirements/architecture/review
to ChatGPT Work and primary repository execution to OpenCode in Codespaces through
FHNW LiteLLM. The owner approved consolidating reasoning and execution in Codex
while keeping repository Markdown authoritative. Existing uncommitted planning
work and approved product/privacy decisions must be preserved.

## Alternatives

- Retain the prior ChatGPT Work planning/review handoff and OpenCode/LiteLLM execution.
- Use Codex in VS Code as primary while keeping those tools optional (selected).

## Decision

Use Codex in VS Code against this repository in GitHub Codespaces for reasoning,
planning, implementation and review. The owner chose direct ChatGPT subscription
authentication instead of FHNW LiteLLM for the primary workflow. Never inspect
credentials or authentication caches to verify this choice.

The owner-reported observed UI model was GPT-6.1 Sol with Medium reasoning. Record
it as an observed session setting, not a permanent requirement or independently
verified subscription entitlement. Model choice remains adaptable within the
approved workflow; runtime AI model choice remains a separate, pending decision.

ChatGPT Work is optional consultation. OpenCode/FHNW LiteLLM remains historical
setup evidence and an optional comparison route. This supersedes their mandatory
planning/review handoff and primary execution roles; it preserves their history.

Maintain project decisions, architecture, workflow, specifications and development
evidence in repository Markdown. Apply SPECIFY → DESIGN → DEVELOP → VALIDATE →
DEPLOY to each feature/UC with canonical skills and existing approval rules.
Use the explicitly selected phase, TDD in DEVELOP, actual evidence in review
and authorized Git/delivery actions. Tool modes do not select lifecycle phases.

## Rationale and consequences

One repository-based primary assistant reduces mandatory tool handoffs; reviewed
Markdown makes decisions and evidence available to later sessions. Architecture,
workflow and decision history have distinct canonical owners with links rather
than repeated logs. Self-review remains limited and does not replace independent
validation or required human acceptance.

This is a development-tooling decision, not a runtime dependency or permission
to send collected application data to external LLMs. The strict privacy boundary
is unchanged. MCP, CI/CD, hosting and release improvements remain proposals
requiring their own decisions, permissions and verification.

BOOTSTRAP remains accepted as complete. UC-001 remains PHASE: 1 / STATUS:
in-progress with October 7 approvals intact; this migration neither completes
SPECIFY nor authorizes application implementation. Decision approval does not
equal verification or owner acceptance of the resulting documentation.

## Related artifacts

- [Architecture](../ARCHITECTURE.md)
- [Development workflow](../DEVELOPMENT_WORKFLOW.md)
- [Project baseline and historical evidence](../PROJECT.md)
- [Durable instructions](../../AGENTS.md)
