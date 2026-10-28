from dataclasses import replace
from copy import deepcopy

import pytest

from app.application.comparisons import InputOutcome, digest
from app.application.rendering import SourceBoundRenderer, rendering_material
from app.domain.interpretation import apply_language_policy
from app.domain.qualification import qualify
from tests.support.source_bound_rendering import candidate, reviewed_artifacts
from tests.support.synthetic import EXAMPLE, FIXTURE_TIME, SyntheticInterpreter


def selected():
    interpretation = apply_language_policy(SyntheticInterpreter().interpret(EXAMPLE), {})
    return interpretation, qualify(candidate(), interpretation, {"country_code": "CH"}, FIXTURE_TIME)


@pytest.mark.parametrize("part", ["unit", "amount", "conditions", "quote", "review_date", "currency"])
def test_changed_source_or_protected_value_cannot_reuse_a_rendering_review(part):
    interpretation, result = selected()
    if part in ("unit", "amount", "currency"):
        claims = tuple(replace(c, value=replace(c.value, **{part: {"unit": "repair", "amount": "12.00", "currency": "EUR"}[part]}))
            if c.key == "financial" else c for c in result.candidate.claims)
        changed = replace(result.candidate, claims=claims)
    else:
        source = result.candidate.evidence[0]
        key = {"conditions": "scope", "quote": "supporting_quote", "review_date": "reviewed_at"}[part]
        source = replace(source, snapshot={**source.snapshot, key: "Changed synthetic content"})
        changed = replace(result.candidate, evidence=(source,))
    with pytest.raises(ValueError):
        SourceBoundRenderer(reviewed_artifacts(), allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME).prepare(
            interpretation, (replace(result, candidate=changed),))


def test_even_a_rebound_text_must_preserve_literal_money_and_all_required_fields():
    interpretation, result = selected()
    artifacts = reviewed_artifacts()
    artifact = next(a for a in artifacts if a["language"] == "en")
    artifact["content"]["presentation"]["financial"] = "Synthetic provider-stated rate: EUR 12.00 per repair."
    artifact["review"]["artifact_sha256"] = digest({k: v for k, v in artifact.items() if k != "review"})
    with pytest.raises(ValueError):
        SourceBoundRenderer(artifacts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME).prepare(interpretation, (result,))


def test_factual_review_is_not_a_language_review_and_fallback_is_explicit():
    interpretation, result = selected()
    artifacts = reviewed_artifacts()
    for a in artifacts:
        a["review"]["source"] = {"reviewer": "project owner", "review_date": "2026-10-18", "basis": "factual extraction only"}
    renderer = SourceBoundRenderer(artifacts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME)
    with pytest.raises(InputOutcome) as caught:
        renderer.prepare(interpretation, (result,))
    assert caught.value.code == "rendering_unavailable"
    with pytest.raises(InputOutcome):
        renderer.prepare_coverage(interpretation, ("no_retrieved_knowledge",))


def test_unqualified_candidate_cannot_be_promoted_by_reviewed_wording():
    interpretation, result = selected()
    with pytest.raises(ValueError):
        SourceBoundRenderer(reviewed_artifacts(), allow_synthetic_reviews=True).prepare(interpretation, (replace(result, qualified=False),))


def test_constructor_and_saved_output_do_not_alias_mutable_artifact_content():
    interpretation, result = selected()
    artifacts = reviewed_artifacts()
    renderer = SourceBoundRenderer(artifacts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME)
    artifacts[-1]["content"]["description"] = "Changed outside renderer"
    option = renderer.prepare(interpretation, (result,))[0]
    assert option.snapshot["description"] == "Synthetic bicycle repair."
    option.snapshot["rendering"]["review"]["status"] = "changed returned metadata"
    assert renderer.prepare(interpretation, (result,))[0].snapshot["rendering"]["review"]["status"] == "approved"
    assert digest(rendering_material(result)) == reviewed_artifacts()[-1]["material_sha256"]


def test_review_binds_source_meaning_while_qualification_keeps_request_specific_labels():
    interpretation, result = selected()
    snapshot = deepcopy(result.snapshot)
    snapshot["claims"][2]["requirement"] = "not_applicable"
    renderer = SourceBoundRenderer(reviewed_artifacts(), allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME)
    assert renderer.prepare(interpretation, (replace(result, snapshot=snapshot),))[0].snapshot["description"] == "Synthetic bicycle repair."


@pytest.mark.parametrize("field,value", [("reviewer", " "), ("reviewer", 123), ("basis", " "), ("basis", True)])
def test_review_requires_a_recorded_reviewer_and_nonblank_basis(field, value):
    interpretation, result = selected()
    artifacts = reviewed_artifacts()
    artifacts[-1]["review"]["target"][field] = value
    with pytest.raises(InputOutcome):
        SourceBoundRenderer(artifacts, allow_synthetic_reviews=True, clock=lambda: FIXTURE_TIME).prepare(interpretation, (result,))
