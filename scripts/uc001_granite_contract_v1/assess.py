"""Future owner-gated client. No acquisition, build, server startup or automatic retry."""

import argparse
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import sqlite3
import time
from uuid import uuid4

from app.domain.interpretation import LanguageOutcome, apply_language_policy
from app.infrastructure.granite_interpreter import GraniteInterpreter
from app.infrastructure.llama_cpp_interpreter import strict_json
from scripts.uc001_granite_contract_v1.package import (
    PACKAGE, accept_review, canonical, check_approval, load_frozen, reserve_generation, validate_cases,
)


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def wait_review(path, bundle_id, case_id, packet_sha256, deadline, *, clock=time.monotonic, sleep=time.sleep):
    stop = min(deadline, clock() + 120)
    while clock() < stop:
        if path.is_file():
            review = json.loads(path.read_text(encoding="utf-8"))
            accept_review(review, bundle_id, case_id, packet_sha256)
            return review
        sleep(0.2)
    raise TimeoutError("Competent review was unavailable within the frozen wall-clock budget")


def check_dependencies(root):
    expected = json.loads((root / PACKAGE / "validation-dependencies.json").read_text(encoding="utf-8"))
    if platform.system() != "Windows" or platform.python_version() != expected["python"]:
        raise ValueError("The approved Windows/Python environment is not established")
    for name, version in expected["packages"].items():
        if importlib.metadata.version(name) != version:
            raise ValueError("A frozen validation dependency differs or is missing")


def runtime_properties(interpreter, deadline):
    remaining = min(120, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError("Assessment deadline expired before runtime metadata")
    with interpreter.client.stream("GET", "/props", timeout=remaining) as response:
        response.raise_for_status()
        raw = bytearray()
        for chunk in response.iter_bytes():
            raw.extend(chunk)
            if len(raw) > GraniteInterpreter.MAX_RESPONSE_BYTES or time.monotonic() >= deadline:
                raise ValueError("Runtime metadata exceeds response/deadline guard")
    return strict_json(bytes(raw))


def validate_runtime_metadata(props, config):
    build = props.get("build_info") if isinstance(props, dict) else None
    match = re.fullmatch(r"b[0-9]+-([0-9a-f]{7,40})", build) if isinstance(build, str) else None
    if (match is None or not config["runtime"]["revision"].startswith(match[1])
            or type(props.get("total_slots")) is not int or props["total_slots"] != 1
            or type(props.get("default_generation_settings", {}).get("n_ctx")) is not int
            or props["default_generation_settings"]["n_ctx"] != 8192
            or props.get("model_alias") != GraniteInterpreter.MODEL
            or not isinstance(props.get("chat_template"), str)
            or sha256(props["chat_template"].encode()).hexdigest() != config["candidate"]["expected_template_sha256"]):
        raise ValueError("Actual runtime build/context/slot/alias/template differs from the freeze")


def validate_case_state(result, case):
    if result.meaning_status not in case["acceptable_meaning_states"]:
        raise ValueError("A structurally valid packet violates the frozen case outcome")


def replay_application(root, output, case, result):
    from fastapi.testclient import TestClient
    from scripts.uc001_contract_check.development import create_development_app

    class Captured:
        def interpret(self, original_text):
            if original_text != result.original_text:
                raise ValueError("Captured interpretation cannot answer a different input")
            return result

    database = output / "application-replay.sqlite3"
    app = create_development_app(database, Captured())
    service = app.state.comparisons
    try:
        with TestClient(app) as client:
            response = client.post("/api/comparisons", json={"submission_key": str(uuid4()), "text": case["text"],
                "search_location": {"country_code": "CH"}, "location_choice": "provided",
                "language_context": {"browser_language": "en"}}, headers={"X-Submission-Proof": uuid4().hex + uuid4().hex})
        body = response.json()
        with sqlite3.connect(database) as connection:
            rows = connection.execute("SELECT id,projection FROM search_request").fetchall()
            counts = {name: connection.execute("SELECT count(*) FROM " + name).fetchone()[0]
                for name in ("search_request", "request_alternative", "request_alternative_evidence")}
        if body.get("persistence", {}).get("state") == "saved":
            if len(rows) != 1 or json.loads(rows[0][1]) != body:
                raise ValueError("Application replay projection/identity differs from SQLite")
        elif rows:
            raise ValueError("Unsaved application replay unexpectedly persisted")
        observation = {"mode": "captured_result_replay", "additional_generations": 0,
            "status": response.status_code, "response": body, "row_counts": counts,
            "semantic_acceptance": False, "real_knowledge_or_multilingual_rendering_acceptance": False}
        save(output / "application-replay.json", observation)
        if response.status_code >= 500:
            raise ValueError("Application replay failed technically")
    finally:
        service.store.engine.dispose()


def run_assessment(root, approval, output):
    root = Path(root).resolve()
    frozen = load_frozen(root)
    check_approval(approval, frozen["bundle_id"])
    check_dependencies(root)
    output = Path(output).resolve()
    if not output.is_relative_to((root / "build/test-only").resolve()) or output.exists():
        raise ValueError("Use a new isolated assessment directory; consumed attempts cannot resume")
    key = os.environ.get("RESOLENA_GRANITE_API_KEY", "")
    if not key:
        raise ValueError("Explicit loopback authentication is missing")
    config = json.loads((root / PACKAGE / "config.json").read_text(encoding="utf-8"))
    started = datetime.fromisoformat(approval.get("assessment_start_utc", ""))
    if started.tzinfo is None:
        raise ValueError("Owner-attested UTC assessment start before server launch is required")
    elapsed = time.time() - started.timestamp()
    if not 0 <= elapsed < config["operational_limits"]["assessment_seconds"]:
        raise ValueError("Assessment clock is future-dated or already expired")
    deadline = time.monotonic() + config["operational_limits"]["assessment_seconds"] - elapsed
    cases = validate_cases(root)["cases"]
    prompt = (root / PACKAGE / "system-prompt.txt").read_bytes().decode("utf-8")
    if sha256(prompt.encode()).hexdigest() != config["system_prompt_sha256"]:
        raise ValueError("System prompt differs from the frozen configuration")
    output.mkdir(parents=True)
    (output / "reviews").mkdir()
    ledger = {"bundle_id": frozen["bundle_id"], "generation_attempts": [], "closed": False,
        "maximum_startups": 1, "startup_measurements": "Owner-attested prerequisites, not verified by this client",
        "structural_results": [], "semantic_results": [], "qualified_review": "pending"}
    save(output / "ledger.json", ledger)
    try:
        with GraniteInterpreter(config["endpoint"], key, prompt) as interpreter:
            props = runtime_properties(interpreter, deadline)
            validate_runtime_metadata(props, config)
            save(output / "runtime-props.json", {name: props.get(name) for name in
                ("total_slots", "default_generation_settings", "model_alias", "build_info", "model_ftype", "modalities")})
            for case in cases:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Total assessment/review deadline expired")
                if (deadline - time.monotonic()) < GraniteInterpreter.TIMEOUT:
                    raise TimeoutError("Insufficient remaining global budget for a complete request")
                case_dir = output / case["id"]
                case_dir.mkdir()

                def reserve(original):
                    if original != case["text"] or time.monotonic() >= deadline:
                        raise ValueError("Unfrozen input or expired assessment")
                    reserve_generation(ledger, case["id"], [value["id"] for value in cases], frozen["bundle_id"])
                    save(output / "ledger.json", ledger)

                def record(event, value):
                    if event not in ("prompt_fit", "request", "response"):
                        raise ValueError("Unexpected capture event")
                    save(case_dir / (event + ".json"), value)

                interpreter.before_generation, interpreter.record = reserve, record
                result = interpreter.interpret(case["text"])
                raw = json.loads((case_dir / "response.json").read_text(encoding="utf-8"))["content"]
                packet_sha256 = sha256(raw.encode()).hexdigest()
                save(case_dir / "structural-result.json", {"status": "pass", "packet_sha256": packet_sha256,
                    "interpretation": asdict(result), "semantic_status": "unreviewed", "qualified_review_status": "pending"})
                ledger["structural_results"].append(case["id"])
                save(output / "ledger.json", ledger)
                validate_case_state(result, case)
                if time.monotonic() >= deadline:
                    raise TimeoutError("Total assessment/review deadline expired")
                print(json.dumps({"awaiting_review": case["id"], "packet_sha256": packet_sha256,
                    "review_file": str(output / "reviews" / (case["id"] + ".json"))}), flush=True)
                wait_review(output / "reviews" / (case["id"] + ".json"), frozen["bundle_id"], case["id"], packet_sha256, deadline)
                ledger["semantic_results"].append(case["id"])
                if case["id"] == "g04-en":
                    replay_application(root, output, case, result)
                if case["id"] in ("g05-shared", "g07-mixed-balanced"):
                    replays = []
                    for context in ({"preferred_language": "fr", "browser_language": "de"},
                            {"explanation_language_choice": "it", "browser_language": "de"}):
                        try:
                            value = apply_language_policy(result, context)
                            replays.append({"mode": "captured_result_policy_replay", "additional_generations": 0,
                                "language": value.explanation_language, "origin": value.language_origin})
                        except LanguageOutcome as action:
                            replays.append({"mode": "captured_result_policy_replay", "additional_generations": 0,
                                "outcome": action.outcome, "code": action.code})
                    save(case_dir / "policy-replays.json", replays)
                save(output / "ledger.json", ledger)
                if time.monotonic() >= deadline:
                    raise TimeoutError("Total assessment/review deadline expired")
            ledger["qualified_review"] = "Owner-attested per-case receipts; no general linguistic acceptance"
    except BaseException as error:
        ledger["stop"] = type(error).__name__
        raise
    finally:
        ledger["closed"] = True
        save(output / "ledger.json", ledger)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    run_assessment(root, approval, args.output)


if __name__ == "__main__":
    main()
