import json
import sqlite3
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from app.application.comparisons import digest
from app.application.rendering import SourceBoundRenderer
from tests.integration.test_language_contract_api import payload, post
from tests.support.source_bound_rendering import create_service, reviewed_artifacts
from tests.support.synthetic import FIXTURE_TIME


@pytest.fixture
def system(tmp_path):
    path = tmp_path / "rendering.sqlite3"
    service = create_service(path)
    yield path, service
    service.store.engine.dispose()


def saved_rows(path):
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT projection FROM search_request ORDER BY rowid").fetchall()


@pytest.mark.parametrize("language", ["de", "fr", "it", "en"])
def test_reviewed_synthetic_rendering_is_saved_with_original_evidence_and_unknowns(system, language):
    path, service = system
    response = post(service, payload(context={"explanation_language_choice": language}))
    assert response.status_code == 201
    body = response.json()
    assert json.loads(saved_rows(path)[0][0]) == body
    option = body["comparison"]["options"][0]
    assert option["rendering"]["language"] == language
    assert option["rendering"]["review"]["synthetic"] is True
    assert "CHF 120.00" in option["presentation"]["financial"]
    assert option["financial"]["amount"] == "120.00"
    assert option["financial"]["unit"] == "workshop labour hour"
    assert option["financial"]["total_cost"] is option["financial"]["difference"] is None
    assert option["environmental"]["status"] == option["availability"]["status"] == "unknown"
    assert option["evidence"][0]["source_language"] == "de"
    assert option["evidence"][0]["reviewed_at"] == FIXTURE_TIME.isoformat()
    assert option["evidence"][0]["source_reference"] == "https://synthetic.example.invalid/hourly-repair-v1"


@pytest.mark.parametrize("change", ["pending", "missing_review", "unqualified_source", "unqualified_target", "day_only_review", "disabled", "missing_language"])
def test_missing_review_or_rendering_is_a_limitation_without_save(system, change):
    path, service = system
    artifacts = reviewed_artifacts()
    artifact = next(a for a in artifacts if a["language"] == "en")
    if change == "missing_review":
        del artifact["review"]
    elif change == "pending":
        artifact["review"]["status"] = "pending"
    elif change.startswith("unqualified"):
        artifact["review"][change.split("_")[1]]["qualified"] = False
    elif change == "day_only_review":
        artifact["review"]["target"]["reviewed_at"] = "2026-10-15"
    elif change == "disabled":
        artifact["runtime_use"] = False
    else:
        artifacts.remove(artifact)
    service = replace(service, renderer=SourceBoundRenderer(artifacts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME))
    response = post(service, payload())
    assert response.status_code == 200
    assert response.json()["outcome"] == "interpretation_unavailable"
    assert response.json()["issues"] == [{"code": "rendering_unavailable"}]
    assert "comparison" not in response.json()
    assert saved_rows(path) == []


@pytest.mark.parametrize("change", ["text", "version", "language", "evidence_ids", "material", "missing_conditions", "source_language", "duplicate"])
def test_stale_or_inconsistent_binding_is_a_processing_failure_without_save(system, change):
    path, service = system
    artifacts = reviewed_artifacts()
    artifact = next(a for a in artifacts if a["language"] == "en")
    if change == "text":
        artifact["content"]["presentation"]["financial"] = "CHF 120.00 total; saves money."
    elif change == "version":
        artifact["version"] = "unreviewed-v2"
    elif change == "language":
        artifact["review"]["target"]["languages"] = ["fr"]
    elif change == "evidence_ids":
        artifact["evidence_version_ids"] = ["changed-source"]
    elif change == "material":
        artifact["material_sha256"] = "0" * 64
    elif change == "missing_conditions":
        del artifact["content"]["presentation"]["conditions"]
    elif change == "source_language":
        artifact["review"]["source"]["languages"] = ["en"]
    else:
        artifacts.append(deepcopy(artifact))
    response = post(replace(service, renderer=SourceBoundRenderer(artifacts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME)), payload())
    assert response.status_code == 500
    assert response.json()["outcome"] == "processing_error"
    assert saved_rows(path) == []


def test_review_cannot_be_reused_after_source_change_or_be_treated_as_real_review(system):
    path, service = system
    response = post(replace(service, renderer=SourceBoundRenderer(reviewed_artifacts())), payload())
    assert response.json()["outcome"] == "interpretation_unavailable"
    from tests.support.source_bound_rendering import candidate
    changed = candidate()
    source = replace(changed.evidence[0], snapshot={**changed.evidence[0].snapshot, "supporting_quote": "Changed synthetic conditions"})

    class ChangedKnowledge:
        def retrieve(self, *args):
            return (replace(changed, evidence=(source,)),)

    response = post(replace(service, knowledge=ChangedKnowledge()), payload())
    assert response.status_code == 500
    assert saved_rows(path) == []


def test_source_bound_save_failure_rolls_back_and_later_artifact_edits_do_not_change_saved_text(system):
    path, service = system
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TRIGGER fail_rendered_save BEFORE INSERT ON request_alternative_evidence BEGIN SELECT RAISE(ABORT, 'synthetic'); END")
    response = post(service, payload(context={"explanation_language_choice": "fr"}))
    assert response.status_code == 503 and response.json()["persistence"]["state"] == "failed"
    assert saved_rows(path) == []
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM request_alternative").fetchone()[0] == 0
        connection.execute("DROP TRIGGER fail_rendered_save")
    body = post(service, payload(context={"explanation_language_choice": "fr"})).json()
    later = reviewed_artifacts()
    artifact = next(a for a in later if a["language"] == "fr")
    artifact["content"]["description"] = "Nouvelle formulation synthétique."
    artifact["version"] = "synthetic-hourly-fr-v2"
    artifact["review"]["artifact_sha256"] = digest({k: v for k, v in artifact.items() if k != "review"})
    changed = replace(service, renderer=SourceBoundRenderer(later, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME))
    updated = post(changed, payload(context={"explanation_language_choice": "fr"})).json()
    assert updated["comparison"]["options"][0]["description"] == "Nouvelle formulation synthétique."
    assert json.loads(saved_rows(path)[0][0]) == body


def test_real_packet_drafts_are_inactive_and_cannot_be_promoted_by_factual_approval(system):
    path, service = system
    document = json.loads(Path("docs/knowledge/UC-001-BICYCLE-REPAIR-CH-RENDERINGS.json").read_text())
    assert document["runtime_use"] is False
    assert document["source_packet"]["sha256"] == sha256(Path(document["source_packet"]["path"]).read_bytes()).hexdigest()
    assert {a["language"] for a in document["renderings"]} == {"de", "fr", "it", "en"}
    for artifact in document["renderings"]:
        assert artifact["review"]["status"] == "pending" and artifact["runtime_use"] is False
        assert artifact["review"]["source"]["qualified"] is False
        assert artifact["review"]["target"]["qualified"] is False
        assert artifact["material_sha256"] is None
    response = post(replace(service, renderer=SourceBoundRenderer(document["renderings"])), payload())
    assert response.json()["outcome"] == "interpretation_unavailable"
    assert saved_rows(path) == []
