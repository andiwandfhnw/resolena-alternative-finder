import copy
import json

import httpx
import pytest

from app.domain.interpretation import ContractViolation, LanguageOutcome, apply_language_policy
from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter, decode_result, exact_span
from tests.integration.test_llama_contract_adapter_api import NON_THINKING_PROMPT, envelope, mock_adapter, reference, wire
from tests.support.synthetic import EXAMPLE


def test_exact_occurrences_use_original_unicode_codepoints_without_normalization():
    text = "🚲 vélo; vélo; e\u0301"
    assert exact_span(text, reference("vélo", 2)).start == 8
    assert exact_span(text, reference("e\u0301")).end == len(text)
    assert exact_span("aaa", reference("aa", 2)).start == 1  # overlapping occurrences count
    with pytest.raises(ContractViolation):
        exact_span("e\u0301", reference("é"))
    for value in [reference("vélo", 3), reference("vélo", 0), reference("", 1), reference("vélo", True)]:
        with pytest.raises(ContractViolation):
            exact_span(text, value)


@pytest.mark.parametrize("mutate", [
    lambda v: v.update(original_text="forged"), lambda v: v.update(version="forged"),
    lambda v: v["recognition"].update(version="forged"),
    lambda v: v["items"][0]["span"].update(occurrence="1"),
    lambda v: v["items"][0].update(normalized=3),
    lambda v: v["items"][0]["span"].update(quote="Bicycle"),
    lambda v: v["items"][2].update(negation=reference("Repair")),
    lambda v: v["clauses"][0].update(span=reference("Repair my bicycle")),
    lambda v: v["clauses"][0].update(item_ids=["s", "a"]),
    lambda v: v["recognition"].update(status="unsupported", language="en"),
    lambda v: v.update(meaning_status="unsupported", message=None)])
def test_strict_schema_and_domain_reject_detectable_contract_loss(mutate):
    value = wire()
    mutate(value)
    with pytest.raises(ContractViolation):
        decode_result(EXAMPLE, json.dumps(value))


@pytest.mark.parametrize("content", ['{} {}', '```json\n{}\n```', '{"a":NaN}', '{"meaning_status":"understood","meaning_status":"unsupported"}', '[]'])
def test_no_markdown_repair_duplicate_keys_nonfinite_or_trailing_json(content):
    with pytest.raises(ContractViolation):
        decode_result(EXAMPLE, content)


def quantity_wire(amount="49.90", number="49,90"):
    text = f"Repair bicycle; budget {number} CHF per repair"
    value = wire(text)
    value["items"] = value["items"][:2]
    value["items"].append({"id": "b", "kind": "budget", "normalized": "budget",
        "span": reference(f"{number} CHF per repair"), "negation": None,
        "quantity": {"amount": amount, "number": reference(number), "decimal_separator": ",", "grouping_separator": None,
            "currency": {"value": "CHF", "span": reference("CHF")},
            "unit": {"value": "repair", "span": reference("per repair")},
            "period": {"value": "once", "span": reference("per repair")},
            "basis": {"value": "per repair", "span": reference("per repair")}, "charges_known": False}})
    value["clauses"][0]["item_ids"] = ["s", "a", "b"]
    return text, value


def test_exact_quantity_mapping_and_original_currency_are_retained():
    text, value = quantity_wire()
    result = decode_result(text, json.dumps(value))
    assert result.original_text == text and result.version.startswith("qwen3-8b-contract-")
    money = apply_language_policy(result, {}).budget
    assert money.amount == "49.90" and money.currency == "CHF" and money.unit == "repair"
    for field, changed in [("amount", "49.9"), ("currency", {"value": "EUR", "span": reference("CHF")}), ("charges_known", "false")]:
        bad = copy.deepcopy(value)
        bad["items"][-1]["quantity"][field] = changed
        with pytest.raises(ContractViolation):
            decode_result(text, json.dumps(bad))


def test_ambiguous_amount_is_clarification_even_with_language_choice():
    text, value = quantity_wire(None, "1,200")
    result = decode_result(text, json.dumps(value))
    with pytest.raises(LanguageOutcome) as action:
        apply_language_policy(result, {"explanation_language_choice": "en"})
    assert action.value.code == "amount_uncertain"


def test_undetectable_semantic_omission_is_not_claimed_to_be_caught():
    value = wire()
    value["items"] = value["items"][:1]
    value["clauses"][0]["item_ids"] = ["s"]
    # Entire source is quoted but the action/negation was falsely declared represented.
    assert decode_result(EXAMPLE, json.dumps(value)).meaning_status == "understood"


@pytest.mark.parametrize("mutate", [lambda v: v["choices"][0].update(finish_reason="length"),
    lambda v: v["choices"].append(v["choices"][0]),
    lambda v: v["choices"][0]["message"].update(tool_calls=[{}]),
    lambda v: v["choices"][0]["message"].update(refusal="no"),
    lambda v: v["usage"].update(completion_tokens=3073)])
def test_bad_completion_envelope_stops_without_retry(mutate):
    result = envelope(wire())
    mutate(result)
    paths = []
    def handle(request):
        paths.append(request.url.path)
        if request.url.path == "/apply-template":
            return httpx.Response(200, json={"prompt": NON_THINKING_PROMPT})
        if request.url.path == "/tokenize":
            return httpx.Response(200, json={"tokens": [1] * 200})
        return httpx.Response(200, json=result)
    with LlamaCppInterpreter("http://127.0.0.1:49188", "test", "prompt", transport=httpx.MockTransport(handle)) as adapter:
        with pytest.raises(ContractViolation):
            adapter.interpret(EXAMPLE)
    assert paths.count("/v1/chat/completions") == 1


@pytest.mark.parametrize("mode", ["timeout", "redirect", "http", "overflow"])
def test_http_failure_or_prompt_overflow_does_not_generate_or_retry(mode):
    seen = []
    def handle(request):
        seen.append(request)
        if mode == "timeout":
            raise httpx.ReadTimeout("offline", request=request)
        if mode == "redirect":
            return httpx.Response(302, headers={"Location": "https://example.invalid"})
        if mode == "http":
            return httpx.Response(503)
        if request.url.path == "/apply-template":
            return httpx.Response(200, json={"prompt": NON_THINKING_PROMPT})
        return httpx.Response(200, json={"tokens": [1] * 5121})
    with LlamaCppInterpreter("http://127.0.0.1:49188", "test", "prompt", transport=httpx.MockTransport(handle)) as adapter:
        with pytest.raises((httpx.HTTPError, ContractViolation)):
            adapter.interpret(EXAMPLE)
    assert all(r.url.path != "/v1/chat/completions" for r in seen)


def test_proxy_environment_is_ignored_and_endpoint_is_literal_loopback(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://untrusted.invalid:9")
    monkeypatch.setenv("ALL_PROXY", "http://untrusted.invalid:9")
    with mock_adapter(wire(), []) as adapter:
        assert adapter.client.trust_env is False and adapter.client.follow_redirects is False
        adapter.interpret(EXAMPLE)
    for endpoint in ["http://localhost:49188", "https://127.0.0.1:49188", "http://example.com", "http://127.0.0.1:49188/path", "http://a:b@127.0.0.1:49188"]:
        with pytest.raises(ValueError):
            LlamaCppInterpreter(endpoint, "test", "prompt")


def test_template_must_establish_non_thinking_before_generation():
    calls = []
    def handle(request):
        calls.append(request.url.path)
        if request.url.path == "/apply-template":
            return httpx.Response(200, json={"prompt": "<|im_start|>assistant\n"})
        if request.url.path == "/tokenize":
            return httpx.Response(200, json={"tokens": [1] * 200})
        return httpx.Response(200, json=envelope(wire()))
    with LlamaCppInterpreter("http://127.0.0.1:49188", "test", "prompt", transport=httpx.MockTransport(handle)) as adapter:
        with pytest.raises(ContractViolation):
            adapter.interpret(EXAMPLE)
    assert "/v1/chat/completions" not in calls


def test_schema_request_uses_the_retained_pinned_server_envelope():
    with mock_adapter(wire(), []) as adapter:
        body = adapter.request_body(EXAMPLE)
        assert body["response_format"]["type"] == "json_object"
        assert body["response_format"]["schema"]["additionalProperties"] is False
        assert body["max_tokens"] == 3072 and body["cache_prompt"] is False
        assert body["chat_template_kwargs"] == {"enable_thinking": False}
