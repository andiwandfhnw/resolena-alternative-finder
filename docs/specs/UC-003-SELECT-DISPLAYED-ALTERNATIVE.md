# UC-003 — Select a displayed alternative

Incomplete draft — Errors, Acceptance and Tests are pending owner review.

Approval provenance: Flow below retains original journey steps 8–9 approved
on 2026-10-07 in UC-001. The owner approved this decomposition on 2026-10-09;
the complete specification and proposed policies are not thereby approved.
See [ADR-002](../adr/ADR-002-use-case-decomposition.md).

## Intent

Let a user record a preferred alternative from the comparison produced by
[UC-001](UC-001-FIND-AND-SELECT-ALTERNATIVE.md). Trigger: explicitly choose a
displayed alternative. Outcome: the choice is saved against its request and
saving is confirmed, without changing factual confidence or validation status.

## Actors

Primary: A user choosing an alternative, without needing an account.

Persistence is an internal system component, not an external actor. Research,
location input and applicability assessment belong to UC-001.

## Preconditions

- UC-001 has persisted the request, interpretation, displayed alternatives and
  evidence before presenting the comparison.
- Resolena-controlled persistence is available.
- The choice concerns an alternative displayed for that request.

Availability-based selection eligibility remains pending owner approval:
verified availability, unknown availability and geographic limitations must not
be conflated. Whether uncertain/inapplicable alternatives are selectable,
blocked or require a warning is unresolved; no acknowledgement step is approved.

The [shared privacy boundary](../ARCHITECTURE.md#strict-runtime-privacy) and
[location constraints](UC-001-FIND-AND-SELECT-ALTERNATIVE.md#preconditions)
remain binding. This use case authorizes no external LLM transmission or new
location collection, research, accounts or history interface.

## Flow

Original journey numbering is retained for traceability; steps 1–7 are in UC-001.

8. Select: The user explicitly selects one of the displayed
   alternatives. The system stores the selection against that request
   and confirms it was saved.

9. Preserve evidence integrity: The selection is available as a
   relevance signal for future requests. It does not automatically
   change factual confidence or validation status.

Acceptance boundary: explicit selection, persistence, confirmation and evidence
integrity, following a persisted comparison. Leaving UC-001 without choosing
does not invoke this flow or infer a selection; the request/results remain saved.
Both journey increments use the same selection guarantees.

## Errors

Pending definition and owner review. Draft recommendation: if storage fails,
report that saving failed rather than confirm success. Missing/stale request,
invalid choice, retry and repeated-selection policies still need definition.
Availability-based eligibility and any warnings/blocks remain unresolved;
UC-001 owns market coverage and research fallback policies.

## Acceptance

Draft/pending owner review; not a complete acceptance specification:

- Given a persisted displayed comparison, when the user explicitly chooses an
  eligible displayed alternative (eligibility pending), then store the choice
  against its request and confirm saving.
- Given a saved selection, when its relevance signal is used, then factual
  confidence and validation status do not automatically change.
- Given no explicit choice, when the user leaves, then no selection is inferred
  and UC-001's persisted request/results remain.

The [selection versus realized savings clarification](../PRODUCT_CONTEXT.md#pending-specify-clarification)
remains proposed, not approved behaviour. Currency, market fallback and selection
eligibility policies remain pending; decomposition introduces no Saver features.

## Tests

Draft scenarios — pending owner review; no executable tests are created.

- Unit: explicit choice against a displayed request alternative; evidence-integrity
  rule; agreed eligibility/error policies once approved.
- Integration: choice stored against the persisted request; confirmation reflects
  storage outcome; confidence/validation unchanged; no inferred selection.
- E2E: comparison-to-selection journey for sufficient knowledge and for approved
  research after insufficient/empty knowledge; persistence precedes presentation
  and selection. Retain location/availability labels from UC-001; eligibility
  assertions await approval.
