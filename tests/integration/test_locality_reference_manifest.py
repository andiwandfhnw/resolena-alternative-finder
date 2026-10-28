from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "build/uc001-priority5t-locality-reference"
SOURCE = EVIDENCE / "source/ortschaftenverzeichnis_plz_2056.csv.zip"
SOURCE_HASH = "0903076e7c3b8670d836ec20d486f9d2045b120e61f07d27a2bd7be09443098b"
MEMBER = "AMTOVZ_CSV_LV95/AMTOVZ_CSV_LV95.csv"


def preparation_command(tmp_path, *, source_hash=SOURCE_HASH, acquisition=None, approved=False):
    command = [sys.executable, "scripts/uc001_locality_reference/prepare.py",
        "--source", str(SOURCE.relative_to(ROOT)), "--source-sha256", source_hash,
        "--acquisition", str(acquisition or (EVIDENCE / "acquisition.json").relative_to(ROOT)),
        "--output", str(tmp_path / "draft.json"),
        "--manifest", str(tmp_path / "manifest.json"),
        "--prepared-at", "2026-10-23T17:20:00+00:00"]
    if approved:
        command.append("--approved-release")
    return command


def test_pinned_preparation_is_inactive_traceable_and_reproduces_exactly(tmp_path):
    command = preparation_command(tmp_path)
    first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    draft = (tmp_path / "draft.json").read_bytes()
    manifest_bytes = (tmp_path / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["status"] == "draft" and manifest["runtime_use"] is False
    assert manifest["review"] == {"status": "pending", "owner_approved": False,
        "activation_approved": False, "reviewer": None, "reviewed_at": None}
    assert manifest["raw_source"]["sha256"] == SOURCE_HASH == sha256(SOURCE.read_bytes()).hexdigest()
    with zipfile.ZipFile(SOURCE) as archive:
        member = archive.read(MEMBER)
    assert manifest["raw_source"]["member"] == {"path": MEMBER,
        "sha256": sha256(member).hexdigest(), "bytes": len(member)}
    assert manifest["normalized_output"]["sha256"] == sha256(draft).hexdigest()
    assert manifest["normalized_output"]["bytes"] == len(draft)
    assert manifest["prepared_at"] == "2026-10-23T17:20:00+00:00"
    assert manifest["source_dates"]["snapshot_at"] == "2026-10-01T00:00:00Z"
    assert manifest["source_dates"]["metadata_updated_at"] == "2026-10-01T04:45:13.574657Z"
    assert manifest["source_dates"]["publication_date"] is None
    assert manifest["source_dates"]["reviewed_at"] is None
    assert manifest["identity"]["locality_id_supplied"] is False
    assert manifest["identity"]["postal_id_column"] == "ZIP_ID"
    counts = manifest["counts"]
    assert counts["source_records"] == counts["included"] + counts["excluded"] + counts["unresolved"]
    assert counts["included"] == len(json.loads(draft))
    assert counts["excluded"] == len(manifest["excluded"])
    assert counts["unresolved"] == len(manifest["unresolved"])
    assert len(manifest["documentation"]) == 5
    for document in manifest["documentation"]:
        assert document["reference"].startswith("https://")
        raw = (ROOT / document["path"]).read_bytes()
        assert sha256(raw).hexdigest() == document["sha256"]
        assert len(raw) == document["bytes"]
    assert manifest["attribution"]["credit"] == "Federal Office of Topography swisstopo"
    assert "swisstopo.admin.ch" in manifest["attribution"]["terms_reference"]
    assert manifest["preparation"]["script_sha256"] == sha256(
        (ROOT / "scripts/uc001_locality_reference/prepare.py").read_bytes()).hexdigest()
    second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert (tmp_path / "draft.json").read_bytes() == draft
    assert (tmp_path / "manifest.json").read_bytes() == manifest_bytes


@pytest.mark.parametrize("changed_pin", ["source", "documentation"])
def test_preparation_rejects_unverified_input_pins_before_writing(tmp_path, changed_pin):
    acquisition = EVIDENCE / "acquisition.json"
    source_hash = SOURCE_HASH
    if changed_pin == "source":
        source_hash = "0" * 64
    else:
        records = json.loads(acquisition.read_text())
        document = next(item for item in records if item.get("HTTP_status") == 200
            and item["reference"].endswith("free-geodata-and-geoservices"))
        document["sha256"] = "0" * 64
        for item in records:
            if item.get("file"):
                item["file"] = str((EVIDENCE / item["file"]).resolve())
        acquisition = tmp_path / "altered-acquisition.json"
        acquisition.write_text(json.dumps(records))
    completed = subprocess.run(preparation_command(tmp_path, source_hash=source_hash,
        acquisition=acquisition), cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode != 0
    assert "hash mismatch" in completed.stderr
    assert not (tmp_path / "draft.json").exists()
    assert not (tmp_path / "manifest.json").exists()


def test_approved_release_retains_original_draft_bytes_and_records_dated_development_approval(tmp_path):
    draft_path = ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-DRAFT.json"
    prior_manifest = ROOT / "docs/reference/LOCALITIES-CH-LI-SWISSTOPO-2026-10-01-MANIFEST.json"
    before_draft, before_manifest = draft_path.read_bytes(), prior_manifest.read_bytes()
    command = preparation_command(tmp_path, approved=True)

    first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)

    assert first.returncode == 0, first.stderr
    raw = (tmp_path / "draft.json").read_bytes()
    manifest_bytes = (tmp_path / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    prior = json.loads(before_manifest)
    assert raw == before_draft
    assert sha256(raw).hexdigest() == "eb99e833904327d0c0c78b6a2f261fceaec76dad35e23926269c0096529824e9"
    assert manifest["release_id"] == "swisstopo-chli-associations-2026-10-01-v1"
    assert manifest["status"] == "approved-development" and manifest["runtime_use"] == "development-only"
    assert manifest["approval"]["owner_approved"] is True
    assert manifest["approval"]["approved_on"] == "2026-10-23"
    assert manifest["approval"]["approved_at"] is None
    assert manifest["approval"]["scope"] == "Priority 5U development slice and isolated demo/test composition only"
    assert manifest["approval"]["production_activation_approved"] is False
    assert manifest["approval"]["independent_factual_review"] is False
    assert manifest["approval"]["linguistic_approval"] is False
    assert manifest["review"]["owner_approved"] is True
    assert manifest["review"]["reviewed_at"] is None
    assert manifest["raw_source"] == prior["raw_source"]
    assert manifest["source_dates"] == prior["source_dates"]
    assert manifest["retrieved_at"] == prior["retrieved_at"]
    assert manifest["prepared_at"] == "2026-10-23T17:20:00+00:00"
    assert manifest["counts"] == prior["counts"]
    assert manifest["identity"] == prior["identity"]
    assert manifest["normalized_output"]["sha256"] == sha256(raw).hexdigest()
    assert manifest["draft_history"]["manifest"]["sha256"] == sha256(before_manifest).hexdigest()
    assert manifest["draft_history"]["output"]["sha256"] == sha256(before_draft).hexdigest()
    assert "--approved-release" in manifest["preparation"]["command"]
    second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    assert (tmp_path / "draft.json").read_bytes() == raw
    assert (tmp_path / "manifest.json").read_bytes() == manifest_bytes
    assert draft_path.read_bytes() == before_draft and prior_manifest.read_bytes() == before_manifest
