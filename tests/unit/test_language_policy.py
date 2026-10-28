from dataclasses import replace

import pytest

from app.domain.interpretation import (
    Clause, ContractViolation, GroundedValue, InterpretationResult, LanguageOutcome,
    MeaningItem, OriginalSpan, Quantity, Recognition, apply_language_policy,
)


def span(text, quote):
    start = text.index(quote)
    return OriginalSpan(start, start + len(quote), quote)


def request(text="Velo", language=None, status="unknown"):
    item = MeaningItem("subject", "subject", "bicycle", OriginalSpan(0, len(text), text))
    return InterpretationResult(text, Recognition(status, language, "synthetic-recognition"), "understood",
        (Clause(item.span, "understood", "bicycle", (item.id,)),), (item,), "synthetic-meaning")


@pytest.mark.parametrize("language", ["de", "fr", "it", "en"])
def test_clear_input_uses_interpreter_original_language_not_normalized_english_or_browser(language):
    result = apply_language_policy(request("Synthetic original input", language, "supported"), {"browser_language": "it"})
    assert result.request_language == result.explanation_language == language
    assert result.language_origin == "detected"
    assert result.provenance["clauses"][0]["normalized"] == "bicycle"


@pytest.mark.parametrize("context,language,origin", [
    ({"preferred_language": "fr", "browser_language": "de"}, "fr", "user_choice"),
    ({"browser_language": "de"}, "de", "browser_preference"),
    ({"explanation_language_choice": "it", "preferred_language": "fr", "browser_language": "de"}, "it", "user_choice"),
])
@pytest.mark.parametrize("status", ["unknown", "mixed"])
def test_shared_or_balanced_input_uses_preference_order_without_detected_language(context, language, origin, status):
    result = apply_language_policy(request(status=status), context)
    assert result.explanation_language == language
    assert result.language_origin == origin
    assert result.request_language is None


@pytest.mark.parametrize("context", [{}, {"browser_language": "es"}, {"browser_language": "fr-CH"}])
def test_no_supported_preference_prompts_once_without_forced_english_or_country_fallback(context):
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(request(), context)
    assert caught.value.outcome == "clarification_required"
    assert caught.value.code == "explanation_language_required"
    assert caught.value.detail["clarification"]["choices"] == ["de", "fr", "it", "en"]


def test_explicit_correction_overrides_clear_language_without_changing_original_hypothesis():
    result = apply_language_policy(request(language="fr", status="supported"), {"explanation_language_choice": "en"})
    assert result.request_language == "fr"
    assert result.explanation_language == "en"
    assert result.language_origin == "user_choice"


def mixed():
    text = "Please repair my bicycle, sans remplacement"
    items = (
        MeaningItem("subject", "subject", "bicycle", span(text, "bicycle")),
        MeaningItem("constraint", "constraint", "no_replacement", span(text, "sans remplacement"), negation=span(text, "sans")),
    )
    split = text.index("sans")
    clauses = (Clause(OriginalSpan(0, split, text[:split]), "understood", "repair bicycle", ("subject",)),
        Clause(OriginalSpan(split, len(text), text[split:]), "understood", "without replacement", ("constraint",)))
    return InterpretationResult(text, Recognition("mixed", "en", "synthetic"), "understood", clauses, items, "synthetic")


def test_all_mixed_clauses_and_negation_survive_normalization():
    result = apply_language_policy(mixed(), {"browser_language": "de"})
    assert result.explanation_language == "en"
    assert result.constraints[0].value == "no_replacement"
    assert result.constraints[0].quote == "sans remplacement"
    assert result.provenance["items"][1]["negation"]["quote"] == "sans"
    assert len(result.provenance["clauses"]) == 2


@pytest.mark.parametrize("mutation", ["missing_clause", "missing_item", "unreferenced_item", "altered_quote", "wrong_offset", "missing_negation", "overlap"])
def test_demonstrated_clause_or_span_loss_is_a_contract_failure(mutation):
    original = mixed()
    if mutation == "missing_clause":
        changed = replace(original, clauses=original.clauses[:1])
    elif mutation == "missing_item":
        changed = replace(original, items=original.items[:1])
    elif mutation == "unreferenced_item":
        changed = replace(original, clauses=(original.clauses[0], replace(original.clauses[1], item_ids=())))
    elif mutation == "overlap":
        changed = replace(original, clauses=(*original.clauses, original.clauses[0]))
    else:
        item = original.items[1]
        if mutation == "altered_quote":
            item = replace(item, span=replace(item.span, quote="replacement allowed"))
        elif mutation == "wrong_offset":
            item = replace(item, span=replace(item.span, start=0))
        else:
            item = replace(item, negation=OriginalSpan(0, 4, "sans"))
        changed = replace(original, items=(original.items[0], item))
    with pytest.raises(ContractViolation):
        apply_language_policy(changed, {})


@pytest.mark.parametrize("state,outcome", [("needs_clarification", "clarification_required"), ("unsupported", "interpretation_unavailable")])
def test_one_unresolved_mixed_clause_cannot_be_dropped_even_with_supported_preference(state, outcome):
    result = mixed()
    result = replace(result, clauses=(result.clauses[0], replace(result.clauses[1], meaning_status=state)), message="Clarify this synthetic clause")
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(result, {"explanation_language_choice": "en"})
    assert caught.value.outcome == outcome


@pytest.mark.parametrize("recognition", [Recognition("supported", None, "synthetic"), Recognition("supported", "es", "synthetic"), Recognition("unsupported", "en", "synthetic"), Recognition("unknown", "fr", "synthetic")])
def test_inconsistent_language_hypotheses_are_adapter_contract_failures(recognition):
    with pytest.raises(ContractViolation):
        apply_language_policy(replace(request(), recognition=recognition), {"browser_language": "en"})


def test_unknown_label_does_not_prove_understanding_and_unsupported_needs_a_limitation():
    result = replace(request(), recognition=Recognition("unsupported", None, "synthetic"), meaning_status="unsupported")
    with pytest.raises(ContractViolation):
        apply_language_policy(result, {})
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(replace(result, message="Synthetic capability limitation; rephrase"), {})
    assert caught.value.outcome == "interpretation_unavailable"


def amount_packet(number_text="49,90", amount="49.90"):
    text = f"Repair Acme X-2 in Genève; budget {number_text} CHF per repair; do not replace it"
    number = span(text, number_text)
    basis = GroundedValue("per repair", span(text, "per repair"))
    quantity = Quantity(amount, number, ",", None, GroundedValue("CHF", span(text, "CHF")),
        GroundedValue("repair", basis.span), GroundedValue("once", basis.span), basis)
    items = (
        MeaningItem("subject", "subject", "bicycle", span(text, "Acme X-2")),
        MeaningItem("name", "name", "Acme X-2", span(text, "Acme X-2")),
        MeaningItem("place", "place", "Genève", span(text, "Genève")),
        MeaningItem("budget", "budget", "budget", span(text, f"{number_text} CHF per repair"), quantity=quantity),
        MeaningItem("constraint", "constraint", "no_replacement", span(text, "do not replace it"), negation=span(text, "not")),
    )
    return InterpretationResult(text, Recognition("supported", "en", "synthetic"), "understood",
        (Clause(OriginalSpan(0, len(text), text), "understood", "synthetic complete meaning", tuple(i.id for i in items)),), items, "synthetic")


def test_exact_amounts_units_names_and_original_unicode_spans_survive():
    result = apply_language_policy(amount_packet(), {})
    assert result.budget.amount == "49.90"
    assert (result.budget.currency, result.budget.unit, result.budget.period, result.budget.basis) == ("CHF", "repair", "once", "per repair")
    assert result.baseline is None
    assert result.goals == ()
    assert result.provenance["items"][2]["span"]["quote"] == "Genève"
    assert result.provenance["items"][3]["quantity"]["number"]["quote"] == "49,90"


@pytest.mark.parametrize("field", ["magnitude", "currency", "name", "unit_span"])
def test_demonstrated_protected_value_alteration_is_rejected(field):
    result = amount_packet()
    items = list(result.items)
    budget = items[3]
    if field == "magnitude":
        items[3] = replace(budget, quantity=replace(budget.quantity, amount="4990"))
    elif field == "currency":
        items[3] = replace(budget, quantity=replace(budget.quantity, currency=replace(budget.quantity.currency, value="EUR")))
    elif field == "name":
        items[1] = replace(items[1], normalized="Another product")
    else:
        items[3] = replace(budget, quantity=replace(budget.quantity, unit=GroundedValue("kg", OriginalSpan(0, 2, "kg"))))
    with pytest.raises(ContractViolation):
        apply_language_policy(replace(result, items=tuple(items)), {})


def test_unresolved_amount_requests_clarification_without_locale_guessing():
    result = amount_packet()
    budget = result.items[3]
    result = replace(result, items=(*result.items[:3], replace(budget, quantity=replace(budget.quantity, amount=None)), result.items[4]))
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(result, {"browser_language": "fr"})
    assert caught.value.code == "amount_uncertain"
    assert caught.value.detail["clarification"]["span"]["quote"] == "49,90"


@pytest.mark.parametrize("language", ["de", "fr", "it", "en"])
def test_ambiguous_1200_amount_never_uses_language_to_guess_magnitude(language):
    result = replace(amount_packet("1,200", None), recognition=Recognition("supported", language, "synthetic"))
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(result, {"explanation_language_choice": "en"})
    assert caught.value.code == "amount_uncertain"
    assert caught.value.detail["clarification"]["span"]["quote"] == "1,200"


def test_uncertain_cost_basis_precedes_explanation_language_choice():
    result = amount_packet()
    item = result.items[3]
    result = replace(result, recognition=Recognition("unknown", None, "synthetic"),
        items=(*result.items[:3], replace(item, quantity=replace(item.quantity, unit=None)), result.items[4]))
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(result, {})
    assert caught.value.code == "comparison_basis_uncertain"


def test_novel_subject_and_multiple_items_are_not_forced_into_a_known_catalogue():
    result = request("NovelWidget")
    result = replace(result, items=(replace(result.items[0], normalized=None),))
    assert apply_language_policy(result, {"browser_language": "en"}).subject == "NovelWidget"
    text = "bicycle and kettle"
    items = (MeaningItem("first", "subject", "bicycle", span(text, "bicycle")), MeaningItem("second", "subject", "kettle", span(text, "kettle")))
    result = replace(result, original_text=text, items=items,
        clauses=(Clause(OriginalSpan(0, len(text), text), "understood", "joint scope", ("first", "second")),))
    assert apply_language_policy(result, {"browser_language": "en"}).subjects == ("bicycle", "kettle")


def test_unmapped_explicit_requirement_is_not_ignored():
    result = mixed()
    result = replace(result, items=(result.items[0], replace(result.items[1], normalized=None)))
    with pytest.raises(LanguageOutcome) as caught:
        apply_language_policy(result, {})
    assert caught.value.outcome == "interpretation_unavailable"


def test_explicit_action_is_preserved_as_an_essential_requirement_without_inventing_a_goal():
    from app.domain.qualification import qualify
    from tests.support.synthetic import candidates, FIXTURE_TIME
    text = "Repair my bicycle"
    items = (MeaningItem("subject", "subject", "bicycle", span(text, "bicycle")),
        MeaningItem("action", "action", "repair", span(text, "Repair")))
    packet = InterpretationResult(text, Recognition("supported", "en", "synthetic"), "understood",
        (Clause(OriginalSpan(0, len(text), text), "understood", "repair bicycle", ("subject", "action")),), items, "synthetic")
    interpreted = apply_language_policy(packet, {})
    assert interpreted.actions == ("repair",)
    assert interpreted.goals == ()
    candidate = candidates()[0]
    assert qualify(candidate, interpreted, {"country_code": "CH"}, FIXTURE_TIME).qualified
    candidate = replace(candidate, claims=tuple(c for c in candidate.claims if c.key != "action:repair"))
    assert not qualify(candidate, interpreted, {"country_code": "CH"}, FIXTURE_TIME).qualified


def test_explicit_textual_locality_constraint_remains_essential_independently_of_location_fields():
    from app.domain.qualification import qualify
    from tests.support.synthetic import candidates, FIXTURE_TIME, represented_locality
    interpreted = apply_language_policy(represented_locality(), {})
    assert interpreted.constraints[0].quote == "in Genève"
    assert not qualify(candidates()[0], interpreted, {"country_code": "CH"}, FIXTURE_TIME).qualified
