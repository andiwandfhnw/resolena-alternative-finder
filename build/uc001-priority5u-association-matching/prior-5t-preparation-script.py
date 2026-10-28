"""Prepare an inactive, pinned swisstopo CH/LI locality/postcode draft offline."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
from hashlib import sha256
import io
import json
from pathlib import Path
import shlex
import sys
import unicodedata
import zipfile


COLLECTION = "https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo-vd.ortschaftenverzeichnis_plz"
ITEMS = COLLECTION + "/items"
SOURCE = "https://data.geo.admin.ch/ch.swisstopo-vd.ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz_2056.csv.zip"
PRODUCT = "https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities"
FORMAT = "https://www.swisstopo.admin.ch/dam/de/sd-web/63GBDVbxjKqw/Jan26_Amtliches%20Ortschaftenverzeichnis%20-%20Technical%20Documentation.pdf"
TERMS = "https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices"
MEMBER = "AMTOVZ_CSV_LV95/AMTOVZ_CSV_LV95.csv"
HEADER = ("Ortschaftsname", "PLZ4", "Zusatzziffer", "ZIP_ID", "Gemeindename", "BFS-Nr",
    "Kantonskürzel", "Adressenanteil", "E", "N", "Sprache", "Validity")
CH_CANTONS = set("AG AI AR BE BL BS FR GE GL GR JU LU NE NW OW SG SH SO SZ TG TI UR VD VS ZG ZH".split())
REQUIRED = ("Ortschaftsname", "PLZ4", "Zusatzziffer", "ZIP_ID", "Gemeindename", "BFS-Nr")


def output_bytes(rows):
    return (json.dumps(rows, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def extract_csv(raw):
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), delimiter=";", strict=True)
    if tuple(next(reader, ())) != HEADER:
        raise ValueError("Expected unchanged twelve-column swisstopo CSV header")
    source = list(reader)
    if not source:
        raise ValueError("Source has no data records")
    rows, excluded, unresolved = [], [], []
    raw_records = {}
    identities = defaultdict(set)
    for number, values in enumerate(source, 1):
        if not values:
            excluded.append({"source_record": number, "reason": "Blank CSV data record"})
            continue
        if len(values) != len(HEADER):
            unresolved.append({"source_record": number, "reason": "Unexpected column count"})
            continue
        record = dict(zip(HEADER, values, strict=True))
        missing = [key for key in REQUIRED if not record[key].strip()]
        canton = record["Kantonskürzel"]
        if missing or (canton and canton not in CH_CANTONS):
            unresolved.append({"source_record": number,
                "reason": "Missing required values: " + ", ".join(missing) if missing else "Undocumented canton/country assignment"})
            continue
        country = "LI" if canton == "" else "CH"
        name, postcode = record["Ortschaftsname"], record["PLZ4"]
        postal_id, additional = record["ZIP_ID"], record["Zusatzziffer"]
        identities[postal_id].add((country, name, postcode, additional))
        rows.append({"source_record": number, "country_code": country,
            "locality_name": name, "postcode": postcode, "source_postcode_id": postal_id,
            "additional_number": additional,
            "administrative": {"municipality_name": record["Gemeindename"],
                "municipality_id": record["BFS-Nr"], "canton": canton},
            "matching": {"locality_name": unicodedata.normalize("NFC", name.strip()).casefold(),
                "postcode": postcode.strip()}})
        raw_records[number] = tuple(values)
    conflicts = {key for key, values in identities.items() if len(values) > 1}
    included = []
    duplicates = []
    seen_raw, seen_retained = {}, {}
    exact_duplicates = 0
    for row in rows:
        number = row["source_record"]
        if row["source_postcode_id"] in conflicts:
            unresolved.append({"source_record": number, "reason": "Conflicting country/name/postcode/additional number for source ZIP_ID"})
            continue
        included.append(row)
        source_key = raw_records[number]
        retained_key = json.dumps({key: value for key, value in row.items() if key != "source_record"}, sort_keys=True)
        if retained_key in seen_retained:
            exact = source_key in seen_raw
            exact_duplicates += exact
            duplicates.append({"source_record": number,
                "same_as": seen_raw[source_key] if exact else seen_retained[retained_key],
                "kind": "exact_source_record" if exact else "same_retained_association"})
        seen_raw.setdefault(source_key, number)
        seen_retained.setdefault(retained_key, number)
    return {"rows": included,
        "counts": {"source_records": len(source), "included": len(included),
            "excluded": len(excluded), "unresolved": len(unresolved),
            "duplicate_source_records": exact_duplicates, "duplicate_retained_associations": len(duplicates)},
        "excluded": excluded, "unresolved": sorted(unresolved, key=lambda row: row["source_record"]),
        "duplicates": duplicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "acquisition", "output", "manifest"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--prepared-at", required=True)
    args = parser.parse_args()
    if datetime.fromisoformat(args.prepared_at).utcoffset() is None:
        raise ValueError("Preparation timestamp requires an explicit timezone")
    acquired = json.loads(args.acquisition.read_text())

    def pinned(reference):
        record = next(item for item in reversed(acquired)
            if item["reference"] == reference and item.get("HTTP_status") == 200)
        path = args.acquisition.parent / record["file"]
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != record["sha256"] or len(raw) != record["bytes"]:
            raise ValueError("Acquisition hash mismatch: " + reference)
        return record, path, raw

    acquisition, source_path, source_bytes = pinned(SOURCE)
    raw = args.source.read_bytes()
    source_hash = sha256(raw).hexdigest()
    if source_hash != args.source_sha256 or raw != source_bytes:
        raise ValueError("Source hash mismatch")
    documents = []
    metadata = {}
    for reference in (COLLECTION, ITEMS, PRODUCT, FORMAT, TERMS):
        record, path, data = pinned(reference)
        documents.append({"reference": reference, "path": str(path), "sha256": record["sha256"],
            "bytes": len(data), "retrieved_at": record["retrieved_at"]})
        if reference in (COLLECTION, ITEMS):
            metadata[reference] = json.loads(data)
    item = next(value for value in metadata[ITEMS]["features"] if value["id"] == "ortschaftenverzeichnis_plz")
    if item["assets"]["ortschaftenverzeichnis_plz_2056.csv.zip"]["href"] != SOURCE:
        raise ValueError("Source is not the documented CSV asset")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if [name for name in archive.namelist() if not name.endswith("/")] != [MEMBER]:
            raise ValueError("Expected only the documented CSV archive member")
        csv_bytes = archive.read(MEMBER)
    result = extract_csv(csv_bytes)
    output = output_bytes(result["rows"])
    ids = defaultdict(list)
    for row in result["rows"]:
        ids[row["source_postcode_id"]].append(row)
    snapshot_at = item["properties"].get("datetime")
    snapshot_id = "swisstopo-ortschaften-" + (snapshot_at[:10] if snapshot_at else "unknown-date") + "-sha256-" + source_hash
    manifest = {
        "status": "draft", "runtime_use": False, "synthetic": False,
        "review": {"status": "pending", "owner_approved": False, "activation_approved": False,
            "reviewer": None, "reviewed_at": None},
        "publisher": "Federal Office of Topography swisstopo", "source_reference": SOURCE,
        "snapshot_id": snapshot_id, "export_identity": item["id"],
        "raw_source": {"path": str(source_path), "sha256": source_hash, "bytes": len(raw),
            "format": "ZIP with one UTF-8 BOM semicolon CSV; twelve exact columns",
            "member": {"path": MEMBER, "sha256": sha256(csv_bytes).hexdigest(), "bytes": len(csv_bytes)}},
        "source_dates": {"snapshot_at": snapshot_at,
            "metadata_updated_at": item["properties"].get("updated"),
            "publication_date": None, "reviewed_at": None,
            "publisher_HTTP_last_modified": acquisition.get("publisher_HTTP_last_modified"),
            "format_document_version": "1.2", "format_document_version_date": "2026-01-01",
            "limits": "STAC snapshot and update times describe this export; HTTP Last-Modified is a resource timestamp. CSV Validity is locality-name effective date, not export/retrieval/review time; omitted from draft. No per-entry factual currentness inferred."},
        "retrieved_at": acquisition["retrieved_at"], "prepared_at": args.prepared_at,
        "acquisition_record": str(args.acquisition), "documentation": documents,
        "normalized_output": {"path": str(args.output), "sha256": sha256(output).hexdigest(),
            "bytes": len(output), "order": "source data record order; source_record is one-based after the header"},
        "field_mapping": {"Ortschaftsname": "locality_name (verbatim)", "PLZ4": "postcode (string, verbatim)",
            "ZIP_ID": "source_postcode_id (string, PLZ6/ONRP identifier only)",
            "Zusatzziffer": "additional_number (string, verbatim; separate from PLZ4)",
            "Gemeindename": "administrative.municipality_name (label, not locality identity)",
            "BFS-Nr": "administrative.municipality_id (source municipal identifier, string)",
            "Kantonskürzel": "administrative.canton (verbatim) and documented derived country",
            "Adressenanteil,E,N,Sprache,Validity": "omitted; no spatial/address-share fields, invented aliases or verification dates"},
        "country_derivation": {"raw_country_column_supplied": False,
            "rule": "Documented empty canton denotes LI; the 26 observed Swiss canton labels denote CH. Unexpected labels remain unresolved.",
            "CH_canton_labels": sorted(CH_CANTONS), "basis": "Product information January 2026, attribute catalogue page 7; product coverage page 4."},
        "identity": {"locality_id_supplied": False, "postal_id_column": "ZIP_ID",
            "basis": "Product information pages 5-7: LOCALITYID is a locality GUID but is absent from this CSV; ZIP_ID identifies PLZ6 and is assigned by Swiss Post (ONRP).",
            "rule": "One row per locality/postcode/municipality association. source_record identifies an extraction record within this pinned input, never an authoritative locality. Do not merge by name, PLZ4, ZIP_ID or municipality; cross-postcode locality identity remains unreviewed."},
        "preparation_rules": [
            "Strict documented header/UTF-8/semicolon format. Preserve exact raw Unicode, whitespace, postcodes, additional numbers and identifier strings.",
            "Derived matching.locality_name uses boundary trim, Unicode NFC then casefold; matching.postcode uses boundary trim only. No numeric postcode conversion, format resolver, split multilingual names, translations or aliases.",
            "Retain municipality/BFS/canton labels to preserve source associations and enable later human disambiguation; municipality is not locality.",
            "Every data record is included, excluded blank or unresolved with reason; source_record links back to the exact pinned CSV record.",
            "Conflicting country/name/postcode/additional values for one ZIP_ID remain unresolved. Different municipality/canton associations within CH are retained.",
            "Duplicate records remain included. Duplicate counts overlap: exact-source duplicates are also retained-association duplicates; neither count is an excluded disposition."],
        "counts": result["counts"], "excluded": result["excluded"],
        "unresolved": result["unresolved"], "duplicates": result["duplicates"],
        "structural_summary": {"country_association_counts": dict(sorted(Counter(row["country_code"] for row in result["rows"]).items())),
            "distinct_postal_ids": len(ids), "postal_ids_with_multiple_associations": sum(len(rows) > 1 for rows in ids.values()),
            "postal_ids_across_canton_labels": sum(len({row["administrative"]["canton"] for row in rows}) > 1 for rows in ids.values())},
        "coverage": {"countries": ["CH", "LI"],
            "scope": "Official localities/building-address postcodes; not all postal purposes.",
            "omissions": "Non-address/administrative postcode types, including PO-box/company/internal postcodes, are omitted; see publisher product FAQ and technical documentation."},
        "attribution": {"credit": "Federal Office of Topography swisstopo", "source_reference": PRODUCT,
            "terms_reference": TERMS, "terms_version": "1.3.2021",
            "basis": "Publisher OGD terms allow use, redistribution and processing with mandatory source credit. STAC labels the licence proprietary; no Creative Commons or endorsement claim is inferred.",
            "modification_notice": "Selected non-spatial association columns, derived country/matching keys and extraction provenance; excluded coordinates/address shares/language/validity. Source spelling and postal strings unchanged. Human factual/release review pending."},
        "outstanding_review": [
            "Approve source snapshot, field meanings and all association/country dispositions; automated checks are not factual or release approval.",
            "Review documented empty-canton LI derivation and retained municipal/canton labels, including cross-canton associations.",
            "No locality GUID in the CSV: determine whether/when reviewed locality identity across postal IDs is needed. No consolidation or resolver is authorized.",
            "Review coverage omissions, attribution/licensing basis and source-provided multilingual spellings; no qualified DE/FR/IT/EN linguistic acceptance.",
            "Any unresolved/duplicate ledgers require review; zero unresolved source records does not resolve these identity or release decisions.",
            "Activation, replacement and application integration each require explicit authorization."],
        "limitations": ["Reference presence does not prove delivery or service availability.",
            "Reference absence alone does not prove an entered locality is invalid.",
            "No geometry, full addresses, fuzzy matching, geocoding or runtime publisher request.",
            "Inactive preparation only; approved country artifacts, saved requests and immutable alternative evidence unchanged."],
        "preparation": {"script": str(Path(__file__).relative_to(Path.cwd())),
            "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "command": shlex.join(sys.orig_argv)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.write_bytes(output_bytes(manifest))
    print(json.dumps({"counts": result["counts"], "sha256": sha256(output).hexdigest(),
        "status": "draft", "runtime_use": False}, sort_keys=True))


if __name__ == "__main__":
    main()
