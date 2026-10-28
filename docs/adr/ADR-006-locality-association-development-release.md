# ADR-006 — Pinned CH/LI association reference for development

Status: owner-approved, 2026-10-23. Scope: UC-001 Priority 5U development and
isolated demo/test composition; no production activation or deployment.

Accept swisstopo's 2026-10-01 snapshot and its 5,716 CH/LI associations, documented
country derivation, field mapping, attribution and limitations. The source ZIP is
pinned to SHA-256 `0903076e7c3b8670d836ec20d486f9d2045b120e61f07d27a2bd7be09443098b`.
The separate [release](../reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01.json) keeps
the original draft bytes, SHA-256
`eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9`, with its own
[approval metadata](../reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-APPROVAL.json).
Preserve the [5T draft/manifest](../reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-MANIFEST.json),
raw source, acquisition history and receipts unchanged. This is owner acceptance
of the source-based policy and release basis, not independent factual verification
of every association or linguistic approval.

Use one approved local release through an application port. Exact matching stays
within the selected country, using boundary trim, Unicode NFC/casefold for names
and trimmed postcode strings; town plus postcode intersects both conditions.
Do not invent aliases, strip accents, split multilingual names or infer nearby
places. Countries outside CH/LI remain valid country choices without matching
capability from this release. Broken/unapproved reference loading is configuration
failure, never a successful empty lookup.

Keep every postal/municipal association. Multiple matches require clarification
and explicit selection; never take the first or merge shared names, postcodes,
ZIP_ID values or municipalities. A selection pointer is
`{source:swisstopo,release,source_record}` and must identify an association in the
approved release, consistent with country and all entered locality fields.
ZIP_ID remains postal identity; source_record is release-bound extraction
identity. Neither is an authoritative locality GUID, and cross-postcode locality
identity remains unresolved. Selection alone sends nothing; explicit continuation
captures new intent, and country/town/postcode edits clear the selection.

Reference presence establishes only a match within this snapshot, not delivery,
service coverage, detected user location or universal currentness. Absence alone
does not prove invalidity. Preserve O-1's separate confirmed/unverified route and
independent applicability/textual-constraint checks. Checked committed recovery
precedes current reference loading; retain server-derived provenance separately
from the captured client payload. Save assessed outcomes atomically before display.
Normal app.main remains unconfigured; production use and replacement need separate
authorization. See [ARCHITECTURE.md](../ARCHITECTURE.md#location-reference-data-and-matching).
