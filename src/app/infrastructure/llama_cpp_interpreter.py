"""Opt-in local candidate adapter. JSON/grounding checks do not prove semantic fidelity."""

from hashlib import sha256
import json
import time
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain.interpretation import (
    Clause, ContractViolation, GroundedValue, InterpretationResult, MeaningItem,
    OriginalSpan, Quantity, Recognition,
)


class StrictWire(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Quote(StrictWire):
    quote: str = Field(min_length=1)
    occurrence: int = Field(ge=1)


class Value(StrictWire):
    value: str = Field(min_length=1)
    span: Quote


class WireQuantity(StrictWire):
    amount: str | None
    number: Quote
    decimal_separator: Literal[".", ","] | None
    grouping_separator: Literal[".", ",", "'", " ", "\u202f"] | None
    currency: Value | None
    unit: Value | None
    period: Value | None
    basis: Value | None
    charges_known: bool


class Item(StrictWire):
    id: str = Field(min_length=1)
    kind: Literal["subject", "action", "goal", "constraint", "name", "place", "budget", "baseline", "quantity", "context"]
    normalized: str | None
    span: Quote
    negation: Quote | None
    quantity: WireQuantity | None


State = Literal["understood", "needs_clarification", "unsupported"]


class WireClause(StrictWire):
    span: Quote
    meaning_status: State
    normalized: str | None
    item_ids: list[str]


class Hypothesis(StrictWire):
    status: Literal["supported", "unsupported", "mixed", "unknown"]
    language: Literal["de", "fr", "it", "en"] | None


class WireResult(StrictWire):
    recognition: Hypothesis
    meaning_status: State
    clauses: list[WireClause]
    items: list[Item]
    message: str | None


def strict_json(content: str | bytes):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ContractViolation("Duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_value):
        raise ContractViolation("Nonfinite JSON number")

    try:
        return json.loads(content, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ContractViolation("Invalid strict JSON") from error


def exact_span(original: str, value: dict | Quote) -> OriginalSpan:
    try:
        quote = Quote.model_validate(value) if isinstance(value, dict) else value
    except ValidationError as error:
        raise ContractViolation("Invalid original quotation reference") from error
    start = -1
    for _ in range(quote.occurrence):
        start = original.find(quote.quote, start + 1)
        if start == -1:
            raise ContractViolation("Quotation occurrence is absent from original input")
    return OriginalSpan(start, start + len(quote.quote), quote.quote)


def decode_result(original: str, content: str, version="qwen3-8b-contract-v1-offline") -> InterpretationResult:
    try:
        wire = WireResult.model_validate(strict_json(content))
    except ValidationError as error:
        raise ContractViolation("Invalid interpretation wire schema") from error
    span = lambda value: exact_span(original, value)

    def quantity(value):
        def grounded(field):
            return GroundedValue(field.value, span(field.span)) if field else None
        return Quantity(value.amount, span(value.number), value.decimal_separator, value.grouping_separator,
            *(grounded(getattr(value, field)) for field in ("currency", "unit", "period", "basis")), value.charges_known)

    result = InterpretationResult(original,
        Recognition(wire.recognition.status, wire.recognition.language, version), wire.meaning_status,
        tuple(Clause(span(c.span), c.meaning_status, c.normalized, tuple(c.item_ids)) for c in wire.clauses),
        tuple(MeaningItem(i.id, i.kind, i.normalized, span(i.span), span(i.negation) if i.negation else None,
            quantity(i.quantity) if i.quantity else None) for i in wire.items), version, wire.message)
    result.validate()
    return result


class LlamaCppInterpreter:
    CONTEXT = 8192
    OUTPUT = 3072
    TIMEOUT = 90
    MODEL = "uc001-qwen3-8b"
    SAMPLING = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "seed": 42}

    def __init__(self, endpoint: str, api_key: str, prompt: str, *, transport=None, before_generation=None, record=None):
        if endpoint != "http://127.0.0.1:49188" or not api_key or not prompt:
            raise ValueError("Explicit loopback endpoint, authentication and frozen prompt are required")
        self.prompt = prompt
        self.version = "qwen3-8b-contract-v1-" + sha256(prompt.encode()).hexdigest()[:16]
        self.before_generation, self.record = before_generation, record
        self.client = httpx.Client(base_url=endpoint, headers={"Authorization": "Bearer " + api_key},
            timeout=self.TIMEOUT, trust_env=False, follow_redirects=False, transport=transport)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.client.close()

    def request_body(self, original: str):
        return {"model": self.MODEL, "messages": [{"role": "system", "content": self.prompt}, {"role": "user", "content": original}],
            "response_format": {"type": "json_object", "schema": WireResult.model_json_schema()},
            "chat_template_kwargs": {"enable_thinking": False}, "max_tokens": self.OUTPUT,
            "stream": False, "cache_prompt": False, **self.SAMPLING}

    def _request(self, method, path, *, deadline, **kwargs):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Interpreter request deadline exceeded")
        with self.client.stream(method, path, timeout=remaining, **kwargs) as response:
            response.raise_for_status()
            content = bytearray()
            for part in response.iter_bytes():
                content.extend(part)
                if len(content) > 262144 or time.monotonic() > deadline:
                    raise ContractViolation("Interpreter response exceeds size/deadline guard")
        return strict_json(bytes(content))

    def prompt_fit(self, body, deadline):
        template = self._request("POST", "/apply-template", deadline=deadline,
            json={"messages": body["messages"], "chat_template_kwargs": body["chat_template_kwargs"], "add_generation_prompt": True})
        if not isinstance(template, dict) or not isinstance(template.get("prompt"), str):
            raise ContractViolation("Missing actual rendered prompt")
        if not template["prompt"].endswith("<think>\n\n</think>\n\n"):
            raise ContractViolation("Actual chat template does not establish non-thinking mode")
        tokens = self._request("POST", "/tokenize", deadline=deadline,
            json={"content": template["prompt"], "add_special": False, "parse_special": True, "with_pieces": False})
        values = tokens.get("tokens") if isinstance(tokens, dict) else None
        if not isinstance(values, list) or not values or any(type(v) is not int for v in values):
            raise ContractViolation("Invalid actual prompt token count")
        if len(values) + self.OUTPUT > self.CONTEXT:
            raise ContractViolation("Actual prompt plus full output allowance exceeds context")
        if self.record:
            self.record("prompt_fit", {"template": template, "prompt_tokens": len(values), "output_allowance": self.OUTPUT})
        return len(values)

    def interpret(self, original_text: str) -> InterpretationResult:
        deadline = time.monotonic() + self.TIMEOUT
        body = self.request_body(original_text)
        count = self.prompt_fit(body, deadline)
        if self.before_generation:
            self.before_generation(original_text)
        if self.record:
            self.record("request", body)
        response = self._request("POST", "/v1/chat/completions", deadline=deadline, json=body)
        if self.record:
            self.record("response", response)
        try:
            choices, usage = response["choices"], response["usage"]
            if len(choices) != 1 or choices[0]["index"] != 0 or choices[0]["finish_reason"] != "stop":
                raise ContractViolation("Completion was not a single complete response")
            message = choices[0]["message"]
            if (message["role"] != "assistant" or not isinstance(message["content"], str)
                    or message.get("tool_calls") or message.get("refusal") or message.get("reasoning_content")):
                raise ContractViolation("Unexpected completion message")
            actual, completed = usage["prompt_tokens"], usage["completion_tokens"]
            if (type(actual) is not int or actual != count or type(completed) is not int
                    or not 0 < completed <= self.OUTPUT or actual + completed > self.CONTEXT):
                raise ContractViolation("Actual usage differs from prompt fit/output guards")
            return decode_result(original_text, message["content"], self.version)
        except (KeyError, TypeError, IndexError) as error:
            raise ContractViolation("Malformed completion envelope") from error
