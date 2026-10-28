from dataclasses import replace
from datetime import timedelta

import pytest

from app.domain.qualification import Claim, Money, assess_claim, qualify, cost_difference, value_data
from tests.support.synthetic import FIXTURE_TIME, candidates
from app.domain.comparison import Interpretation, QuotedConstraint


def interpretation(**changes):
    return replace(Interpretation("bicycle", (QuotedConstraint("no_replacement", "without replacing it"),),
        "en", "en", "detected", "synthetic"), **changes)


def assess(candidate=None, request=None, location=None, now=FIXTURE_TIME):
    return qualify(candidate or candidates()[0], request or interpretation(), location or {"country_code": "CH"}, now)


def change_claim(candidate, key, **changes):
    return replace(candidate, claims=tuple(replace(c, **changes) if c.key == key else c for c in candidate.claims))


def test_required_claims_and_optional_unknowns_are_independent():
    candidate = candidates()[0]
    assert assess(candidate).qualified
    for key in ("relevance", "applicability", "no_replacement"):
        missing = replace(candidate, claims=tuple(c for c in candidate.claims if c.key != key))
        assert not assess(missing).qualified
        assert not assess(change_claim(candidate, key, value=False)).qualified
    result = assess(candidate)
    assert result.snapshot["environmental"]["status"] == "unknown"
    assert result.snapshot["financial"]["amount"] == "45.00"
    assert not assess(request=interpretation(goals=("waterproof",))).qualified
    assert not assess(change_claim(candidate, "financial", specific=False)).qualified


@pytest.mark.parametrize("kind,days", [("price", 1), ("availability", 1), ("service_coverage", 90), ("specification", 365), ("environmental", 365)])
def test_elapsed_windows_expire_at_boundary(kind, days):
    candidate = candidates()[0]
    claim = replace(candidate.claims[0], kind=kind)
    evidence = tuple(replace(v, snapshot={**v.snapshot, "method": "synthetic", "baseline": "synthetic baseline",
        "assumptions": ["synthetic"], "data_period": "synthetic period", "temporal_applicability_reviewed": True}) for v in candidate.evidence)
    expiry = FIXTURE_TIME + timedelta(days=days)
    assert assess_claim(claim, evidence, expiry - timedelta(microseconds=1))["freshness"] == "fresh"
    for now in (expiry, expiry + timedelta(seconds=1)):
        assert assess_claim(claim, evidence, now)["freshness"] == "expired"


@pytest.mark.parametrize("metadata,expected", [
    ({"reviewed_at": None}, "unverified"),
    ({"reviewed_at": "2026-10-15"}, "unverified"),
    ({"reviewed_at": "2026-10-15T12:00:00+02:00"}, "fresh"),
    ({"reviewed_at": "2026-10-16T10:00:00+00:00"}, "unverified"),
    ({"expires_at": FIXTURE_TIME.isoformat()}, "expired"),
    ({"invalidated_at": FIXTURE_TIME.isoformat()}, "expired"),
    ({"publication_date": None, "retrieved_at": "2099-01-01"}, "fresh"),
])
def test_review_precision_expiry_and_separate_dates(metadata, expected):
    candidate = candidates()[0]
    evidence = replace(candidate.evidence[0], snapshot={**candidate.evidence[0].snapshot, **metadata})
    assert assess_claim(candidate.claims[0], (evidence,), FIXTURE_TIME)["freshness"] == expected


@pytest.mark.parametrize("metadata", [
    {"publisher": ""}, {"source_reference": ""}, {"supporting_quote": ""},
    {"competent_claims": []}, {"scope": {"country_code": "DE"}},
    {"assertions": {}},
])
def test_source_must_support_exact_claim_in_competence_and_scope(metadata):
    candidate = candidates()[0]
    evidence = replace(candidate.evidence[0], snapshot={**candidate.evidence[0].snapshot, **metadata})
    assert not assess(replace(candidate, evidence=(evidence,))).qualified


def test_conflicts_are_scope_aware_and_labels_do_not_promote_failed_requirements():
    candidate = candidates()[0]
    original = candidate.evidence[0]
    conflict = replace(original, version_id="conflict", snapshot={**original.snapshot,
        "assertions": {**original.snapshot["assertions"], "no_replacement": False}})
    failed = assess(replace(candidate, evidence=(original, conflict)))
    assert not failed.qualified
    label = next(c for c in failed.snapshot["claims"] if c["claim"] == "no_replacement")
    assert (label["support"], label["freshness"], label["requirement"]) == ("disputed", "fresh", "unverified")
    abroad = replace(conflict, snapshot={**conflict.snapshot, "scope": {"country_code": "DE"}})
    assert assess(replace(candidate, evidence=(original, abroad))).qualified
    contradiction = change_claim(candidate, "no_replacement", value=False)
    evidence = replace(original, snapshot={**original.snapshot, "assertions": {**original.snapshot["assertions"], "no_replacement": False}})
    result = assess(replace(contradiction, evidence=(evidence,)))
    label = next(c for c in result.snapshot["claims"] if c["claim"] == "no_replacement")
    assert (label["support"], label["freshness"], label["requirement"]) == ("supported", "fresh", "contradicted")


def test_country_and_intended_locality_require_independent_coverage():
    assert not assess(location={"country_code": "DE"}).qualified
    assert assess(location={"country_code": "CH", "town": "Intended synthetic town"}).qualified
    candidate = candidates()[0]
    scoped = change_claim(candidate, "applicability", scope={"country_code": "CH", "town": "Same name"})
    assert not assess(scoped, location={"country_code": "CH", "town": "Same name"}).qualified
    # Country-wide coverage is sufficient only without narrower conditions.
    scoped = change_claim(candidate, "applicability", scope={"country_code": "CH", "conditions": "non-electric only"})
    assert not assess(scoped).qualified


def test_optional_expiry_does_not_expire_other_claims_and_environment_requires_method_period():
    candidate = candidates()[0]
    result = assess(now=FIXTURE_TIME + timedelta(days=2))
    assert not result.qualified  # price was the only useful comparison dimension
    env = Claim("environmental", "Keeps the existing frame", "environmental", {"country_code": "CH"}, specific=True)
    source = candidate.evidence[0]
    source = replace(source, snapshot={**source.snapshot, "assertions": {**source.snapshot["assertions"], env.key: env.value},
        "competent_claims": [*source.snapshot["competent_claims"], env.key]})
    assert assess_claim(env, (source,), FIXTURE_TIME)["freshness"] == "unverified"
    source = replace(source, snapshot={**source.snapshot, "method": "synthetic reuse method", "baseline": "existing frame", "assumptions": ["synthetic same frame"],
        "data_period": "synthetic current period", "temporal_applicability_reviewed": True})
    candidate = replace(candidate, claims=(*candidate.claims, env), evidence=(source,))
    assert assess(candidate, now=FIXTURE_TIME + timedelta(days=2)).qualified


def money(amount="45.00", **changes):
    changes.setdefault("charges_known", True)
    return Money(amount, "CHF", "repair", "once", "total", **changes)


@pytest.mark.parametrize("field,value", [("currency", "EUR"), ("unit", "kg"), ("period", "month"), ("basis", "labour")])
def test_costs_require_comparable_supported_inputs(field, value):
    assert cost_difference(money(), replace(money("50.00"), **{field: value})) is None


def test_exact_amounts_unknown_charges_and_cheaper_requirement():
    assert cost_difference(money("0.10"), money("0.30")) == "0.20"
    assert cost_difference(money(), money("50.00", charges_known=False)) is None
    assert cost_difference(money(), None) is None
    assert not assess(request=interpretation(goals=("cheaper",), baseline=money("100.00"))).qualified
    with pytest.raises(ValueError):
        money("NaN")


def priced_candidate(price):
    candidate = change_claim(candidates()[0], "financial", value=price)
    source = candidate.evidence[0]
    return replace(candidate, evidence=(replace(source, snapshot={**source.snapshot,
        "assertions": {**source.snapshot["assertions"], "financial": value_data(price)}}),))


def test_supported_cost_comparison_and_budget_keep_basis_and_provenance():
    candidate = priced_candidate(money("49.90", assumptions=("one repair",)))
    request = interpretation(goals=("cheaper",), baseline=money("100.00"), budget=money("49.90"))
    result = assess(candidate, request=request)
    assert result.qualified
    assert result.snapshot["financial"]["difference"] == "50.10"
    assert result.snapshot["financial"]["baseline_provenance"] == "user-reported"
    assert not assess(candidate, request=replace(request, budget=money("49.89"))).qualified
    assert not assess(candidate, request=replace(request, baseline=replace(request.baseline, currency="EUR"))).qualified
    cheaper = next(label for label in result.snapshot["claims"] if label["claim"] == "cheaper")
    assert cheaper["requirement"] == "satisfied"


def test_other_market_optional_cost_is_unknown_and_cannot_satisfy_budget():
    candidate = priced_candidate(money())
    candidate = change_claim(candidate, "financial", scope={"country_code": "DE"})
    source = candidate.evidence[0]
    abroad = replace(source, version_id="abroad", snapshot={**source.snapshot, "scope": {"country_code": "DE"}})
    candidate = replace(candidate, evidence=(*candidate.evidence, abroad))
    result = assess(candidate, request=interpretation(budget=money("100.00")))
    assert not result.qualified
    assert result.snapshot["financial"]["amount"] is None


@pytest.mark.parametrize("kind", ["price", "service_coverage", "specification"])
def test_product_service_and_habit_applicability_use_claim_windows(kind):
    candidate = candidates()[0]
    candidate = change_claim(candidate, "applicability", kind=kind)
    assert assess(candidate).qualified


def test_optional_disputed_financial_information_can_leave_environmental_only_match():
    candidate = candidates()[0]
    env = Claim("environmental", "Synthetic frame reuse information", "environmental", {"country_code": "CH"}, specific=True)
    source = candidate.evidence[0]
    source = replace(source, snapshot={**source.snapshot, "assertions": {**source.snapshot["assertions"], "environmental": env.value},
        "competent_claims": [*source.snapshot["competent_claims"], "environmental"], "method": "synthetic method",
        "baseline": "synthetic frame", "assumptions": ["same frame"], "data_period": "synthetic period", "temporal_applicability_reviewed": True})
    conflict = replace(source, version_id="conflict", snapshot={**source.snapshot, "assertions": {"financial": {"amount": "999"}}})
    result = assess(replace(candidate, claims=(*candidate.claims, env), evidence=(source, conflict)))
    assert result.qualified
    assert result.snapshot["financial"]["status"] == "unknown"
    assert result.snapshot["environmental"]["status"] == "supported"


def test_narrow_locality_requires_identity_and_retains_geographic_limits():
    candidate = candidates()[0]
    scope = {"country_code": "CH", "town": "Synthetic town", "locality_identity_unambiguous": True}
    candidate = change_claim(candidate, "applicability", scope=scope)
    source = candidate.evidence[0]
    local = replace(source, version_id="local", snapshot={**source.snapshot, "scope": scope})
    candidate = replace(candidate, evidence=(*candidate.evidence, local))
    assert assess(candidate).qualified
    assert assess(candidate, location={"country_code": "CH", "town": "Synthetic town"}).qualified
    assert not assess(candidate, location={"country_code": "CH", "town": "Another place"}).qualified
    assert assess(candidate).snapshot["geographic_scope"] == scope


def test_exact_money_cannot_default_unknown_charges_to_zero():
    price = Money("10.00", "CHF", "repair", "once", "total")
    assert not price.charges_known
    assert cost_difference(price, money("20.00")) is None


def test_supported_component_price_is_not_an_invented_total_cost():
    result = assess(priced_candidate(replace(money(), basis="labour")))
    assert result.qualified
    assert result.snapshot["financial"]["amount"] == "45.00"
    assert result.snapshot["financial"]["total_cost"] is None


def test_comparison_requires_traceable_inputs_beyond_marketing():
    candidate = candidates()[0]
    claim = Claim("environmental", "Synthetic lower resource use", "environmental", {"country_code": "CH"}, specific=True, comparative=True)
    source = candidate.evidence[0]
    source = replace(source, snapshot={**source.snapshot, "assertions": {"environmental": claim.value},
        "competent_claims": ["environmental"], "method": "synthetic method", "baseline": "synthetic baseline",
        "assumptions": ["same function"], "data_period": "synthetic period", "temporal_applicability_reviewed": True})
    assert assess_claim(claim, (source,), FIXTURE_TIME)["support"] == "missing"
    inputs = (Claim("baseline_resource", "100 units", "environmental", claim.scope),
        Claim("alternative_resource", "50 units", "environmental", claim.scope))
    source = replace(source, snapshot={**source.snapshot, "assertions": {**source.snapshot["assertions"], **{c.key: c.value for c in inputs}},
        "competent_claims": ["environmental", *(c.key for c in inputs)]})
    claim = replace(claim, inputs=inputs)
    assert assess_claim(claim, (source,), FIXTURE_TIME)["support"] == "supported"
    assert assess_claim(claim, (source,), FIXTURE_TIME)["evidence_version_ids"] == [source.version_id]


def test_noncomparative_resource_information_does_not_invent_baseline_or_data_period():
    candidate = candidates()[0]
    claim = Claim("environmental", "Synthetic service retains the existing frame", "environmental", {"country_code": "CH"}, specific=True)
    source = candidate.evidence[0]
    source = replace(source, snapshot={**source.snapshot, "assertions": {**source.snapshot["assertions"], claim.key: claim.value},
        "competent_claims": [*source.snapshot["competent_claims"], claim.key],
        "data_period_required": False, "data_period_not_applicable_reason": "Current scoped service statement, no historical study inputs"})
    candidate = replace(candidate, evidence=(source,), claims=(*candidate.claims, claim))
    result = assess(candidate, request=interpretation(baseline=money("100.00")), now=FIXTURE_TIME + timedelta(days=2))
    assert result.qualified
    assert result.snapshot["environmental"]["status"] == "supported"
    assert result.snapshot["financial"]["status"] == "unknown"
    assert result.snapshot["financial"]["baseline"]["amount"] == "100.00"
    assert result.snapshot["financial"]["difference"] is None
