# ADR-005 — Pinned country reference for the development slice

Status: owner-approved, 2026-10-23. Scope: UC-001 Priority 5R development and
isolated demo/test composition; no production activation or deployment.

Use the existing GeoNames countryInfo source and pinned raw SHA-256
`c55f638cfaafb4fe45a9aa15120a0f1f78e8a34a8e1847d7b9320cf740fbc9ab`.
Retain the 249 draft entries and include XK/Kosovo; exclude obsolete AN/CS.
XK is a documented temporary/source-specific GeoNames code, without an official
ISO-assignment or political-status claim. Preserve source names and attribution,
including BQ's disclosed boundary whitespace. The owner accepts the source-based
policy and release basis, without independently verifying every entry or granting
linguistic approval.

Generate a separate versioned release and approval manifest; preserve the original
[5Q draft and pending manifest](../reference/COUNTRIES-GEONAMES-MANIFEST.json).
The approved accounting is 252 source rows = 250 included + 2 excluded + 0 unresolved.
Retain XK's earlier unresolved decision and its explicit approved disposition.

Use the same approved local reference for UI choices and new-submission membership.
An unavailable/corrupt/unapproved reference is configuration failure, not evidence
of invalid country. A valid country does not imply alternative knowledge or delivery/
service applicability. Country clearing stays explicit; no automatic CH restoration.
Committed ownership/payload-bound recovery precedes current reference loading;
record the new-validation release in server-derived provenance without changing
the captured client payload or historical records. See the implementation boundary
in [ARCHITECTURE.md](../ARCHITECTURE.md#location-reference-data-and-matching).

Owner continuation, 2026-10-23: the unchanged approved country release may also be
used for Priority 5S's bounded O-1 locality-confirmation development/test slice,
under the same restrictions. This adds no production approval, new source review
or release-byte change; the original manifest and its dated approval remain intact.
