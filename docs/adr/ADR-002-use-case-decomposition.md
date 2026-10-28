# ADR-002 — Separate comparison and explicit selection

Date: 2026-10-09.
Decision status: approved by the owner on 2026-10-09.
Documentation status: recorded during SPECIFY; resulting edits await owner review.
Complete specifications, Errors, Acceptance and Tests are not approved by this decision.

## Context

The original UC-001 flow was approved on 2026-10-07; search-location requirements
were approved on 2026-10-09. A comparison is useful even without choosing;
explicit selection has its own trigger and saved outcome. Preserve both goals,
all approved behaviour and uncommitted location-amendment work.
The supplied rubric requires at least five entities and two use cases; document
count alone does not establish compliance.

## Alternatives

- Retain one end-to-end UC with incremental delivery.
- Separate comparison from explicit selection, retaining end-to-end increments
  (selected).

## Decision

| Original approved flow | Responsibility |
|---|---|
| Steps 1–7: submit, interpret, retrieve, assess, research if needed, compare, persist/present | [UC-001 — Find and compare alternatives](../specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md) |
| Steps 8–9: explicit selection, saving confirmation and evidence integrity | [UC-003 — Select a displayed alternative](../specs/UC-003-SELECT-DISPLAYED-ALTERNATIVE.md) |

Keep the historical UC-001 pathname; retain approval provenance in both specs.
Location input, applicability and conditional research remain in UC-001.
Retrieval precedes research; persistence precedes presentation/selection; no
selection is inferred; selection affects relevance without automatically changing
factual confidence or validation. All privacy/location restrictions remain intact.

Deliver two journey increments, each spanning UC-001 and UC-003:

1. Sufficient existing knowledge: comparison and explicit selection end-to-end.
2. Insufficient/empty knowledge: approved research and the same guarantees.

UC-002 remains optional image input, deferred until the full mandatory UC-001 +
UC-003 journey, including research, is validated. Permission-based “Use my location”
remains separately deferred and unauthorized for implementation.

## Consequences

UC-003 depends on a persisted displayed UC-001 comparison; no new navigation,
history, research or data-collection features follow from this split.
Keep one active UC and its phase/status in TASKS; track journey increment and
full-scope completion separately. Each affected UC follows AI-SDLC with skills,
TDD in DEVELOP, evidence-based validation and human transition/delivery gates.
Increment 1 completion does not complete research or full mandatory scope.

Availability-based selection eligibility, currency/fallback/validation/ranking
policies and selection-versus-realized-savings clarification remain unresolved.
The five conceptual entities in [ARCHITECTURE.md](../ARCHITECTURE.md#retrieval-persistence-and-evidence)
retain distinct responsibilities; implementation, relationships and assessed
outcomes must establish rubric compliance, not labels or entity/document counts.
ADR-001 remains the historical tooling decision and is not superseded.
