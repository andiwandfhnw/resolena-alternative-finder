"""Evaluate real frozen functions; expected data is used only by the scorer."""
import hashlib
import json
import socket
import sys
from collections import Counter
from pathlib import Path
from prototype import interpret, extract_evidence, render, LANGUAGES

ROOT = Path(__file__).resolve().parent
def mismatch(actual, expected):
    return {k: {"expected": v, "actual": actual.get(k)}
            for k, v in expected.items()
            if k not in {"must_clarify", "unsupported"} and actual.get(k) != v}

def main():
    sample = json.loads((ROOT / "heldout.json").read_text())
    parser_hash = hashlib.sha256((ROOT / "prototype.py").read_bytes()).hexdigest()
    if parser_hash != sample["frozen_parser_sha256"]:
        raise RuntimeError("Frozen parser changed")
    attempts = []
    def blocked(*args, **kwargs):
        attempts.append("network")
        raise RuntimeError("Network use is forbidden")
    socket.socket = blocked
    socket.create_connection = blocked
    requests = []
    for case in sample["requests"]:
        actual = interpret(case["text"], **case["context"])
        expected = case["expected"]
        differences = mismatch(actual, expected)
        if actual["status"] == "handled":
            incorrect = bool(differences or expected.get("must_clarify") or expected.get("unsupported"))
            if case["language"] in LANGUAGES and actual["language"] != case["language"]:
                differences["language"] = {"expected": case["language"], "actual": actual["language"]}
                incorrect = True
            category = "incorrect" if incorrect else "handled"
        else:
            category = actual["status"]
        requests.append({"id": case["id"], "language": case["language"],
                         "text": case["text"], "category": category, "actual": actual,
                         "differences": differences,
                         "original_and_country_preserved": actual["original"] == case["text"] and actual["country"] == "CH"})
    evidence = []
    for case in sample["evidence"]:
        actual = extract_evidence(case["text"])
        differences = mismatch(actual, case["expected"])
        category = ("incorrect" if differences else "handled") if actual["status"] == "handled" else actual["status"]
        renderings = []
        if category == "handled":
            for language in LANGUAGES:
                value = render(actual, language)
                renderings.append(value)
                if mismatch(value, case["expected"]) or value["original_evidence"] != case["text"]:
                    category = "incorrect"
        evidence.append({"id": case["id"], "language": case["language"], "text": case["text"],
                         "category": category, "actual": actual, "renderings": renderings,
                         "differences": differences})
    output = {
        "experiment": "UC-001 multilingual stdlib spike v1",
        "python": sys.version.split()[0],
        "parser_sha256": parser_hash,
        "fixture_sha256": hashlib.sha256((ROOT / "heldout.json").read_bytes()).hexdigest(),
        "provenance": sample["provenance"],
        "requests_summary": dict(Counter(c["category"] for c in requests)),
        "request_language_summary": {lang: dict(Counter(c["category"] for c in requests if c["language"] == lang))
                                     for lang in [*LANGUAGES, "mixed", "ambiguous", "es", "gsw"]},
        "evidence_summary": dict(Counter(c["category"] for c in evidence)),
        "renderings_executed": sum(len(c["renderings"]) for c in evidence),
        "network_attempts": attempts,
        "limitations": ["No production knowledge, retrieval, persistence, API or browser implementation tested.",
                        "Template phrases and expected meaning are AI-authored, not independent linguistic validation.",
                        "Hand-authored oracles are scoring data; runtime never reads expected fields.",
                        "Partial hints in abstentions may be wrong; they are not usable interpretations."],
        "requests": requests, "evidence": evidence,
    }
    (ROOT / "results.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k not in {"requests", "evidence"}}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
