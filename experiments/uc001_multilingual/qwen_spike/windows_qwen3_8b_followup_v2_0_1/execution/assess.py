"""Codespace-only offline assessment of manually transferred synthetic responses."""
import argparse
import copy
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

from contract import canonical, semantic_score, validate

HERE = Path(__file__).resolve().parent
EQUIVALENTS = {"kettle": {"water_kettle", "bouilloire", "bollitore", "wasserkocher"},
    "repair": {"répare", "réparer", "ripara", "riparare", "repariere"}}

def classify(case, output):
    obj = copy.deepcopy(output)
    errors = validate(obj, case["text"])
    expected = case["expected"]
    semantic = []
    labels = {}
    uncertain = []
    if obj.get("status") != expected["status"]:
        semantic.append("status")
    if obj.get("language") != expected["language"]:
        semantic.append("language")
    if expected.get("unresolved_nonempty") and not obj.get("unresolved"):
        semantic.append("missing_uncertainty")
    if expected.get("uncertainty_terms") and not any(term.casefold() in str(obj.get("unresolved", [])).casefold() for term in expected["uncertainty_terms"]):
        semantic.append("uncertainty_target")
    for field in ["subject", "action"]:
        actual = canonical(obj.get(field, {}).get("value"))
        if expected["status"] == "understood":
            wanted = canonical(expected[field])
            if actual != wanted:
                labels[field] = {"expected": wanted, "actual": actual}
                if actual in EQUIVALENTS.get(wanted, set()):
                    uncertain.append(field + ": plausible equivalent label, not qualified linguistic validation")
                else:
                    semantic.append(field)
        else:
            allowed = expected.get("allowed_" + field + "s", [None, "kettle"] if field == "subject" else [None, "repair"])
            if actual not in allowed:
                semantic.append(field)
    goals = sorted(g.get("value") for g in obj.get("goals", []))
    constraints = {c["kind"]: c["value"] for c in obj.get("constraints", [])}
    if goals != sorted(expected.get("goals", [])):
        semantic.append("goals")
    if constraints != expected.get("constraints", {}):
        semantic.append("constraints")
    if len(obj.get("constraints", [])) != len(constraints):
        semantic.append("duplicate_constraint_kind")
    for literal in case.get("protected_literals", []):
        if literal not in json.dumps(obj.get("constraints", []), ensure_ascii=False):
            semantic.append("protected_literal:" + literal)
    score = semantic_score(copy.deepcopy(obj), expected)
    return {"strict_pass": not errors and not semantic and not labels,
        "semantic_errors": semantic, "grounding_errors": [e for e in errors if e in {"ungrounded_quote", "offset", "ambiguous_quote_occurrence"}],
        "validation_errors": errors, "label_mismatches": labels,
        "meaning_inconclusive": uncertain, "unchanged_scorer": score, "actual": obj,
        "classification": "AI-assisted exploratory, no independent linguistic validation"}

def schema_errors(obj, schema, path="root"):
    errors = []
    types = schema.get("type", [])
    if isinstance(types, str):
        types = [types]
    if types and not any({"object": isinstance(obj, dict), "array": isinstance(obj, list),
        "string": isinstance(obj, str), "null": obj is None}[t] for t in types):
        return [path + ":type"]
    if "enum" in schema and obj not in schema["enum"]:
        errors.append(path + ":enum")
    if isinstance(obj, dict) and schema.get("type") == "object":
        props = schema["properties"]
        errors += [path + ":missing:" + k for k in schema.get("required", []) if k not in obj]
        if schema.get("additionalProperties") is False:
            errors += [path + ":extra:" + k for k in obj if k not in props]
        for key in obj.keys() & props.keys():
            errors += schema_errors(obj[key], props[key], path + "." + key)
    if isinstance(obj, list) and schema.get("type") == "array":
        for index, item in enumerate(obj):
            errors += schema_errors(item, schema["items"], path + "." + str(index))
    return errors

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def assess_folder(results, known_only):
    from contract import SCHEMA
    freeze = json.loads((HERE / "freeze.json").read_text())
    for name, expected in freeze["files"].items():
        if sha(HERE / name) != expected:
            raise ValueError("Bundle changed: " + name)
    cfg = json.loads((HERE / "config.json").read_text())
    cases = json.loads((HERE / "cases.json").read_text())
    lookup = {c["id"]: c for c in cases["known_cases"] + cases["new_cases"]}
    plan = json.loads((HERE / "order.json").read_text())
    if known_only:
        plan = [p for p in plan if p["stage"] == "known"]
    evaluations = []
    failures = []
    receipt = {}
    for entry in plan:
        response_path = results / "responses" / (entry["id"] + ".json")
        request_path = results / entry["request"]
        if sha(request_path) != sha(HERE / entry["request"]):
            raise ValueError("Request changed: " + entry["id"])
        record = json.loads(response_path.read_text(encoding="utf-8-sig"))
        receipt[entry["id"]] = {"request_sha256": sha(request_path), "response_sha256": sha(response_path)}
        operational = []
        if record.get("http_status") != 200:
            operational.append("http_status")
        try:
            raw = json.loads(record["raw_body"])
            choice = raw["choices"][0]
            if choice.get("finish_reason") != "stop":
                operational.append("finish_reason")
            if choice["message"].get("reasoning_content"):
                operational.append("thinking_output")
            output = json.loads(choice["message"]["content"])
            shape = schema_errors(output, SCHEMA)
            result = classify(lookup[entry["case"]], output) if not shape else {"strict_pass": False, "schema_errors": shape}
            usage = raw.get("usage", {})
            timings = raw.get("timings", {})
            if timings.get("cache_n") != 0 or usage.get("prompt_tokens_details", {}).get("cached_tokens") != 0:
                operational.append("cache_not_confirmed_zero")
            if not usage or not timings:
                operational.append("missing_server_usage_or_timings")
            result.update(finish_reason=choice.get("finish_reason"), usage=usage, timings=timings)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            result = {"strict_pass": False, "parse_failure": str(error)}
        if record.get("bundle_freeze_sha256") != sha(HERE / "freeze.json"):
            operational.append("freeze_receipt")
        if record.get("wall_seconds", float("inf")) > cfg["limits"]["request_seconds"]:
            operational.append("request_timeout")
        result.update(id=entry["id"], stage=entry["stage"], operational_errors=operational, wall_seconds=record.get("wall_seconds"))
        result["strict_pass"] = result["strict_pass"] and not operational
        if not result["strict_pass"]:
            failures.append(entry["id"])
        evaluations.append(result)
    stderr = (results / "server.stderr.log").read_text(encoding="utf-8-sig", errors="replace")
    offloads = re.findall(r"offloaded (\d+)/(\d+) layers to GPU", stderr)
    full_offload = bool(offloads) and all(int(n) == int(total) and int(n) > 0 for n, total in offloads)
    samples = [json.loads(line) for line in (results / "resources.jsonl").read_text(encoding="utf-8-sig").splitlines() if line]
    measured = [s for s in samples if s.get("owned_gpu_bytes", 0) > 0]
    evidence_ok = full_offload and bool(measured) and not (results / "guard_failure.json").exists()
    if not evidence_ok:
        failures.append("gpu_or_guard_evidence")
    warm = [e["wall_seconds"] for e in evaluations[1:] if isinstance(e.get("wall_seconds"), (int, float))]
    latency = {"first_seconds": evaluations[0]["wall_seconds"], "warm_n": len(warm),
        "warm_median_seconds": statistics.median(warm) if warm else None,
        "warm_p95_seconds": sorted(warm)[math.ceil(.95 * len(warm)) - 1] if warm else None}
    latency["targets_met"] = bool(warm) and latency["warm_median_seconds"] <= 10 and latency["warm_p95_seconds"] <= 20
    summary = {"version": "1.0.0", "bundle_freeze_sha256": sha(HERE / "freeze.json"),
        "classification": cfg["classification"], "evaluations": evaluations, "failures": failures,
        "strict_passes": sum(e["strict_pass"] for e in evaluations), "request_count": len(evaluations),
        "gpu_offload": {"recorded_layers": offloads, "full_offload": full_offload, "positive_memory_samples": len(measured),
            "speedup_over_CPU_established": False}, "latency": latency,
        "linguistic_validation": "pending", "DESIGN": "pending"}
    (results / "assessment.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    if known_only:
        gate = {"version": "1.0.0", "bundle_freeze_sha256": sha(HERE / "freeze.json"),
            "allowed": not failures and len(evaluations) == 6,
            "known_receipt": receipt, "assessment_sha256": sha(results / "assessment.json"),
            "reason": "all six strict gates passed" if not failures else "STOP: strict gate failure; no extra cases/retry/tuning"}
        (results / "gate.json").write_text(json.dumps(gate, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ["strict_passes", "request_count", "failures", "latency", "linguistic_validation", "DESIGN"]}, indent=2))
    return bool(failures)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["known", "all"])
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    raise SystemExit(assess_folder(args.results.resolve(), args.stage == "known"))
