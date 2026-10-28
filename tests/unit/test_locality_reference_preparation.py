import csv
from hashlib import sha256
import io
import json
from pathlib import Path
import unicodedata
import zipfile

import pytest

from scripts.uc001_locality_reference.prepare import extract_csv, output_bytes


HEADER = ("Ortschaftsname", "PLZ4", "Zusatzziffer", "ZIP_ID", "Gemeindename", "BFS-Nr",
    "Kantonskürzel", "Adressenanteil", "E", "N", "Sprache", "Validity")
CH_CANTONS = set("AG AI AR BE BL BS FR GE GL GR JU LU NE NW OW SG SH SO SZ TG TI UR VD VS ZG ZH".split())
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "build/uc001-priority5t-locality-reference/source/ortschaftenverzeichnis_plz_2056.csv.zip"
SOURCE_SHA256 = "0903076e7c3b8670d836ec20d486f9d2045b120e61f07d27a2bd7be09443098b"
PROHIBITED = {"E", "N", "Adressenanteil", "Sprache", "Validity", "locality_id", "aliases",
    "coordinates", "geometry", "latitude", "longitude", "address", "language", "validity"}


def row(**changes):
    values = dict(zip(HEADER, ("Synthetic locality", "0123", "00", "012300", "Synthetic municipality",
        "0012", "GE", "DO-NOT-RETAIN-SHARE", "DO-NOT-RETAIN-E", "DO-NOT-RETAIN-N",
        "DO-NOT-RETAIN-LANGUAGE", "DO-NOT-RETAIN-VALIDITY"), strict=True))
    values.update(changes)
    return [values[key] for key in HEADER]


def export(*records, header=HEADER):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter=";", lineterminator="\r\n")
    writer.writerow(header)
    writer.writerows(records)
    return stream.getvalue().encode("utf-8-sig")


def expected_record(values, source_record):
    raw = dict(zip(HEADER, values, strict=True))
    return {"source_record": source_record, "country_code": "LI" if raw["Kantonskürzel"] == "" else "CH",
        "locality_name": raw["Ortschaftsname"], "postcode": raw["PLZ4"],
        "source_postcode_id": raw["ZIP_ID"], "additional_number": raw["Zusatzziffer"],
        "administrative": {"municipality_name": raw["Gemeindename"], "municipality_id": raw["BFS-Nr"],
            "canton": raw["Kantonskürzel"]},
        "matching": {"locality_name": unicodedata.normalize("NFC", raw["Ortschaftsname"].strip()).casefold(),
            "postcode": raw["PLZ4"].strip()}}


def assert_no_prohibited_fields(value):
    if isinstance(value, dict):
        assert not PROHIBITED.intersection(value)
        for child in value.values():
            assert_no_prohibited_fields(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_prohibited_fields(child)


def test_exact_raw_unicode_postcodes_and_ids_remain_separate_from_matching_keys():
    original = row(Ortschaftsname="  Säntis e\u0301  ", PLZ4=" 0123 ", ZIP_ID="000123",
        Gemeindename="  Gemeinde é  ", **{"BFS-Nr": "0001"})
    raw = export(original)

    result = extract_csv(raw)

    assert result["rows"] == [expected_record(original, 1)]
    assert result["counts"] == {"source_records": 1, "included": 1, "excluded": 0, "unresolved": 0,
        "duplicate_source_records": 0, "duplicate_retained_associations": 0}
    assert result["rows"][0]["matching"] == {"locality_name": "säntis é", "postcode": "0123"}
    assert result["excluded"] == result["unresolved"] == result["duplicates"] == []
    output = output_bytes(result["rows"])
    assert isinstance(output, bytes) and output.endswith(b"\n")
    assert json.loads(output) == result["rows"]
    assert "Säntis e\u0301".encode() in output
    assert output == output_bytes(extract_csv(raw)["rows"])
    assert_no_prohibited_fields(result)
    assert "DO-NOT-RETAIN" not in json.dumps(result)


def test_documented_blank_canton_maps_to_LI_while_unknown_canton_is_unresolved():
    records = (row(**{"Kantonskürzel": "ZH"}),
        row(Ortschaftsname="Synthetic LI locality", ZIP_ID="012301", Zusatzziffer="01", **{"Kantonskürzel": ""}),
        row(Ortschaftsname="Unresolved locality", ZIP_ID="012302", Zusatzziffer="02", **{"Kantonskürzel": "XX"}))

    result = extract_csv(export(*records))

    assert result["rows"] == [expected_record(records[0], 1), expected_record(records[1], 2)]
    assert result["rows"][1]["country_code"] == "LI"
    assert result["rows"][1]["administrative"]["canton"] == ""
    assert result["counts"] == {"source_records": 3, "included": 2, "excluded": 0, "unresolved": 1,
        "duplicate_source_records": 0, "duplicate_retained_associations": 0}
    assert result["unresolved"][0]["source_record"] == 3
    assert result["unresolved"][0]["reason"].strip()


def test_multiple_postcode_name_and_municipality_associations_are_never_flattened():
    records = (row(), row(ZIP_ID="012301", Zusatzziffer="01"),
        row(Ortschaftsname="Another locality", ZIP_ID="012302", Zusatzziffer="02"),
        row(Gemeindename="Second municipality", **{"BFS-Nr": "0099", "Kantonskürzel": "VD"}),
        row(PLZ4="0124", ZIP_ID="012400"))

    result = extract_csv(export(*records))

    assert result["rows"] == [expected_record(record, number) for number, record in enumerate(records, 1)]
    assert result["counts"] == {"source_records": 5, "included": 5, "excluded": 0, "unresolved": 0,
        "duplicate_source_records": 0, "duplicate_retained_associations": 0}
    assert result["unresolved"] == result["excluded"] == result["duplicates"] == []
    assert len([item for item in result["rows"] if item["source_postcode_id"] == "012300"]) == 2
    assert {item["postcode"] for item in result["rows"] if item["locality_name"] == "Synthetic locality"} == {"0123", "0124"}


def test_exact_and_discarded_column_duplicates_are_retained_with_overlapping_accounting():
    first = row()
    changed_discarded_columns = row(Adressenanteil="different discarded share", E="different discarded E",
        N="different discarded N", Sprache="different discarded language", Validity="different discarded date")

    result = extract_csv(export(first, first, changed_discarded_columns))

    assert result["rows"] == [expected_record(first, 1), expected_record(first, 2),
        expected_record(changed_discarded_columns, 3)]
    assert result["counts"] == {"source_records": 3, "included": 3, "excluded": 0, "unresolved": 0,
        "duplicate_source_records": 1, "duplicate_retained_associations": 2}
    assert result["duplicates"] == [
        {"source_record": 2, "same_as": 1, "kind": "exact_source_record"},
        {"source_record": 3, "same_as": 1, "kind": "same_retained_association"}]
    assert_no_prohibited_fields(result)
    assert "discarded" not in json.dumps(result)


def test_bad_data_records_are_fully_accounted_without_exporting_prohibited_values():
    required = ("Ortschaftsname", "PLZ4", "Zusatzziffer", "ZIP_ID", "Gemeindename", "BFS-Nr")
    records = [row(), [], row()[:-1], *(row(**{field: "  "}) for field in required),
        row(ZIP_ID="012399", **{"Kantonskürzel": "XX"})]

    result = extract_csv(export(*records))

    assert result["rows"] == [expected_record(records[0], 1)]
    assert result["counts"] == {"source_records": len(records), "included": 1, "excluded": 1,
        "unresolved": len(records) - 2, "duplicate_source_records": 0, "duplicate_retained_associations": 0}
    assert [item["source_record"] for item in result["excluded"]] == [2]
    assert {item["source_record"] for item in result["unresolved"]} == set(range(3, len(records) + 1))
    assert all(item["reason"].strip() for item in result["excluded"] + result["unresolved"])
    assert_no_prohibited_fields(result)
    assert "DO-NOT-RETAIN" not in json.dumps(result)


@pytest.mark.parametrize("changes", [
    {"Ortschaftsname": "Different locality"}, {"PLZ4": "9999"},
    {"Zusatzziffer": "99"}, {"Kantonskürzel": ""},
])
def test_conflicting_source_postcode_identity_keeps_every_group_record_unresolved(changes):
    independent = row(Ortschaftsname="Independent locality", ZIP_ID="012301", Zusatzziffer="01")

    result = extract_csv(export(row(), row(**changes), independent))

    assert result["rows"] == [expected_record(independent, 3)]
    assert result["counts"] == {"source_records": 3, "included": 1, "excluded": 0, "unresolved": 2,
        "duplicate_source_records": 0, "duplicate_retained_associations": 0}
    assert {item["source_record"] for item in result["unresolved"]} == {1, 2}
    assert all(item["reason"].strip() for item in result["unresolved"])
    assert_no_prohibited_fields(result)


@pytest.mark.parametrize("raw", [
    pytest.param(b"", id="empty-file"), pytest.param(export(), id="header-without-data"),
    pytest.param(b"\xff\xfe\xff", id="invalid-utf8"),
    pytest.param(export(row(), header=("Locality", *HEADER[1:])), id="renamed-column"),
    pytest.param(export(row(), header=tuple(reversed(HEADER))), id="reordered-columns"),
    pytest.param(export(row(), header=HEADER[:-1]), id="missing-column"),
    pytest.param(export(row()).replace(b";", b","), id="wrong-delimiter"),
])
def test_invalid_export_format_or_empty_export_is_rejected(raw):
    with pytest.raises(ValueError):
        extract_csv(raw)


def test_pinned_export_preserves_every_included_association_and_complete_source_accounting():
    archive = SOURCE.read_bytes()
    assert sha256(archive).hexdigest() == SOURCE_SHA256
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        members = [name for name in bundle.namelist() if name.lower().endswith(".csv")]
        assert len(members) == 1
        raw = bundle.read(members[0])
    records = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), delimiter=";"))
    assert tuple(records.pop(0)) == HEADER

    result = extract_csv(raw)

    assert result["counts"]["source_records"] == len(records)
    assert result["counts"]["included"] == len(result["rows"])
    assert result["counts"]["excluded"] == len(result["excluded"])
    assert result["counts"]["unresolved"] == len(result["unresolved"])
    assert len(records) == sum(result["counts"][key] for key in ("included", "excluded", "unresolved"))
    accounted = [item["source_record"] for key in ("rows", "excluded", "unresolved") for item in result[key]]
    assert sorted(accounted) == list(range(1, len(records) + 1))
    assert {item["country_code"] for item in result["rows"]} == {"CH", "LI"}
    for item in result["rows"]:
        original = records[item["source_record"] - 1]
        assert original[6] == "" or original[6] in CH_CANTONS
        assert item == expected_record(original, item["source_record"])
    included_records = {item["source_record"] for item in result["rows"]}
    assert all(item["source_record"] in included_records and item["same_as"] in included_records
        for item in result["duplicates"])
    assert result["counts"]["duplicate_source_records"] == sum(
        item["kind"] == "exact_source_record" for item in result["duplicates"])
    assert result["counts"]["duplicate_retained_associations"] == len(result["duplicates"])
    assert output_bytes(result["rows"]) == output_bytes(extract_csv(raw)["rows"])
    assert_no_prohibited_fields(result)
