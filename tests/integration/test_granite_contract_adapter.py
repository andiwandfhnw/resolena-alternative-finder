"""Prepared native responses and schema inspection only; no runtime/model verification."""

from copy import deepcopy
from dataclasses import replace
import json
import sqlite3
from types import SimpleNamespace

import httpx
import pytest

from app.domain.interpretation import ContractViolation
from app.infrastructure.granite_interpreter import GraniteInterpreter, expected_prompt, transport_schema
from app.infrastructure.llama_cpp_interpreter import WireResult
from tests.integration.test_language_contract_api import payload, post
from tests.integration.test_llama_contract_adapter_api import wire
from tests.support.synthetic import EXAMPLE, create_service


ENDPOINT = "http://127.0.0.1:9931"
PROMPT = "Offline mocked Granite contract instructions."
MOCK_TOKENS = list(range(64))


def completion(content=None):
    return {"index": 0, "id_slot": 0, "model": "uc001-granite-3.3-8b-v1", "stop": True,
        "content": json.dumps(wire()) if content is None else content,
        "tokens": [71, 72, 0], "tokens_predicted": 3, "tokens_evaluated": len(MOCK_TOKENS),
        "prompt": expected_prompt(PROMPT, EXAMPLE), "truncated": False,
        "stop_type": "eos", "stopping_word": "", "tokens_cached": 66,
        "generation_settings": {**deepcopy(GraniteInterpreter.REQUEST_SETTINGS),
            "max_tokens": 4096, "grammar": 'root ::= "mock grammar, not native conversion"',
            "reasoning_format": "none", "speculative.types": "none"}}


def mocked_adapter(seen, *, response=None, status=200, token_count=None, template=None, fault=None, **kwargs):
    def handle(request):
        seen.append(request)
        if request.url.path == "/apply-template":
            return httpx.Response(200, json={"prompt": expected_prompt(PROMPT, EXAMPLE) if template is None else template})
        if request.url.path == "/tokenize":
            return httpx.Response(200, json={"tokens": MOCK_TOKENS if token_count is None else list(range(token_count))})
        assert request.url.path == "/completion"
        if fault is not None:
            raise fault
        return httpx.Response(status, json=completion() if response is None else response,
            headers={"Location": "https://outside.invalid/completion"} if status == 307 else None)
    return GraniteInterpreter(ENDPOINT, "offline-test-secret", PROMPT,
        transport=httpx.MockTransport(handle), **kwargs)


def test_granite_native_request_keeps_raw_contract_and_explicit_version_through_api(tmp_path):
    path = tmp_path / "granite.sqlite3"
    service = create_service(path)
    seen, generations = [], []
    try:
        with mocked_adapter(seen, before_generation=generations.append) as adapter:
            response = post(replace(service, interpreter=adapter), payload(context={"browser_language": "it"}))
            version = adapter.version
        assert response.status_code == 201 and response.json()["outcome"] == "comparison"
        assert version.startswith("granite-3.3-8b-contract-v1-")
        assert generations == [EXAMPLE]
        assert [request.url.path for request in seen] == ["/apply-template", "/tokenize", "/completion"]
        assert all(request.headers["Authorization"] == "Bearer offline-test-secret" for request in seen)
        formatting = json.loads(seen[0].content)
        assert formatting["messages"] == [{"role": "system", "content": PROMPT}, {"role": "user", "content": EXAMPLE}]
        assert formatting["chat_template_kwargs"] == {"thinking": False, "enable_thinking": False}
        assert json.loads(seen[1].content) == {"content": expected_prompt(PROMPT, EXAMPLE),
            "add_special": False, "parse_special": True, "with_pieces": False}
        native = json.loads(seen[2].content)
        assert native["prompt"] == MOCK_TOKENS
        assert native["json_schema"] == transport_schema()
        assert native["n_predict"] == 4096 and native["temperature"] == 0 and native["seed"] == 42
        assert native["samplers"] == ["temperature"]
        assert native["dynatemp_range"] == 0.0
        assert native["n_cmpl"] == 1 and native["stream"] is False and native["cache_prompt"] is False
        assert "response_format" not in native and "country" not in json.dumps(native)
        assert "browser_language" not in json.dumps(native)
        with sqlite3.connect(path) as connection:
            original, interpretation = connection.execute("SELECT original_text,interpretation FROM search_request").fetchone()
        meaning = json.loads(interpretation)
        assert original == EXAMPLE
        assert meaning["version"] == version
        assert meaning["provenance"]["version"] == version
    finally:
        service.store.engine.dispose()


@pytest.mark.parametrize("mode", ["invalid_json", "fenced", "reasoning_wrapper", "bad_span", "unreferenced_meaning"])
def test_granite_rejects_raw_or_ungrounded_output_without_repair(mode):
    value = wire()
    if mode == "bad_span": value["items"][0]["span"]["quote"] = "invented bicycle"
    if mode == "unreferenced_meaning": value["clauses"][0]["item_ids"].remove("s")
    content = json.dumps(value)
    if mode == "invalid_json": content = '{"recognition":'
    if mode == "fenced": content = "```json\n" + content + "\n```"
    if mode == "reasoning_wrapper": content = "<think>hidden</think><response>" + content + "</response>"
    seen = []
    with mocked_adapter(seen, response=completion(content)) as adapter:
        with pytest.raises(ContractViolation): adapter.interpret(EXAMPLE)
    assert [request.url.path for request in seen].count("/completion") == 1


@pytest.mark.parametrize("mode", ["incomplete", "word_stop", "truncated", "wrong_settings", "wrong_prompt",
    "wrong_accounting", "wrong_model", "missing_grammar", "dynamic_temperature"])
def test_granite_rejects_native_termination_settings_and_accounting_violations(mode):
    response = completion()
    if mode == "incomplete": response["stop"] = False
    if mode == "word_stop": response["stop_type"] = "word"
    if mode == "truncated": response["truncated"] = True
    if mode == "wrong_settings": response["generation_settings"]["samplers"] = ["top_p", "temperature"]
    if mode == "wrong_prompt": response["prompt"] += "changed"
    if mode == "wrong_accounting": response["tokens_predicted"] = 4097
    if mode == "wrong_model": response["model"] = "another-model"
    if mode == "missing_grammar": response["generation_settings"]["grammar"] = ""
    if mode == "dynamic_temperature": response["generation_settings"]["dynatemp_range"] = 0.5
    seen = []
    with mocked_adapter(seen, response=response) as adapter:
        with pytest.raises(ContractViolation): adapter.interpret(EXAMPLE)
    assert len(seen) == 3


@pytest.mark.parametrize("endpoint", ["https://127.0.0.1:9931", "http://outside.invalid:9931", "http://user:secret@127.0.0.1:9931"])
def test_granite_rejects_nonexplicit_loopback_configuration(endpoint):
    with pytest.raises(ValueError): GraniteInterpreter(endpoint, "offline-secret", PROMPT)


@pytest.mark.parametrize("status", [307, 503])
def test_granite_transport_failures_remain_technical_and_never_retry(tmp_path, status):
    path = tmp_path / "technical.sqlite3"
    service = create_service(path)
    seen, generations = [], []
    try:
        with mocked_adapter(seen, status=status, before_generation=generations.append) as adapter:
            response = post(replace(service, interpreter=adapter), payload())
        assert response.status_code == 500
        assert response.json()["outcome"] == "processing_error"
        assert response.json()["persistence"] == {"state": "not_attempted"}
        assert len(seen) == 3 and generations == [EXAMPLE]
        with sqlite3.connect(path) as connection:
            assert connection.execute("SELECT COUNT(*) FROM search_request").fetchone()[0] == 0
    finally:
        service.store.engine.dispose()


def test_granite_reserves_full_output_and_rejects_template_drift_before_generation():
    for options, expected_calls in (({"token_count": 4097}, 2), ({"template": "<think>untrusted template"}, 1)):
        seen, generations = [], []
        with mocked_adapter(seen, before_generation=generations.append, **options) as adapter:
            with pytest.raises(ContractViolation): adapter.interpret(EXAMPLE)
        assert len(seen) == expected_calls and generations == []


def test_granite_source_justified_duplicate_none_specification_is_not_a_draft_model():
    response = completion()
    response["generation_settings"]["speculative.types"] = "none,none"
    with mocked_adapter([], response=response) as adapter:
        assert adapter.interpret(EXAMPLE).original_text == EXAMPLE
    response["generation_settings"]["speculative.types"] = "none,draft-simple"
    with mocked_adapter([], response=response) as adapter:
        with pytest.raises(ContractViolation): adapter.interpret(EXAMPLE)


def test_granite_timeout_remains_technical_with_one_generation_attempt(tmp_path):
    service = create_service(tmp_path / "timeout.sqlite3")
    seen, generations = [], []
    try:
        with mocked_adapter(seen, fault=httpx.ReadTimeout("offline timeout"), before_generation=generations.append) as adapter:
            response = post(replace(service, interpreter=adapter), payload())
        assert response.status_code == 500 and response.json()["outcome"] == "processing_error"
        assert len(seen) == 3 and generations == [EXAMPLE]
    finally:
        service.store.engine.dispose()


def test_granite_byte_limit_stops_before_generation(monkeypatch):
    seen, generations = [], []
    with mocked_adapter(seen, before_generation=generations.append) as adapter:
        monkeypatch.setattr(adapter, "MAX_RESPONSE_BYTES", 16)
        with pytest.raises(ContractViolation): adapter.interpret(EXAMPLE)
    assert len(seen) == 1 and generations == []


def test_granite_total_deadline_stops_before_a_request(monkeypatch):
    values = iter((0.0, 121.0))
    seen, generations = [], []
    with mocked_adapter(seen, before_generation=generations.append) as adapter:
        monkeypatch.setattr("app.infrastructure.granite_interpreter.time", SimpleNamespace(monotonic=lambda: next(values)))
        with pytest.raises(TimeoutError): adapter.interpret(EXAMPLE)
    assert seen == generations == []


def test_granite_schema_inlines_only_finite_references_and_preserves_constraints():
    original = WireResult.model_json_schema()
    schema = transport_schema()
    assert "$ref" not in json.dumps(schema) and "$defs" not in schema
    assert "title" not in json.dumps(schema)
    assert schema["required"] == original["required"]
    assert schema["additionalProperties"] is False
    quote = schema["properties"]["clauses"]["items"]["properties"]["span"]
    assert quote["properties"]["quote"] == {"minLength": 1, "type": "string"}
    assert quote["properties"]["occurrence"] == {"minimum": 1, "type": "integer"}
    assert original == WireResult.model_json_schema()


@pytest.mark.parametrize("mode", ["unsupported", "recursive", "unrestricted"])
def test_granite_schema_rejects_unaccounted_validation_or_recursive_references(mode):
    schema = WireResult.model_json_schema()
    if mode == "unsupported": schema["$defs"]["Quote"]["properties"]["quote"]["pattern"] = "^x$"
    elif mode == "recursive": schema["$defs"]["Quote"]["properties"]["loop"] = {"$ref": "#/$defs/Quote"}
    else: schema = {}
    with pytest.raises(ContractViolation): transport_schema(schema)
