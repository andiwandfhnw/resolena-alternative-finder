# UC-001 — Bicycle repair / Switzerland: draft evidence packet

Revision 1, prepared 2026-10-18 by Codex from public provider pages.
**Factual extraction owner-approved within the scope below; applicability,
qualification and linguistic review pending; runtime_use: false; synthetic: false.**
This Markdown review record uses the existing Alternative, Claim, Money and
EvidenceVersion concepts. It is not an importable or activated knowledge release.

## Scenario and candidate

Accepted [E-IN-01](../specs/UC-001-FIND-AND-SELECT-ALTERNATIVE.md#acceptance):
“Repair my bicycle”, search country `CH`. Goal, constraints, budget, baseline,
town and postcode remain unspecified. Proposed retrieval concepts: subject
`bicycle`, action `repair`; this preparation verifies no interpreter behaviour.

Candidate: **Thömus workshop repair**, type `service`.
Alternative ID: `348f9f82-b6ba-4679-a312-c7faf14e8e8e`.
One candidate is prepared for review; this is neither an exhaustive search nor a
best-option claim. No candidate is admitted or presented as qualifying yet.

## Source records

Both sources are authoritative only for the provider's own scoped statements.
They are **provider-stated**, not independent corroboration, guaranteed prices,
confirmed appointments or proof that any particular bicycle can be repaired.
Two pages from this provider do not constitute two independent sources.

| Evidence metadata | E1 | E2 |
|---|---|---|
| Logical identity / revision | `thoemus-workshop`, 1 | `thoemus-oberried-location`, 1 |
| Version UUID | `122648bc-d6f1-4acb-99ca-bd34d305808d` | `b9053dca-7327-4056-ad78-89171163d746` |
| Publisher / attribution | Thömus AG / provider-stated | Thömus / provider-stated; embedded directory linked by the official site |
| Original source language | `de` | `de` |
| Source reference | [Workshop](https://thoemus.ch/services/werkstatt/) | [Official locations page](https://thoemus.ch/uber-uns/locations/), embedding [the directory](https://thoemus-bikeworld.vercel.app/) |
| Passage locator | Service introduction; “Reparatur”; instructions immediately following the hourly rate | “Oberried” → “Thömus Shop” → address and workshop contact |
| Original support excerpts | “Service-Netzwerk in der ganzen Schweiz”; “Reparatur”; “Preis pro Stunde: CHF 120.00” | “Thömus Factory Store”; “Oberriedgässli 6”; “3145 Niederscherli (Oberried)” |
| Observed / retrieved date | 2026-10-18, day precision, UTC date | 2026-10-18, day precision, UTC date |
| Publication / update / stated expiry | Unknown / unknown / none found | Unknown / unknown / none found |
| Applicable period / underlying data period | Undated current-page statement; historical validity unknown / no study period stated | Undated current-page statement; historical validity unknown / no study period stated |
| At preparation: factual reviewer / reviewed_at / review_basis | None / null / pending | None / null / pending |
| Known invalidation / assessed expiry | Not established / unresolved | Not established / unresolved |

E2 was reached through E1's location-selection link. Its external hosting is
documented by the official page's iframe, not inferred from the directory name.
Address components above preserve the displayed address; text extraction joins
adjacent lines. No locality reference dataset or geocoding was used.

## Owner factual-extraction review — 2026-10-18

Reviewer: project owner, explicit confirmation in this conversation.
Review date: **2026-10-18**, day precision, recorded on the UTC date of confirmation.
The exact review instant/time zone was not supplied; `reviewed_at` remains null
at timestamp precision. This is not a fresh source retrieval or an expiry reset.

Review basis: the owner approved the packet's factual extraction as
**provider-stated evidence** for the repair service, the published **CHF 120.00
hourly rate** (E1), and the listed **Oberried workshop location** (E2), with all
recorded conditions and unknowns. This records approval of those extractions,
not independent corroboration or guaranteed service/price/availability.

Bound to the original revision-1 packet, SHA-256:
`e472a52201eeec88e87d6a851a40707f5c529b2ed097cb0bd86043846ef9e679`.
Source excerpts, typed amount, evidence identities and preparation metadata above
are retained. This review addendum does not approve unrestricted applicability,
candidate qualification, multilingual renderings or runtime activation. Tariff and
applicability questions below remain unresolved. No further research or experiment
is authorized by this review.

## Proposed claims and limits

These were AI-prepared extractions; the three factual statements identified above
now have owner approval as provider-stated evidence. They are not approved renderings.
The proposed `applicability: true` assessment remains unapproved. For every row,
`freshness` and qualifying `requirement` satisfaction remain `unverified`.
Independent verification is not claimed.

| Claim key / typed value | Support and geographic/condition scope | Proposed freshness kind/window after actual review |
|---|---|---|
| `relevance`: `bicycle`; `action:repair`: `true` | E1: bicycle workshop repairs; describe the work to the chosen branch by telephone. No all-brands/all-faults guarantee. | `service_coverage`, 90 elapsed days |
| `applicability`: `true`, proposed country-only scope | E1/E2: listed Swiss workshops; one concrete provider-listed location is Oberriedgässli 6, 3145 Niederscherli (Oberried). This is a provider location, not an inferred user locality. No home collection, mobile coverage, distance or access-from-anywhere claim. | `service_coverage`, 90 elapsed days |
| `financial`: hourly repair rate below; `specific`: `true`; `comparative`: `false` | E1: network-published repair rate. Branch-specific quote, availability, procedure and material costs require contact. No asserted branch-specific final price. | `price`, 24 elapsed hours |

Exact proposed financial value, using the existing Money fields:

```json
{
  "amount": "120.00",
  "currency": "CHF",
  "unit": "workshop labour hour",
  "period": "once",
  "basis": "hourly repair rate; not a complete repair quote",
  "charges_known": false,
  "exclusions": [],
  "assumptions": [],
  "price_basis": "provider-published rate"
}
```

No duration is assumed. An empty exclusions list means no separately confirmed
exclusion was extracted, not that everything is included. Parts/material amounts,
tax treatment, minimum billing/rounding, additional charges and final cost remain
unknown; none is zero. No conversion, total-cost calculation or savings is made.
Baseline and financial advantage remain unknown. Environmental/resource impact
and advantage remain unknown: no candidate-specific method, baseline, data period
or inputs were established. No environmental marketing claim is admitted.

Appointment/parts availability and this bicycle's repairability/acceptance remain
unknown. The draft does not assume its brand, motor, fault or travel requirements.

Retrieval is not review. The owner review date is recorded separately above; no
checked-at instant or expiry is invented from either day-only date. Freshness
remains unresolved. With sufficient review precision and scope, each claim expires at its actual review
instant plus its accepted window, or an earlier source expiry/known invalidation;
it is expired at the boundary. Availability, if later evidenced, has a separate
24-hour window. Reopening this packet renews nothing.

## Acceptance mapping

This maps prepared material to criteria; it is not a passing acceptance report.

| Accepted criterion / examples | Packet contribution and remaining boundary |
|---|---|
| AC-01; E-IN-01/04 | Uses the exact country-only example with optional omissions preserved. No cheaper, environmental or no-replacement constraint is added. |
| AC-03/04/16; E-SQ-01/02 | E1/E2 service, rate and location extractions have scoped owner approval as provider-stated evidence. Applicability and candidate qualification remain unapproved. No locality-specific qualification or independent verification follows. |
| AC-05; E-FR-01/04–06/08 | Separate observation, publication, review and data-period fields; no current freshness claim without actual review. Recheck the price for its short window before future use. |
| AC-06; E-SU-01/02/04 | The published hourly cost extraction is owner-approved; its qualifying scope/usefulness remains for assessment. Environmental content is explicitly unknown. No baseline or advantage is needed for this unconstrained scenario or invented here. |
| AC-07/08; E-OP-01/04 | One candidate can suffice only after all qualification checks. If none qualifies, the accepted saved insufficient-coverage route applies, without implying no alternatives exist. No runtime assessment/save occurs here; ordering/limit remain unchanged. |
| AC-09; E-OP-06/07 | Exact CHF amount and hourly basis; unknown total/charges, no conversion or cheaper claim. This packet cannot establish a budget or cheaper goal. |
| AC-10/12; ADR-003 | Support, freshness and requirement satisfaction stay separate. Future admitted evidence versions and saved content must retain provenance/unknowns and atomic save-before-presentation. No store or saved comparison is changed. |
| AC-13 | Manual preparation uses public service information and the accepted public example. Adds no runtime research, refresh, external LLM forwarding or user-location collection. |
| AC-15; LAC-09/11/12; TL-03 | Original German support retained. This English review draft is AI-prepared; faithful DE/FR/IT/EN rendering, source/target linguistic review and cross-language validation remain pending. |

## Unresolved evidence and review gaps

1. The scoped owner review above completes factual-extraction approval only.
   Applicable claim scope, the hosting chain and usability still need admission
   review; sufficient actual review-time precision is missing for freshness.
   Any same-scope conflict or changed/expired statement must be resolved before
   use. No new source check or comprehensive conflict search is claimed.
2. Confirm the tariff's branch/bike scope and disclose any applicable restrictions.
   The pages do not establish all-brand acceptance, tax/billing details or a
   final quote. Do not silently broaden the rate or service scope. Unknown total,
   baseline, availability and environmental advantage are not automatically
   disqualifying for E-IN-01; a material unresolved usability condition is.
3. Qualified source-language and DE/FR/IT/EN target-language reviewers must review
   faithful claim, condition and unknown renderings. Prior interpreter-expectation
   approvals do not approve this packet. No renderings, aliases or templates are
   approved here, and TL-03 is unverified.

No knowledge release is published/activated. The v1.4.0 interpreter failure remains
closed; this packet establishes no interpreter suitability, multilingual capability,
application journey or increment completion. Priority 4 review preparation is partial;
Priority 3 remains partial and Phase 3 DEVELOP remains in-progress.
