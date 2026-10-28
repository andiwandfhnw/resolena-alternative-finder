from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.uc001_country_catalogue.prepare import catalogue_bytes, extract


HEADER = "\t".join(("#ISO", "ISO3", "ISO-Numeric", "fips", "Country", "Capital",
    "Area(in sq km)", "Population", "Continent", "tld", "CurrencyCode", "CurrencyName",
    "Phone", "Postal Code Format", "Postal Code Regex", "Languages", "geonameid",
    "neighbours", "EquivalentFipsCode"))
AN_NOTE = "# AN (the Netherlands Antilles) with geonameId = 8505032 was dissolved on 10 October 2010."
CS_NOTE = "# CS (Serbia and Montenegro) with geonameId = 8505033 no longer exists."
XK_NOTE = "# The countrycode XK temporarily stands for Kosvo:"


def row(code, name):
    fields = ["unused source value"] * 19
    fields[0], fields[4] = code, name
    fields[-1] = ""
    return "\t".join(fields)


def source(*rows, notes=()):
    return ("\n".join((*notes, HEADER, *rows)) + "\n").encode("utf-8")


def test_extract_retains_only_sorted_codes_and_exact_unicode_territory_names():
    raw = source(row("CH", "Switzerland"), row("BQ", "Bonaire, Saint Eustatius and Saba "),
        row("AX", "Åland Islands")).replace(b"\n", b"\r\n")

    result = extract(raw)

    assert result == {
        "countries": [{"code": "AX", "name": "Åland Islands"},
            {"code": "BQ", "name": "Bonaire, Saint Eustatius and Saba "},
            {"code": "CH", "name": "Switzerland"}],
        "source_rows": 3, "excluded": [], "unresolved": [],
        "preserved_edge_whitespace": [{"code": "BQ", "source_line": 3}],
    }


def test_catalogue_bytes_is_deterministic_unicode_json_with_a_final_newline():
    countries = extract(source(row("CH", "Switzerland"), row("AX", "Åland Islands")))["countries"]

    expected = ('[\n  {\n    "code": "AX",\n    "name": "Åland Islands"\n  },\n'
        '  {\n    "code": "CH",\n    "name": "Switzerland"\n  }\n]\n').encode("utf-8")

    assert catalogue_bytes(countries) == expected
    reordered = extract(source(row("AX", "Åland Islands"), row("CH", "Switzerland")))["countries"]
    assert catalogue_bytes(reordered) == expected


def test_extract_accounts_for_source_supported_exclusions_and_unresolved_code():
    result = extract(source(row("CH", "Switzerland"), row("CS", "Serbia and Montenegro"),
        row("AX", "Åland Islands"), row("XK", "Kosovo"), row("AN", "Netherlands Antilles"),
        notes=(AN_NOTE, CS_NOTE, XK_NOTE)))

    assert result["countries"] == [{"code": "AX", "name": "Åland Islands"},
        {"code": "CH", "name": "Switzerland"}]
    assert result["source_rows"] == 5
    assert len(result["countries"]) + len(result["excluded"]) + len(result["unresolved"]) == 5
    excluded = {item["code"]: item for item in result["excluded"]}
    assert set(excluded) == {"AN", "CS"}
    assert len(result["unresolved"]) == 1
    assert result["preserved_edge_whitespace"] == []
    for item, code, name, source_line, note_line, note in (
        (excluded["AN"], "AN", "Netherlands Antilles", 9, 1, AN_NOTE),
        (excluded["CS"], "CS", "Serbia and Montenegro", 6, 2, CS_NOTE),
        (result["unresolved"][0], "XK", "Kosovo", 8, 3, XK_NOTE),
    ):
        assert set(item) == {"code", "name", "source_line", "reason", "support"}
        assert (item["code"], item["name"], item["source_line"]) == (code, name, source_line)
        assert isinstance(item["reason"], str) and item["reason"].strip()
        assert item["support"] == {"line": note_line, "text": note}


@pytest.mark.parametrize("code,name", [("AN", "Netherlands Antilles"),
    ("CS", "Serbia and Montenegro"), ("XK", "Kosovo")])
def test_extract_requires_the_matching_source_note_for_disposition(code, name):
    with pytest.raises(ValueError):
        extract(source(row(code, name), notes=("# Unrelated source note.",)))


@pytest.mark.parametrize("raw", [
    pytest.param(b"", id="empty-input"),
    pytest.param((row("CH", "Switzerland") + "\n").encode(), id="missing-header"),
    pytest.param(source(row("CH", "Switzerland")).replace(b"Country", b"Country name", 1), id="mutated-header"),
    pytest.param(source(HEADER, row("CH", "Switzerland")), id="duplicate-header"),
    pytest.param(source("\t".join(row("CH", "Switzerland").split("\t")[:-1])), id="short-row"),
    pytest.param(source(row("CH", "Switzerland") + "\textra"), id="long-row"),
    pytest.param(source(row("ch", "Switzerland")), id="lowercase-code"),
    pytest.param(source(row("CHE", "Switzerland")), id="long-code"),
    pytest.param(source(row(" CH", "Switzerland")), id="padded-code"),
    pytest.param(source(row("CH", "")), id="empty-name"),
    pytest.param(source(row("CH", "  ")), id="blank-name"),
    pytest.param(source(row("CH", "Switzerland"), row("CH", "Other name")), id="duplicate-included-code"),
    pytest.param(source(row("AN", "Netherlands Antilles"), row("AN", "Other name"),
        notes=(AN_NOTE,)), id="duplicate-excluded-code"),
    pytest.param(source(row("XK", "Kosovo"), row("XK", "Other name"),
        notes=(XK_NOTE,)), id="duplicate-unresolved-code"),
])
def test_extract_rejects_malformed_source(raw):
    with pytest.raises(ValueError):
        extract(raw)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "build/uc001-priority5q-country-catalogue/source/countryInfo.txt"
ACQUISITION_PATH = ROOT / "build/uc001-priority5q-country-catalogue/source/acquisition.json"
DRAFT_PATH = ROOT / "docs/reference/COUNTRIES-GEONAMES-DRAFT.json"
DRAFT_MANIFEST_PATH = ROOT / "docs/reference/COUNTRIES-GEONAMES-MANIFEST.json"
SOURCE_HASH = "c55f638cfaafb4fe45a9aa15120a0f1f78e8a34a8e1847d7b9320cf740fbc9ab"
DRAFT_HASH = "28e22f26581779311af24f5963550f83c8594590c1edce03b25f6a37d6c03343"
APPROVAL_SCOPE = "Priority 5R development slice and isolated demo/test composition only"


def test_approved_extraction_resolves_xk_and_preserves_the_original_draft():
    raw = SOURCE_PATH.read_bytes()
    original_draft = DRAFT_PATH.read_bytes()

    result = extract(raw, approved_release=True)

    assert sha256(raw).hexdigest() == SOURCE_HASH
    assert sha256(original_draft).hexdigest() == DRAFT_HASH
    assert catalogue_bytes(extract(raw)["countries"]) == original_draft
    assert result["source_rows"] == 252
    assert len(result["countries"]) == len({item["code"] for item in result["countries"]}) == 250
    assert len(result["excluded"]) == 2
    assert {item["code"] for item in result["excluded"]} == {"AN", "CS"}
    assert result["unresolved"] == []
    assert {item["code"]: item["name"] for item in result["countries"]}["XK"] == "Kosovo"
    assert {item["code"]: item["name"] for item in result["countries"]}["BQ"] == "Bonaire, Saint Eustatius and Saba "
    assert catalogue_bytes([item for item in result["countries"] if item["code"] != "XK"]) == original_draft
    decision = result["decision_history"][0]
    assert decision["code"] == "XK"
    assert decision["previous_disposition"] == "unresolved"
    assert decision["previous_manifest"] == "docs/reference/COUNTRIES-GEONAMES-MANIFEST.json"
    assert decision["previous_decision"] == extract(raw)["unresolved"][0]
    assert decision["disposition"] == "included"
    assert decision["approved_on"] == "2026-10-23"
    assert "temporary/source-specific" in decision["limitation"]
    assert "official ISO assignment" in decision["limitation"]
    assert "political-status determination" in decision["limitation"]


@pytest.mark.parametrize("raw", [
    pytest.param(source(row("CH", "Switzerland")), id="different-source"),
    pytest.param(SOURCE_PATH.read_bytes().replace(b"Kosovo", b"Kosova", 1), id="modified-name"),
])
def test_approved_extraction_requires_the_owner_approved_source_pin(raw):
    with pytest.raises(ValueError, match="approved source pin"):
        extract(raw, approved_release=True)


def preparation_command(tmp_path, *, approved=False):
    command = [sys.executable, "scripts/uc001_country_catalogue/prepare.py",
        "--source", str(SOURCE_PATH.relative_to(ROOT)),
        "--acquisition", str(ACQUISITION_PATH.relative_to(ROOT)),
        "--source-sha256", SOURCE_HASH,
        "--output", str(tmp_path / "catalogue.json"),
        "--manifest", str(tmp_path / "manifest.json"),
        "--prepared-at", "2026-10-23T09:31:41+00:00"]
    if approved:
        command.append("--approved-release")
    return command


def test_explicit_approved_release_command_records_dated_scope_and_exact_provenance(tmp_path):
    original_manifest = DRAFT_MANIFEST_PATH.read_bytes()
    completed = subprocess.run(preparation_command(tmp_path, approved=True), cwd=ROOT,
        capture_output=True, text=True, check=False)

    assert completed.returncode == 0, completed.stderr
    output = (tmp_path / "catalogue.json").read_bytes()
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    prior = json.loads(original_manifest)
    assert manifest["status"] == "approved-development"
    assert manifest["runtime_use"] == "development-only"
    assert manifest["release_id"] == "geonames-countryInfo-2026-10-23-v1"
    assert manifest["approval"] == {
        "owner_approved": True, "approved_on": "2026-10-23", "approved_at": None,
        "scope": APPROVAL_SCOPE, "production_activation_approved": False,
        "independent_factual_review": False, "linguistic_approval": False,
        "basis": "Owner acceptance of the source-based catalogue policy and release basis; no independent factual verification of every entry or linguistic approval.",
    }
    assert manifest["review"]["owner_approved"] is True
    assert manifest["review"]["reviewed_at"] is None
    assert manifest["review"]["activation_approved"] is True
    assert manifest["review"]["activation_scope"] == APPROVAL_SCOPE
    assert manifest["counts"] == {"source_rows": 252, "included": 250, "excluded": 2, "unresolved": 0}
    assert manifest["raw_source"] == prior["raw_source"]
    assert manifest["retrieved_at"] == prior["retrieved_at"]
    assert manifest["publisher_HTTP_last_modified"] == prior["publisher_HTTP_last_modified"]
    assert manifest["source_release"] is manifest["source_publication_date"] is manifest["source_update_date"] is None
    assert manifest["prepared_at"] == "2026-10-23T09:31:41+00:00"
    assert manifest["normalized_output"]["sha256"] == sha256(output).hexdigest()
    assert manifest["normalized_output"]["bytes"] == len(output)
    assert manifest["normalized_output"]["fields"] == ["code", "name"]
    assert manifest["attribution"]["source_link"] == prior["attribution"]["source_link"]
    assert manifest["attribution"]["license"] == "CC BY 4.0"
    assert manifest["attribution"]["license_basis"] == prior["attribution"]["license_basis"]
    assert manifest["documentation"] == prior["documentation"]
    assert manifest["excluded"] == prior["excluded"]
    assert manifest["unresolved"] == []
    assert manifest["decision_history"][0]["previous_decision"] == prior["unresolved"][0]
    assert manifest["preserved_edge_whitespace"] == prior["preserved_edge_whitespace"]
    assert "--approved-release" in manifest["preparation"]["command"]
    assert manifest["preparation"]["script_sha256"] == sha256((ROOT / manifest["preparation"]["script"]).read_bytes()).hexdigest()
    assert DRAFT_MANIFEST_PATH.read_bytes() == original_manifest
    assert json.loads(completed.stdout)["counts"] == manifest["counts"]


def test_original_draft_command_remains_reproducible_after_release_support(tmp_path):
    original_manifest = DRAFT_MANIFEST_PATH.read_bytes()
    completed = subprocess.run(preparation_command(tmp_path), cwd=ROOT,
        capture_output=True, text=True, check=False)

    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "catalogue.json").read_bytes() == DRAFT_PATH.read_bytes()
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["status"] == "draft"
    assert manifest["runtime_use"] is False
    assert manifest["review"]["status"] == "pending"
    assert manifest["review"]["owner_approved"] is False
    assert manifest["review"]["activation_approved"] is False
    assert manifest["counts"] == {"source_rows": 252, "included": 249, "excluded": 2, "unresolved": 1}
    assert manifest["unresolved"] == json.loads(original_manifest)["unresolved"]
    assert "approval" not in manifest
    assert "release_id" not in manifest
    assert DRAFT_MANIFEST_PATH.read_bytes() == original_manifest
