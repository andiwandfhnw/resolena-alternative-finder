import json
import sqlite3
from dataclasses import replace

import httpx
import pytest

from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter
from tests.integration.test_language_contract_api import payload, post
from tests.support.synthetic import EXAMPLE, create_service


NON_THINKING_PROMPT = "<|im_start|>synthetic<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def reference(quote, occurrence=1):
    return {"quote": quote, "occurrence": occurrence}


def wire(text=EXAMPLE, language="en", state="understood"):
    return {"recognition": {"status": "supported", "language": language}, "meaning_status": state,
        "clauses": [{"span": reference(text), "meaning_status": state,
            "normalized": "Repair bicycle without replacement", "item_ids": ["s", "a", "c"]}],
        "items": [
            {"id": "s", "kind": "subject", "normalized": "bicycle", "span": reference("bicycle"), "negation": None, "quantity": None},
            {"id": "a", "kind": "action", "normalized": "repair", "span": reference("Repair"), "negation": None, "quantity": None},
            {"id": "c", "kind": "constraint", "normalized": "no_replacement", "span": reference("without replacing it"),
             "negation": reference("without"), "quantity": None}], "message": None}


def envelope(value):
    return {"choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": json.dumps(value)}}],
        "usage": {"prompt_tokens": 200, "completion_tokens": 100}}


def mock_adapter(value, seen, *, completion_status=200):
    def handle(request):
        seen.append(request)
        if request.url.path == "/apply-template":
            return httpx.Response(200, json={"prompt": NON_THINKING_PROMPT})
        if request.url.path == "/tokenize":
            return httpx.Response(200, json={"tokens": [1] * 200})
        if request.url.path == "/v1/chat/completions":
            return httpx.Response(completion_status, json=envelope(value))
        raise AssertionError(request.url)
    return LlamaCppInterpreter("http://127.0.0.1:49188", "offline-test-secret", "offline test prompt", transport=httpx.MockTransport(handle))


@pytest.mark.parametrize("language,status,code", [("en", 201, None), ("fr", 200, "rendering_unavailable")])
def test_http_adapter_real_api_save_boundary_and_renderer_distinction(tmp_path, language, status, code):
    path = tmp_path / "http.sqlite3"
    service = create_service(path)
    seen = []
    with mock_adapter(wire(language=language), seen) as adapter:
        response = post(replace(service, interpreter=adapter), payload(context={"browser_language": "it"}, country="CH"))
    assert response.status_code == status
    if code:
        assert response.json()["issues"] == [{"code": code}]
    else:
        assert response.json()["outcome"] == "comparison"
    with sqlite3.connect(path) as connection:
        assert connection.execute("select count(*) from search_request").fetchone()[0] == (1 if status == 201 else 0)
    body = json.loads(seen[-1].content)
    assert body["messages"][-1] == {"role": "user", "content": EXAMPLE}
    assert "country" not in json.dumps(body) and "browser_language" not in json.dumps(body)
    assert all(r.headers["Authorization"] == "Bearer offline-test-secret" for r in seen)
    service.store.engine.dispose()


@pytest.mark.parametrize("mode,outcome,issue", [
    ("unsupported", "interpretation_unavailable", "interpretation_capability_unavailable"),
    ("ambiguous", "clarification_required", "meaning_uncertain"),
    ("malformed", "processing_error", "interpretation_contract_invalid"),
    ("fault", "processing_error", "comparison_processing_failed")])
def test_adapter_input_capability_and_technical_outcomes_are_unsaved(tmp_path, mode, outcome, issue):
    path = tmp_path / "outcomes.sqlite3"
    service = create_service(path)
    value = wire()
    if mode in ("unsupported", "ambiguous"):
        state = "unsupported" if mode == "unsupported" else "needs_clarification"
        value.update(meaning_status=state, message="Rephrase in DE/FR/IT/EN" if mode == "unsupported" else "Which meaning do you intend?")
        value["clauses"][0]["meaning_status"] = state
        value["recognition"] = {"status": "unsupported" if mode == "unsupported" else "unknown", "language": None}
    if mode == "malformed":
        value["original_text"] = "untrusted"
    with mock_adapter(value, [], completion_status=401 if mode == "fault" else 200) as adapter:
        response = post(replace(service, interpreter=adapter), payload())
    assert response.json()["outcome"] == outcome
    assert response.json()["issues"] == [{"code": issue}]
    with sqlite3.connect(path) as connection:
        assert connection.execute("select count(*) from search_request").fetchone()[0] == 0
    service.store.engine.dispose()


def test_velo_meaning_ambiguity_cannot_be_resolved_by_country_or_language_preferences(tmp_path):
    path = tmp_path / "velo.sqlite3"
    service = create_service(path)
    value = {"recognition": {"status": "unknown", "language": None}, "meaning_status": "needs_clarification",
        "clauses": [{"span": reference("Velo"), "meaning_status": "needs_clarification", "normalized": None, "item_ids": []}],
        "items": [], "message": "Do you mean a bicycle or a veil?"}
    with mock_adapter(value, []) as adapter:
        for country in ("CH", "IT"):
            response = post(replace(service, interpreter=adapter), payload("Velo", {"preferred_language": "en", "explanation_language_choice": "it"}, country))
            assert response.json()["issues"] == [{"code": "meaning_uncertain"}]
            assert response.json()["clarification"]["choices"] == []
    with sqlite3.connect(path) as connection:
        assert connection.execute("select count(*) from search_request").fetchone()[0] == 0
    service.store.engine.dispose()


def test_explicit_development_composition_has_no_recognizer_and_isolates_database(tmp_path):
    from pathlib import Path
    from uuid import uuid4
    from scripts.uc001_contract_check.development import create_development_app
    seen = []
    with mock_adapter(wire(), seen) as adapter:
        with pytest.raises(ValueError):
            create_development_app(tmp_path / "outside.sqlite3", adapter)
        path = Path("build/test-only") / f"offline-composition-{uuid4()}.sqlite3"
        app = create_development_app(path, adapter)
        try:
            assert app.state.comparisons.recognizer is None
            assert post(app.state.comparisons, payload()).status_code == 201
            with pytest.raises(ValueError):
                create_development_app(path, adapter)
        finally:
            app.state.comparisons.store.engine.dispose()
            path.unlink()
