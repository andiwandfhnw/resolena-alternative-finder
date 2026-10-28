import json
import sqlite3
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.interfaces.api import create_app
from app.domain.interpretation import Clause, InterpretationResult, MeaningItem, OriginalSpan, Recognition
from tests.support.synthetic import EXAMPLE, create_service


def span(text, quote):
    start = text.index(quote)
    return OriginalSpan(start, start + len(quote), quote)


def packet(text=EXAMPLE, language="en"):
    subject = MeaningItem("subject", "subject", "bicycle", span(text, "bicycle"))
    constraint = MeaningItem("constraint", "constraint", "no_replacement", span(text, "without replacing it"),
        negation=span(text, "without"))
    return InterpretationResult(text, Recognition("supported", language, "synthetic-original-input-v1"), "understood",
        (Clause(OriginalSpan(0, len(text), text), "understood", "Repair bicycle without replacement", ("subject", "constraint")),),
        (subject, constraint), "synthetic-meaning-v1")


class StubInterpreter:
    def __init__(self, result):
        self.result, self.calls = result, []

    def interpret(self, original_text):
        self.calls.append(original_text)
        return self.result


class StubRecognizer:
    def __init__(self, result):
        self.result, self.calls = result, []

    def recognize(self, original_text):
        self.calls.append(original_text)
        return self.result


def payload(text=EXAMPLE, context=None, country="CH"):
    return {"submission_key": str(uuid4()), "text": text, "search_location": {"country_code": country},
        "language_context": context or {}}


def post(service, body):
    with TestClient(create_app(service)) as client:
        return client.post("/api/comparisons", json=body, headers={"X-Submission-Proof": "a" * 64})


@pytest.fixture
def system(tmp_path):
    path = tmp_path / "language.sqlite3"
    service = create_service(path)
    yield path, service
    service.store.engine.dispose()


def assert_no_search(path):
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM search_request").fetchone()[0] == 0


def test_advisory_unsupported_hint_cannot_block_complete_interpretation_or_change_country(system):
    path, service = system
    interpreter = StubInterpreter(packet())
    recognizer = StubRecognizer(Recognition("unsupported", None, "synthetic-hint-v1"))
    response = post(replace(service, interpreter=interpreter, recognizer=recognizer), payload(context={"browser_language": "de"}))
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "comparison"
    assert body["language"]["explanation_language"] == "en"
    assert body["language"]["origin"] == "detected"
    assert interpreter.calls == recognizer.calls == [EXAMPLE]
    with sqlite3.connect(path) as connection:
        original, interpretation, location = connection.execute("SELECT original_text, interpretation, search_location FROM search_request").fetchone()
    saved = json.loads(interpretation)
    assert original == EXAMPLE
    assert json.loads(location) == {"country_code": "CH"}
    assert saved["provenance"]["recognizer_hypothesis"]["status"] == "unsupported"
    assert saved["provenance"]["recognition"]["language"] == "en"
    assert saved["provenance"]["items"][1]["negation"]["quote"] == "without"


@pytest.mark.parametrize("state,expected", [("needs_clarification", "clarification_required"), ("unsupported", "interpretation_unavailable")])
def test_supported_detector_label_cannot_promote_unresolved_or_unsupported_meaning(system, state, expected):
    path, service = system
    result = replace(packet(), meaning_status=state, message="Synthetic unresolved minority clause")
    class NeverRetrieve:
        def retrieve(self, *args):
            raise AssertionError("Unresolved meaning must not enter retrieval")

    response = post(replace(service, interpreter=StubInterpreter(result), knowledge=NeverRetrieve(),
        recognizer=StubRecognizer(Recognition("supported", "en", "synthetic-hint"))), payload())
    assert response.status_code == 200
    assert response.json()["outcome"] == expected
    assert response.json()["persistence"]["state"] == "not_attempted"
    assert_no_search(path)


def test_shared_subject_without_supported_preference_requests_one_time_choice(system):
    path, service = system
    text = "Velo"
    result = InterpretationResult(text, Recognition("unknown", None, "synthetic"), "understood",
        (Clause(OriginalSpan(0, 4, text), "understood", "bicycle", ("subject",)),),
        (MeaningItem("subject", "subject", "bicycle", OriginalSpan(0, 4, text)),), "synthetic-shared-v1")
    response = post(replace(service, interpreter=StubInterpreter(result)), payload(text))
    assert response.status_code == 200
    assert response.json()["outcome"] == "clarification_required"
    assert response.json()["clarification"]["choices"] == ["de", "fr", "it", "en"]
    assert_no_search(path)
    response = post(replace(service, interpreter=StubInterpreter(result)), payload(text, {"preferred_language": "en", "browser_language": "fr"}, "DE"))
    assert response.status_code == 201
    assert response.json()["outcome"] == "insufficient_coverage"
    assert response.json()["language"]["origin"] == "user_choice"
    with sqlite3.connect(path) as connection:
        assert json.loads(connection.execute("SELECT search_location FROM search_request").fetchone()[0]) == {"country_code": "DE"}


@pytest.mark.parametrize("part", ["interpreter", "recognizer"])
def test_actual_adapter_failure_is_processing_error_without_search(system, part):
    path, service = system

    class Broken:
        def interpret(self, original_text):
            raise RuntimeError("synthetic adapter fault")

        recognize = interpret

    service = replace(service, interpreter=StubInterpreter(packet()), **({"recognizer": Broken()} if part == "recognizer" else {}))
    if part == "interpreter":
        service = replace(service, interpreter=Broken())
    response = post(service, payload())
    assert response.status_code == 500
    assert response.json()["outcome"] == "processing_error"
    assert_no_search(path)


def test_dropped_clause_and_normalized_text_cannot_substitute_for_original_spans(system):
    path, service = system
    result = replace(packet(), original_text="Normalized English instead of the original input")
    response = post(replace(service, interpreter=StubInterpreter(result)), payload())
    assert response.status_code == 500
    assert response.json()["issues"] == [{"code": "interpretation_contract_invalid"}]
    assert_no_search(path)


def test_explicit_language_correction_does_not_fake_a_missing_target_renderer(system):
    path, service = system
    response = post(replace(service, interpreter=StubInterpreter(packet())), payload(context={"explanation_language_choice": "fr"}))
    assert response.status_code == 200
    assert response.json()["outcome"] == "interpretation_unavailable"
    assert response.json()["issues"] == [{"code": "rendering_unavailable"}]
    assert_no_search(path)


def test_original_amount_and_language_provenance_are_saved_with_a_coverage_outcome(system):
    from app.domain.interpretation import GroundedValue, Quantity
    path, service = system
    text = "Repair bicycle; budget 49,90 CHF per repair; without replacing it"
    quantity = Quantity("49.90", span(text, "49,90"), ",", None,
        GroundedValue("CHF", span(text, "CHF")), GroundedValue("repair", span(text, "per repair")),
        GroundedValue("once", span(text, "per repair")), GroundedValue("per repair", span(text, "per repair")))
    items = (MeaningItem("subject", "subject", "bicycle", span(text, "bicycle")),
        MeaningItem("budget", "budget", "budget", span(text, "49,90 CHF per repair"), quantity=quantity),
        MeaningItem("constraint", "constraint", "no_replacement", span(text, "without replacing it"), negation=span(text, "without")))
    result = InterpretationResult(text, Recognition("supported", "en", "synthetic"), "understood",
        (Clause(OriginalSpan(0, len(text), text), "understood", "synthetic complete scope", tuple(i.id for i in items)),), items, "synthetic")
    response = post(replace(service, interpreter=StubInterpreter(result)), payload(text))
    assert response.status_code == 201
    assert response.json()["outcome"] == "insufficient_coverage"  # quoted labour excludes unknown parts
    with sqlite3.connect(path) as connection:
        original, normalized, projection = connection.execute("SELECT original_text, interpretation, projection FROM search_request").fetchone()
    normalized = json.loads(normalized)
    assert original == text
    assert normalized["budget"]["amount"] == "49.90"
    assert normalized["budget"]["currency"] == "CHF"
    assert normalized["provenance"]["items"][1]["quantity"]["number"]["quote"] == "49,90"
    assert json.loads(projection) == response.json()


def test_rendered_language_must_match_selected_language_before_save(system):
    path, service = system

    class WrongLanguage:
        def prepare(self, interpretation, candidates):
            options = service.renderer.prepare(interpretation, candidates)
            return tuple(replace(option, snapshot={**option.snapshot, "rendering": {"language": "fr", "version": "fabricated"}}) for option in options)

    response = post(replace(service, interpreter=StubInterpreter(packet()), renderer=WrongLanguage()), payload())
    assert response.status_code == 500
    assert response.json()["outcome"] == "processing_error"
    assert_no_search(path)


def test_language_correction_cannot_reuse_a_committed_identity_with_changed_payload(system):
    path, service = system
    body = payload()
    assert post(service, body).status_code == 201
    body["language_context"] = {"explanation_language_choice": "fr"}
    assert post(service, body).status_code == 409
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM search_request").fetchone()[0] == 1


def test_normal_main_composition_imports_no_synthetic_language_adapters():
    import os
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-c", "import sys; from app.main import app; assert app.state.comparisons is None; assert not any(m.startswith('tests.support') for m in sys.modules)"],
        env={**os.environ, "PYTHONPATH": "src"}, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
