"""Offline, pinned GeoNames draft or approved development-release preparation."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import shlex
import sys


SOURCE = "https://download.geonames.org/export/dump/countryInfo.txt"
README = "https://download.geonames.org/export/dump/readme.txt"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
APPROVED_SOURCE_SHA256 = "c55f638cfaafb4fe45a9aa15120a0f1f78e8a34a8e1847d7b9320cf740fbc9ab"
APPROVED_ON = "2026-10-23"
RELEASE_ID = "geonames-countryInfo-2026-10-23-v1"
APPROVAL_SCOPE = "Priority 5R development slice and isolated demo/test composition only"
HEADER = "\t".join(("#ISO", "ISO3", "ISO-Numeric", "fips", "Country", "Capital",
    "Area(in sq km)", "Population", "Continent", "tld", "CurrencyCode", "CurrencyName",
    "Phone", "Postal Code Format", "Postal Code Regex", "Languages", "geonameid",
    "neighbours", "EquivalentFipsCode"))
DISPOSITIONS = {
    "AN": ("excluded", "Publisher identifies the Netherlands Antilles as dissolved on 10 October 2010.",
        "# AN (the Netherlands Antilles) with geonameId = 8505032 was dissolved on 10 October 2010."),
    "CS": ("excluded", "Publisher identifies Serbia and Montenegro as no longer existing.",
        "# CS (Serbia and Montenegro) with geonameId = 8505033 no longer exists."),
    "XK": ("unresolved", "Publisher labels XK temporary. Human review must decide membership under the current-country/territory policy; no replacement or ISO status is inferred.",
        "# The countrycode XK temporarily stands for Kosvo:"),
}


def extract(raw, *, approved_release=False):
    if approved_release and sha256(raw).hexdigest() != APPROVED_SOURCE_SHA256:
        raise ValueError("Source does not match the owner-approved source pin")
    lines = raw.decode("utf-8").splitlines()
    if [line for line in lines if line.startswith("#ISO")] != [HEADER]:
        raise ValueError("Expected exactly one unchanged countryInfo header")
    result = {"countries": [], "source_rows": 0, "excluded": [], "unresolved": [],
        "preserved_edge_whitespace": []}
    seen = set()
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 19:
            raise ValueError(f"Expected 19 source columns at line {number}")
        code, name = columns[0], columns[4]
        if not re.fullmatch(r"[A-Z]{2}", code) or not name.strip() or code in seen:
            raise ValueError(f"Invalid or duplicate source code/name at line {number}")
        seen.add(code)
        result["source_rows"] += 1
        entry = {"code": code, "name": name}
        if name != name.strip():
            result["preserved_edge_whitespace"].append({"code": code, "source_line": number})
        if code in DISPOSITIONS:
            disposition, reason, note = DISPOSITIONS[code]
            if note not in lines:
                raise ValueError(f"Missing publisher support for {code} disposition")
            result[disposition].append({**entry, "source_line": number, "reason": reason,
                "support": {"line": lines.index(note) + 1, "text": note}})
        else:
            result["countries"].append(entry)
    if not seen:
        raise ValueError("Source has no country rows")
    if approved_release:
        previous = result["unresolved"].pop()
        result["countries"].append({"code": previous["code"], "name": previous["name"]})
        result["decision_history"] = [{"code": "XK", "name": previous["name"],
            "previous_disposition": "unresolved",
            "previous_manifest": "docs/reference/COUNTRIES-GEONAMES-MANIFEST.json",
            "previous_decision": previous, "disposition": "included", "approved_on": APPROVED_ON,
            "basis": "Owner accepted the pinned source-based catalogue policy: retain the existing 249 entries, include XK and exclude AN/CS.",
            "limitation": "XK is a GeoNames temporary/source-specific code; inclusion claims neither an official ISO assignment nor a political-status determination."}]
    result["countries"].sort(key=lambda entry: entry["code"])
    return result


def catalogue_bytes(countries):
    return (json.dumps(countries, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--prepared-at", required=True)
    parser.add_argument("--approved-release", action="store_true",
        help="Apply only the owner's dated approval for the pinned Priority 5R development release")
    args = parser.parse_args()
    if datetime.fromisoformat(args.prepared_at).utcoffset() is None:
        raise ValueError("Preparation timestamp requires an explicit timezone")
    raw = args.source.read_bytes()
    acquired = json.loads(args.acquisition.read_text())
    source = next(item for item in acquired if item["reference"] == SOURCE and item.get("HTTP_status") == 200)
    readme = next(item for item in acquired if item["reference"] == README and item.get("HTTP_status") == 200)
    actual_hash = sha256(raw).hexdigest()
    if actual_hash != args.source_sha256 or actual_hash != source["sha256"]:
        raise ValueError("Pinned source or acquisition hash mismatch")
    readme_path = args.acquisition.parent / readme["file"]
    readme_raw = readme_path.read_bytes()
    if sha256(readme_raw).hexdigest() != readme["sha256"] or LICENSE.encode() not in readme_raw:
        raise ValueError("Format/licensing readme hash or license reference mismatch")
    result = extract(raw, approved_release=args.approved_release)
    output = catalogue_bytes(result["countries"])
    counts = {"source_rows": result["source_rows"], "included": len(result["countries"]),
        "excluded": len(result["excluded"]), "unresolved": len(result["unresolved"])}
    manifest = {
        "status": "draft", "runtime_use": False, "synthetic": False,
        "review": {"status": "pending", "reviewer": None, "reviewed_at": None,
            "owner_approved": False, "activation_approved": False,
            "basis": "AI preparation and automated structural checks only; all inclusion/exclusion, source-name and release decisions await human review."},
        "publisher": "GeoNames", "source_reference": SOURCE,
        "snapshot_id": "geonames-countryInfo-sha256-" + actual_hash,
        "raw_source": {"path": str(args.source), "sha256": actual_hash, "bytes": len(raw)},
        "source_release": None, "source_publication_date": None, "source_update_date": None,
        "publisher_HTTP_last_modified": source["publisher_HTTP_last_modified"],
        "date_limit": "No named release or entry validity/publication/update dates supplied in the file. HTTP Last-Modified identifies the resource timestamp only; it is not factual review or per-entry currentness.",
        "retrieved_at": source["retrieved_at"], "prepared_at": args.prepared_at,
        "acquisition_record": str(args.acquisition),
        "documentation": [{**item, "path": str(args.acquisition.parent / item["file"])
            if item.get("HTTP_status") == 200 else None}
            for item in acquired if item["reference"] != SOURCE],
        "normalized_output": {"path": str(args.output), "sha256": sha256(output).hexdigest(),
            "bytes": len(output), "fields": ["code", "name"], "order": "source code, ascending"},
        "counts": counts,
        "extraction_rules": [
            "Strict UTF-8 and unchanged 19-column header/rows; ISO column becomes code, Country becomes name.",
            "Codes must have two uppercase ASCII letters and be unique across all dispositions; names must be nonblank.",
            "Source names and codes are verbatim, including Unicode and edge whitespace. No translations, aliases or replacement codes.",
            "All other source-listed country/territory entries are provisional inclusion candidates; no language, alternative/research coverage, population or sovereignty filter.",
            "AN/CS excluded only with the publisher's matching obsolete-entry notes. XK withheld as unresolved under the publisher's temporary-code note; human decision pending.",
            "Sort included codes and emit deterministic two-field UTF-8 JSON. Import no spatial, address or other source columns."],
        "excluded": result["excluded"], "unresolved": result["unresolved"],
        "preserved_edge_whitespace": result["preserved_edge_whitespace"],
        "attribution": {"credit": "Country code/name data derived from GeoNames countryInfo.",
            "source_link": SOURCE, "license": "CC BY 4.0", "license_link": LICENSE,
            "license_basis": {"path": str(readme_path), "sha256": readme["sha256"], "reference": README},
            "requirements": "Retain appropriate credit, source/license links and modification notice; do not imply endorsement or add restrictions. Keep this manifest with the extract.",
            "changes": "Selected ISO/Country fields, sorted codes and applied the explicit excluded/unresolved ledger. Source names unchanged.",
            "disclaimer": "GeoNames supplies data as is, without accuracy, timeliness or completeness warranty."},
        "limitations": [
            "Reference membership candidates only; no product availability, delivery, service coverage or user-location inference.",
            "No guarantee of geopolitical status, universal completeness or per-entry currentness. All entries need human factual/release review.",
            "Publisher-provided names only; no DE/FR/IT/EN localization or qualified linguistic acceptance.",
            "No app.main, demo, API, frontend or saved-record integration. Future snapshot replacement and activation require explicit authorization."],
        "preparation": {"script": str(Path(__file__).relative_to(Path.cwd())),
            "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "command": shlex.join(sys.orig_argv)},
    }
    if args.approved_release:
        basis = "Owner acceptance of the source-based catalogue policy and release basis; no independent factual verification of every entry or linguistic approval."
        manifest.update({"status": "approved-development", "runtime_use": "development-only",
            "release_id": RELEASE_ID,
            "approval": {"owner_approved": True, "approved_on": APPROVED_ON, "approved_at": None,
                "scope": APPROVAL_SCOPE, "production_activation_approved": False,
                "independent_factual_review": False, "linguistic_approval": False, "basis": basis},
            "review": {"status": "owner-approved-source-policy", "reviewer": "owner",
                "reviewed_at": None, "owner_approved": True, "activation_approved": True,
                "activation_scope": APPROVAL_SCOPE, "basis": basis},
            "decision_history": result["decision_history"],
            "limitations": [
                "Reference membership only; no product availability, delivery, service coverage or user-location inference.",
                "Owner acceptance covers the source-based policy and release basis, not independent factual verification of every entry, geopolitical status or per-entry currentness.",
                "Publisher-provided names only; no DE/FR/IT/EN localization or qualified linguistic acceptance.",
                "Activation is limited to the Priority 5R development slice and isolated demo/test composition. Normal app.main remains unconfigured; production activation and future snapshot replacement require separate authorization."]})
        manifest["extraction_rules"][3:5] = [
            "Retain all existing 249 source-listed inclusion candidates under the owner-approved source-based country/territory policy; no language, alternative/research coverage, population or sovereignty filter.",
            "AN/CS remain excluded with the publisher's obsolete-entry notes. Include XK under the owner's 2026-10-23 approval as a documented GeoNames temporary/source-specific code, without official ISO or political-status claims; retain its prior unresolved decision in history."]
        manifest["attribution"]["changes"] = "Selected ISO/Country fields, sorted codes, excluded AN/CS and included XK under the owner's 2026-10-23 source-based policy. Source names unchanged."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": counts, "sha256": sha256(output).hexdigest(),
        "status": manifest["status"], "runtime_use": manifest["runtime_use"]}, sort_keys=True))


if __name__ == "__main__":
    main()
