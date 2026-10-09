# Resolena product context

## Purpose and users

Resolena helps people turn everyday better choices into visible financial and
environmental/resource value. Its initial market is Switzerland, including
students, young professionals and people with constrained budgets who want
practical improvements. This background does not automatically add currency,
language, localization or mobile-platform requirements to the capstone.

Alternative Finder supports discovering and comparing possibilities that could
inform future actions in the wider product.

## Product principles and comparison guidance

Support practical improvement without guilt, shame, moral superiority, political
positioning or pressure to consume. Respect the user's desired outcome, budget
and stated constraints. Do not assume one universally best option; useful choices
depend on context and on which trade-offs the user is willing to make.

Alternatives can concern products, services, purchases, habits or behaviours.
Where relevant, possibilities include buying secondhand, repair, reuse,
substitution or avoiding an unnecessary purchase. These are illustrations, not
requirements to implement every category or return every option type. Local,
secondhand or another category is not automatically cheaper or environmentally
better; factual comparisons need evidence.

An alternative may improve finances, environmental/resource implications or
both. Some useful alternatives cost more. Explain trade-offs plainly and preserve
unknowns and assumptions. Comparable amounts need clear baselines, units and
time periods so users can understand what is being compared. These principles
guide specification work; unresolved behaviour must be proposed through SPECIFY
rather than silently implemented in UX, ranking or comparison logic.

## Small glossary

| Term | Product meaning |
|---|---|
| Alternative | A practical possibility with reusable information for comparison; it is not automatically an executed Saver. |
| Saver | The wider platform's term for a relevant decision/action, associated with its envisioned financial and environmental piggy banks. No Saver entity or integration is defined here. |
| Evidence | Sources and metadata supporting factual claims, including relevant dates and confidence/validation information. |
| Selection | The user's explicit choice of a displayed alternative against a request. It can signal relevance, without automatically increasing factual confidence or changing validation status. |

## Pending SPECIFY clarification

Proposed for owner resolution in UC-001: comparison estimates and an explicit
selection must not be presented as proof of realized savings, completed behaviour
or achieved environmental impact. This clarification is recorded in
[TASKS.md](TASKS.md#backlog), not added to the approved specification by this task.
It introduces no Saver entities, logging features or integration contracts.

## Module boundary and authority

The approved capstone scope and [strict runtime privacy](ARCHITECTURE.md#strict-runtime-privacy)
govern this module. Broader plans for optional external AI do not relax them.
Development AI is separate from application runtime AI. Accounts, piggy banks,
banking/transfers, investment routing, rewards, community and the wider startup
roadmap are background and outside this module unless separately approved through
AI-SDLC. Roadmap ideas are not implementation requirements.

This file supplies product context; approved sections of the active
[UC-001 specification](specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md) control feature
behaviour and acceptance. Its unfinished sections remain pending. Surface
conflicts for owner resolution rather than silently reconciling them. New
features and behaviour changes follow [AI-SDLC instructions](../AGENTS.md).
Technical boundaries belong in [ARCHITECTURE.md](ARCHITECTURE.md), project setup
in [PROJECT.md](PROJECT.md), and phase procedures in the
[development workflow](DEVELOPMENT_WORKFLOW.md) and linked skills.

## Provenance and status

Added on 2026-10-09 from owner-supplied context described as distilled from
`Master_Context_Prompt_Resolena_Updated_2026-09-23.docx`. The DOCX itself was not
available for this task and has not been read. Documentation was accepted by
the owner on 2026-10-09. The proposed clarification remains pending owner
resolution; documentation acceptance does not advance Phase 1/in-progress.
