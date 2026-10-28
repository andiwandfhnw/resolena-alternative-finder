"""Opt-in Granite preparation; mocked checks do not verify a model or runtime."""

from copy import deepcopy
from hashlib import sha256
import json
import time
from urllib.parse import urlsplit

import httpx

from app.domain.interpretation import ContractViolation, InterpretationResult
from app.infrastructure.llama_cpp_interpreter import WireResult, decode_result, strict_json


def transport_schema(schema: dict | None = None) -> dict:
    source = deepcopy(WireResult.model_json_schema() if schema is None else schema)
    definitions = source.get("$defs", {})
    annotations = {"title", "description", "default", "examples", "$comment"}
    supported = {"type", "properties", "required", "additionalProperties", "items", "anyOf", "enum", "minLength", "minimum"}

    def inline(node, stack=()):
        if not isinstance(node, dict):
            raise ContractViolation("Interpretation schema node must be an object")
        if "$ref" in node:
            ref = node["$ref"]
            if (not isinstance(ref, str) or not ref.startswith("#/$defs/")
                    or set(node) - {"$ref"} - annotations):
                raise ContractViolation("Unsupported schema reference or reference sibling constraint")
            name = ref.removeprefix("#/$defs/")
            if name not in definitions or name in stack:
                raise ContractViolation("Missing or recursive interpretation schema reference")
            return inline(definitions[name], (*stack, name))
        unknown = set(node) - supported - annotations - {"$defs"}
        if unknown:
            raise ContractViolation("Unaccounted interpretation schema validation keyword")
        result = {key: deepcopy(value) for key, value in node.items() if key not in annotations and key != "$defs"}
        kind = result.get("type")
        if kind not in (None, "object", "array", "string", "integer", "boolean", "null"):
            raise ContractViolation("Unsupported interpretation schema type")
        if kind is None and "anyOf" not in result:
            raise ContractViolation("Unrestricted interpretation schema")
        if "properties" in result:
            if kind != "object" or "anyOf" in result or result.get("additionalProperties") is not False:
                raise ContractViolation("Interpretation objects must remain closed")
            properties = result["properties"]
            if not isinstance(properties, dict) or not isinstance(result.get("required"), list):
                raise ContractViolation("Malformed interpretation object schema")
            if any(name not in properties for name in result["required"]):
                raise ContractViolation("Interpretation required field is absent")
            result["properties"] = {key: inline(value, stack) for key, value in properties.items()}
        elif kind == "object":
            raise ContractViolation("Unrestricted interpretation object schema")
        if "items" in result:
            if kind != "array":
                raise ContractViolation("Unsupported interpretation array schema")
            result["items"] = inline(result["items"], stack)
        elif kind == "array":
            raise ContractViolation("Unrestricted interpretation array schema")
        if "anyOf" in result:
            if kind is not None or not isinstance(result["anyOf"], list) or not result["anyOf"]:
                raise ContractViolation("Unsupported interpretation union schema")
            result["anyOf"] = [inline(value, stack) for value in result["anyOf"]]
        if "minLength" in result and (kind != "string" or type(result["minLength"]) is not int):
            raise ContractViolation("Unsupported interpretation string constraint")
        if "minimum" in result and (kind != "integer" or type(result["minimum"]) is not int):
            raise ContractViolation("Unsupported interpretation numeric constraint")
        return result

    return inline(source)


def expected_prompt(system: str, original: str) -> str:
    return ("<|start_of_role|>system<|end_of_role|>" + system + "<|end_of_text|>\n"
        + "<|start_of_role|>user<|end_of_role|>" + original + "<|end_of_text|>\n"
        + "<|start_of_role|>assistant<|end_of_role|>")


class GraniteInterpreter:
    MODEL = "uc001-granite-3.3-8b-v1"
    MODEL_REVISION = "e40e9dd739c7be00fa965c16ce167088190ce114"
    RUNTIME_REVISION = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
    CONTEXT = 8192
    OUTPUT = 4096
    TIMEOUT = 120
    MAX_RESPONSE_BYTES = 262144
    REQUEST_SETTINGS = {
        "n_predict": OUTPUT, "temperature": 0.0, "dynatemp_range": 0.0, "seed": 42, "samplers": ["temperature"],
        "mirostat": 0, "adaptive_target": -1.0, "repeat_penalty": 1.0,
        "presence_penalty": 0.0, "frequency_penalty": 0.0, "dry_multiplier": 0.0,
        "n_keep": 0, "n_discard": 0, "ignore_eos": False, "stream": False,
        "stop": [], "logit_bias": [], "n_probs": 0, "grammar_lazy": False,
        "grammar_triggers": [], "timings_per_token": False, "post_sampling_probs": False,
        "backend_sampling": False, "lora": [], "reasoning_format": "none",
    }

    def __init__(self, endpoint: str, api_key: str, prompt: str, *, transport=None, before_generation=None, record=None):
        try:
            address = urlsplit(endpoint)
            valid = (address.scheme == "http" and address.hostname == "127.0.0.1" and address.port is not None
                and 0 < address.port < 65536 and address.path == "" and not address.query and not address.fragment
                and address.username is None and address.password is None
                and endpoint == f"http://127.0.0.1:{address.port}")
        except (AttributeError, TypeError, ValueError):
            valid = False
        if (not valid or not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in "\r\n")
                or not isinstance(prompt, str) or not prompt.strip()):
            raise ValueError("Explicit authenticated loopback endpoint and frozen system prompt required")
        self.prompt, self.schema = prompt, transport_schema()
        binding = {"prompt": prompt, "schema": self.schema, "model": self.MODEL_REVISION, "runtime": self.RUNTIME_REVISION}
        self.version = "granite-3.3-8b-contract-v1-" + sha256(json.dumps(binding, sort_keys=True,
            ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()[:16]
        self.before_generation, self.record = before_generation, record
        self.client = httpx.Client(base_url=endpoint, headers={"Authorization": "Bearer " + api_key},
            timeout=self.TIMEOUT, trust_env=False, follow_redirects=False, transport=transport)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.client.close()

    def _request(self, path: str, body: dict, deadline: float):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Granite interpretation deadline exceeded")
        with self.client.stream("POST", path, json=body, timeout=remaining) as response:
            response.raise_for_status()
            content = bytearray()
            for part in response.iter_bytes():
                content.extend(part)
                if len(content) > self.MAX_RESPONSE_BYTES or time.monotonic() > deadline:
                    raise ContractViolation("Granite response exceeds byte/deadline guard")
        return strict_json(bytes(content))

    @staticmethod
    def _setting_matches(actual, expected):
        if isinstance(expected, bool):
            return type(actual) is bool and actual == expected
        if isinstance(expected, int):
            return type(actual) is int and actual == expected
        if isinstance(expected, float):
            return type(actual) in (int, float) and actual == expected
        return type(actual) is type(expected) and actual == expected

    def interpret(self, original_text: str) -> InterpretationResult:
        if not isinstance(original_text, str) or not original_text.strip():
            raise ValueError("Original text must be an explicit nonblank string")
        deadline = time.monotonic() + self.TIMEOUT
        messages = [{"role": "system", "content": self.prompt}, {"role": "user", "content": original_text}]
        formatted = self._request("/apply-template", {"messages": messages,
            "chat_template_kwargs": {"thinking": False, "enable_thinking": False}, "add_generation_prompt": True}, deadline)
        rendered = expected_prompt(self.prompt, original_text)
        if not isinstance(formatted, dict) or formatted.get("prompt") != rendered:
            raise ContractViolation("Actual Granite rendering differs from the selected template expectation")
        tokenized = self._request("/tokenize", {"content": rendered, "add_special": False,
            "parse_special": True, "with_pieces": False}, deadline)
        tokens = tokenized.get("tokens") if isinstance(tokenized, dict) else None
        if (not isinstance(tokens, list) or not tokens or any(type(value) is not int or value < 0 for value in tokens)
                or len(tokens) + self.OUTPUT > self.CONTEXT):
            raise ContractViolation("Invalid tokenization or insufficient full Granite output reserve")
        body = {**deepcopy(self.REQUEST_SETTINGS), "prompt": tokens, "json_schema": self.schema,
            "cache_prompt": False, "return_tokens": True, "id_slot": 0, "n_cmpl": 1}
        if self.record:
            self.record("prompt_fit", {"prompt": rendered, "prompt_tokens": len(tokens), "output_allowance": self.OUTPUT})
        if self.before_generation:
            self.before_generation(original_text)
        if self.record:
            self.record("request", body)
        result = self._request("/completion", body, deadline)
        if self.record:
            self.record("response", result)
        try:
            settings, generated = result["generation_settings"], result["tokens"]
            actual, predicted = result["tokens_evaluated"], result["tokens_predicted"]
            if (type(result["index"]) is not int or result["index"] != 0 or type(result["id_slot"]) is not int
                    or result["id_slot"] != 0 or result["model"] != self.MODEL or result["stop"] is not True
                    or result["stop_type"] != "eos" or result["truncated"] is not False
                    or result["stopping_word"] != "" or result["prompt"] != rendered):
                raise ContractViolation("Granite native completion identity or termination differs")
            if (type(actual) is not int or actual != len(tokens) or type(predicted) is not int
                    or not 0 < predicted <= self.OUTPUT or actual + predicted > self.CONTEXT
                    or not isinstance(generated, list) or len(generated) != predicted
                    or any(type(value) is not int or value < 0 for value in generated)):
                raise ContractViolation("Granite native completion token accounting differs")
            if (not isinstance(settings, dict) or any(not self._setting_matches(settings.get(key), value)
                    for key, value in self.REQUEST_SETTINGS.items()) or settings.get("max_tokens") != self.OUTPUT
                    or settings.get("speculative.types") not in ("none", "none,none")
                    or not isinstance(settings.get("grammar"), str)
                    or not settings["grammar"].strip()):
                raise ContractViolation("Granite effective settings or grammar differ")
            if not isinstance(result["content"], str) or not result["content"].strip():
                raise ContractViolation("Granite raw content is absent")
            return decode_result(original_text, result["content"], self.version)
        except (KeyError, TypeError, IndexError) as error:
            raise ContractViolation("Malformed Granite native completion envelope") from error
