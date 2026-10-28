from hashlib import sha256
import json
from pathlib import Path
import unicodedata

import pytest

from app.application.localities import LocalityReferenceUnavailable
from app.infrastructure.locality_reference import LocalLocalityCatalogue


ROOT = Path(__file__).resolve().parents[2]
RELEASE = "swisstopo-chli-associations-2026-10-01-v1"
OUTPUT_SHA256 = "eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9"
CATALOGUE = ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01.json"
APPROVAL = ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-APPROVAL.json"
DRAFT = ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-DRAFT.json"
DRAFT_MANIFEST = ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-MANIFEST.json"


def test_approved_reference_preserves_every_pinned_association_and_identity_limit():
    catalogue = LocalLocalityCatalogue().load()

    assert sha256(CATALOGUE.read_bytes()).hexdigest() == OUTPUT_SHA256
    assert CATALOGUE.read_bytes() == DRAFT.read_bytes()
    assert catalogue.reference() == {"source": "swisstopo", "release": RELEASE,
        "sha256": OUTPUT_SHA256, "snapshot_at": "2026-10-01T00:00:00Z"}
    assert catalogue.supports("CH") and catalogue.supports("LI")
    assert not catalogue.supports("DE") and not catalogue.supports("ch")
    assert len(catalogue.matches("CH")) == 5696
    assert len(catalogue.matches("LI")) == 20
    assert tuple(sorted(catalogue.matches("CH") + catalogue.matches("LI"),
        key=lambda row: row["source_record"])) == tuple(json.loads(CATALOGUE.read_text()))


@pytest.mark.parametrize("country,town,postcode,record", [
    ("CH", unicodedata.normalize("NFD", "  JOUXTENS-MÉZERY  "), " 1008 ", 10),
    ("LI", "  vAdUz  ", " 9490 ", 5590),
])
def test_exact_matching_uses_country_normalized_source_name_and_string_postcode(country, town, postcode, record):
    catalogue = LocalLocalityCatalogue().load()

    result = catalogue.matches(country, town=town, postcode=postcode)

    assert len(result) == 1
    assert result[0]["source_record"] == record
    assert result[0]["country_code"] == country
    assert result[0]["postcode"] == postcode.strip()


def test_multiple_associations_remain_distinct_even_with_a_shared_postal_identifier():
    result = LocalLocalityCatalogue().load().matches("CH", town="Lausanne", postcode="1015")

    assert [row["source_record"] for row in result] == [15, 16, 17]
    assert {row["source_postcode_id"] for row in result} == {"163"}
    assert len({row["administrative"]["municipality_id"] for row in result}) == 3


@pytest.mark.parametrize("country,town,postcode", [
    ("CH", "Jouxtens-Mézery", "9490"), ("LI", "Jouxtens-Mézery", "1008"),
    ("CH", "Vaduz", "9490"), ("DE", "Vaduz", "9490"),
    ("CH", "Jouxtens-Mezery", "1008"), ("CH", "Jouxtens", "1008"),
    ("CH", "Jouxtens-Mézery", "01008"),
])
def test_no_intersection_outside_coverage_and_unpublished_aliases_return_no_match(country, town, postcode):
    assert LocalLocalityCatalogue().load().matches(country, town=town, postcode=postcode) == ()


def test_association_choice_contains_only_source_backed_pointer_and_necessary_labels():
    catalogue = LocalLocalityCatalogue().load()
    row, = catalogue.matches("CH", town="Jouxtens-Mézery", postcode="1008")
    pointer = {"source": "swisstopo", "release": RELEASE, "source_record": 10}

    choice = catalogue.association(row)

    assert choice == {"reference": pointer,
        **{key: row[key] for key in ("country_code", "locality_name", "postcode", "source_postcode_id",
            "additional_number", "administrative")}}
    assert catalogue.selected(pointer) == row
    assert "locality_id" not in choice and "matching" not in choice and "source_record" not in choice


@pytest.mark.parametrize("pointer", [
    None, {}, {"source": "swisstopo", "release": RELEASE},
    {"source": "other", "release": RELEASE, "source_record": 10},
    {"source": "swisstopo", "release": "older-release", "source_record": 10},
    {"source": "swisstopo", "release": RELEASE, "source_record": "10"},
    {"source": "swisstopo", "release": RELEASE, "source_record": True},
    {"source": "swisstopo", "release": RELEASE, "source_record": 0},
    {"source": "swisstopo", "release": RELEASE, "source_record": 999999},
    {"source": "swisstopo", "release": RELEASE, "source_record": 10, "locality_name": "edited"},
])
def test_selected_association_rejects_fabricated_stale_or_edited_pointers(pointer):
    assert LocalLocalityCatalogue().load().selected(pointer) is None


@pytest.mark.parametrize("change", ["draft", "unapproved", "missing", "changed_bytes", "wrong_release", "wrong_scope", "bad_attribution"])
def test_unusable_reference_is_configuration_failure_instead_of_a_successful_empty_lookup(tmp_path, change):
    manifest = json.loads(APPROVAL.read_text())
    raw = CATALOGUE.read_bytes()
    if change == "draft":
        manifest = json.loads(DRAFT_MANIFEST.read_text())
    elif change == "unapproved":
        manifest["approval"]["owner_approved"] = False
    elif change == "changed_bytes":
        rows = json.loads(raw)
        rows[0]["locality_name"] = "changed"
        raw = json.dumps(rows).encode()
        manifest["normalized_output"]["sha256"] = sha256(raw).hexdigest()
    elif change == "wrong_release":
        manifest["release_id"] = "unapproved-reference"
    elif change == "wrong_scope":
        manifest["approval"]["scope"] = "production"
    elif change == "bad_attribution":
        manifest["attribution"]["credit"] = 1
    manifest_path, catalogue_path = tmp_path / "approval.json", tmp_path / "associations.json"
    if change != "missing":
        manifest_path.write_text(json.dumps(manifest))
    catalogue_path.write_bytes(raw)

    with pytest.raises(LocalityReferenceUnavailable):
        LocalLocalityCatalogue(manifest_path, catalogue_path).load()
