# ADR-003 — Atomic saved-comparison boundary

Date: 2026-10-10.
Decision status: accepted as the increment-1 implementation baseline, 2026-10-15.
Before recording acceptance, the approved UC and this ADR were checked against
the owner-reviewed ARCHITECTURE.md: no material conflict. Atomic saving, immutable
evidence, saved identities and ownership/payload-bound recovery remain unchanged.
The owner authorized Phase 3, priority 1 only; that synthetic slice is implemented
and verified (8 backend / 2 real browser/API/SQLite tests). Complete recovery/security
matrices remain unverified. Interpreter/hosting, reviewed knowledge and qualified
review remain open. [Checks and limits](../PROJECT.md#priority-1-verification--2026-10-15).
Earlier pending-review statements below describe refinement history.

## Context and refinement history

The initial 2026-10-10 proposal retained atomic comparison persistence and immutable
evidence context. The owner found that direction acceptable for further refinement;
this is not final DESIGN acceptance or implementation authorization.
The owner approved the scoped multilingual UC-001 requirement amendment on
2026-10-10, with support unverified; its canonical behaviour/acceptance remains in
[UC-001](../specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#language-amendment--owner-approved-2026-10-10).
Saved original request and language/derivation context now constrain the proposed
boundary; aliases/templates are provisional, not general automatic translation.
The interpreter-versus-structured-input comparison is in
[ADR-004](ADR-004-multilingual-interpretation-scope.md). On 2026-10-11 the owner
retained multilingual free text and its privacy boundary (A), declining B's scope
changes. Interpreter/hosting selection and final DESIGN acceptance remain pending;
this direction does not amend the original-request persistence contract.
A subsequent owner-requested refinement supersedes the original new-key-on-every-retry
proposal with same-identity recovery and a separate explicit fresh-search action.
At that refinement O-1/O-2 were pending. The owner approved O-1/O-2 on 2026-10-10,
including same-key concurrency/payload integrity and originating-client recovery
ownership; canonical behaviour is in the UC. Final technical DESIGN/ADR acceptance
remains pending. Identifier knowledge alone must grant no request/result/status access.
UC-001 increment-1 SPECIFY is accepted, including persistence before presentation,
stable displayed identities, partial-write handling and reassessment on explicit retry.
SQLite/SQLAlchemy and the existing conceptual entities remain the baseline.
Repository inspection found only the frontend starter and empty backend/test
directories; there is no usable application knowledge catalogue or comparison store.

## Alternatives and rationale

| Choice | Recommendation / trade-off |
|---|---|
| Reconstruct old comparisons from current references vs saved snapshots | Immutable shown values/order and append-only evidence versions preserve what supported the result. Snapshots add storage; current catalogue updates cannot replace saved facts. |
| Commit components independently vs one transaction | One request/outcome/options/evidence-association commit enforces the approved presentation boundary. A failed transaction produces no completed result; confirmed rollback and unknown commit acknowledgement remain distinct. |
| Original retry proposal (superseded) | Initially recommended new keys for explicit retry with prior-save acknowledgement; this can duplicate an uncertain but committed submission. Preserve this rationale as history; use the revised recovery/fresh-search distinction below. |
| Same-submission recovery vs deliberate fresh search | Recovery preserves key/payload and acknowledges an already saved outcome without claims of current freshness. With no established committed result, reassess before the same-key atomic save; uniqueness prevents duplicate records. A separate fresh-search action uses a new identity and reassesses. |
| New records for duplicate wire delivery vs unique key | Unique committed submission-key digest plus payload digest gives one saved record per intended submission, even if concurrent duplicate computations occur. Same key/different payload is a protocol conflict. |
| Automatic recovery/history fetch vs explicit recovery | No automatic retry/polling or history endpoint. Recommend explicit same-key recovery acknowledgement and separately assessed fresh search; O-2 behaviour is now scoped owner-approved; enforcement remains unverified. No saved-history interface follows. |

## Decision — accepted 2026-10-15

Use the existing SearchRequest/Alternative/RequestAlternative/Evidence concepts,
with an evidence association relation and snapshot JSON described canonically in
[ARCHITECTURE.md](../ARCHITECTURE.md#persistence-model-and-atomic-boundary).
Persist a valid request/interpretation and either the comparison/options/evidence
associations or insufficient-coverage outcome atomically. Invalid/clarification
submissions create no application search records. Foreign keys and unique request/
option positions protect identity; referenced Evidence versions are immutable.

Return the committed projection only on acknowledged success. A concurrent unique-key
loser rolls back and acknowledges the committed winner, without reconstructing or
presenting an old snapshot as a fresh comparison. If commit state cannot be established,
report uncertainty rather than saved/unsaved. Recovery retains the original key
and captured payload; absence of a row is not proof of failure while another attempt
may run. A newly prepared comparison repeats interpretation/applicability/evidence/
freshness checks before saving under the same key. Unique-key conflict acknowledges
the committed winner and never presents the loser's unsaved projection.
A committed recovery returns ID/outcome/assessed-at acknowledgement only, not stale
claims presented as fresh. A deliberately fresh search uses a new key/current fields
and full reassessment; it may intentionally create a separate record. Review dates
and historical snapshot content remain unchanged. This replaces prior-key metadata
and new-key-on-every-retry proposals; no automatic retry is introduced.

Recovery also requires originating-client proof beyond the identifier. The proposed
binding/digest and uniform-denial mechanism is canonical in ARCHITECTURE.md; no
security test or passing implementation is claimed by the language spike.

The saved-comparison reader is internal and returns the exact request/option/
evidence context needed by future UC-003. It creates no Selection, does not change
factual validation or renew review dates, and defines no selection eligibility.

## Policy proposals and consequences

- O-2: same-key recovery acknowledgement versus separately keyed explicit fresh
  search, with truthful loading/save state, concurrency/payload integrity and
  originating-client ownership, was scoped owner-approved on 2026-10-10.
  Recovery cannot duplicate a saved submission; the acknowledgement has no current
  comparison/freshness claim. A fresh search intentionally may create another record.
- O-1, scoped owner-approved on 2026-10-10: manual clarification may retain an
  unverified intended locality without
  pretending reference verification or treating intent confirmation as evidence of
  product/service applicability. The independent coverage safeguards are canonical in
  [ARCHITECTURE.md](../ARCHITECTURE.md#owner-decisions-and-material-trade-offs).
- The complete logical field/API/reference/test recommendations now exist in
  ARCHITECTURE.md; data-release hashes and dependency pins are later preparation
  checks, not an open-ended architecture list.
- Immutable snapshots preserve historical support, not guaranteed current price/
  availability. The extra association is a technical relation, not proof of rubric
  compliance. No account/device tracking, history interface, outward queries,
  automatic review or selection implementation is introduced.

Accepted behaviour: [UC-001](../specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#acceptance).
Lifecycle: [TASKS.md](../TASKS.md). ADR-001/ADR-002 remain intact.
DESIGN acceptance was explicitly given on 2026-10-15, not inferred from refinement.
Priority-1 DEVELOP is authorized; mandatory research, UC-003 decisions, full journey
validation and delivery remain pending.
