# ADR-007 — Increment-1 locality-matching scope

Status: owner-approved, 2026-10-23. Recorded: 2026-10-25.
Scope: UC-001 increment 1 delivery boundary; documentation only, no activation
or delivery authorization.

## Context

The accepted [matching design](../ARCHITECTURE.md#location-reference-data-and-matching)
selected swisstopo for CH/LI and GeoNames cities500/admin1 for worldwide locality
matching. The [5X checkpoint](../TASKS.md#priority-5x--current-exit-readiness-checkpoint-2026-10-23)
identified the need for an explicit owner decision on the latter's delivery scope.
That earlier selection and checkpoint remain historical evidence.

## Decision — approved 2026-10-23

For UC-001 increment 1, reference-backed locality matching is limited to the
approved CH/LI release under [ADR-006](ADR-006-locality-association-development-release.md).
Outside CH/LI, existing honest clarification and explicit country-only or
user-confirmed/reference-unverified continuation satisfy the locality handling
required for Priority 5. Preserve independent textual constraints, minimal
retention and evidence-based applicability; confirmation or a reference match
never establishes provider coverage.

Defer GeoNames cities500/admin1 locality-matching preparation, review and
integration **beyond increment 1**. Retain this selected capability in the intended
design; it is not implemented. Future acquisition, preparation, review and
integration require separate authorization.

The approved GeoNames countryInfo catalogue under [ADR-005](ADR-005-country-reference-development-release.md)
is **not deferred**. All approved country choices and DE/FR/IT/EN requirements
remain unchanged. No other accepted requirement, criterion or test identifier
changes. Resolena-controlled processing, atomic save-before-presentation,
ownership/payload-bound recovery, immutable evidence and existing safeguards remain.

## Consequences and acceptance boundary

This resolves 5X's locality-scope decision. Using its existing findings, the
recommendation is: **Ready for scoped owner acceptance under the amended
increment-1 locality boundary, subject to the existing evidence limits.**
Scope approval is not Priority 5 acceptance or completion. Increment 1 and DEVELOP
remain incomplete; real interpretation stays under Priority 3, reviewed knowledge
and renderings under Priority 4, with later Priority 6 integrated/qualified review and
formal Phase 4 VALIDATE gates unchanged. No combined regression pass is inferred.

Approved references retain their development-only permissions. Normal app.main
remains unconfigured; real alternative/rendering drafts stay inactive. No
implementation, tests, services, acquisition or experiments are authorized here.
See the [UC clarification](../specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#flow)
and [recorded resolution](../TASKS.md#increment-1-locality-scope-resolution--recorded-2026-10-25).

## Priority 5 acceptance — owner decision, 2026-10-25

The owner accepted Priority 5 for UC-001 increment 1 under this amended locality
boundary, limited to the demonstrated obligation groups and original receipts in
the [5X checkpoint](../TASKS.md#priority-5x--current-exit-readiness-checkpoint-2026-10-23).
The [existing acceptance record](../TASKS.md#priority-5-owner-acceptance--2026-10-25)
is the provenance; this submission alignment records no new acceptance. The
2026-10-23 scope approval and 2026-10-25 acceptance are separate decisions.

Controlled interleavings, bounded observations, mocked UI outcomes and synthetic
fixtures retain their original limits. Counts and reruns cannot be added into a
combined regression result; static advisor review supplies no independent test
execution. Real interpretation, knowledge/renderings, qualified linguistic review
and TL-03 are outside this acceptance. Priorities 3/4 remain partial; Priority 6
integrated/qualified review and formal Phase 4 validation remain pending. Increment
1 and DEVELOP remain incomplete. PHASE: 3 / STATUS: in-progress.
