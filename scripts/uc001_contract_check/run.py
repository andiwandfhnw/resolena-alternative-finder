"""Prepared bounded runner; default invocation cannot contact a runtime."""

import argparse
from dataclasses import asdict
from datetime import datetime
import base64
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4

from scripts.uc001_contract_check.controls import REPOSITORY, RunBudget, check_case_state, load_bundle, verify_effective, verify_authentication


def require_review(path, freeze_hash):
    review = json.loads(path.read_text())
    if review.get("status") != "approved" or not review.get("expected_meanings_approved") or review.get("freeze_sha256") != freeze_hash:
        raise ValueError("Qualified expectations review for this exact frozen bundle is required")
    languages = set()
    for reviewer in review.get("reviewers", []):
        if not all(reviewer.get(k) for k in ("name", "role", "date", "competence", "artifact_hash")) or reviewer["artifact_hash"] != freeze_hash:
            raise ValueError("Review identity/competence/date/artifact provenance missing")
        languages.update(reviewer.get("languages", []))
    if not {"de", "fr", "it", "en"} <= languages:
        raise ValueError("Qualified DE/FR/IT/EN review remains incomplete")
    return review


def deadline_alarm(_signal, _frame):
    raise TimeoutError("Bounded request deadline expired; no retry")


def verify_forward_listener():
    # Inspect the actual listener, not the health response. Reject any wildcard bind.
    result = subprocess.run(["ss", "-H", "-ltnp"], capture_output=True, text=True, check=True)
    lines = [line for line in result.stdout.splitlines() if line.split()[3].rsplit(":", 1)[-1] == "49188"]
    if len(lines) != 1 or lines[0].split()[3] != "127.0.0.1:49188":
        raise ValueError("Reverse listener absent, ambiguous or not loopback-only")
    # The SSH session's actual server port is supplied by sshd, not guessed from gh's local bridge flag.
    import os
    connection = os.environ.get("SSH_CONNECTION", "").split()
    if len(connection) != 4:
        raise ValueError("Runner must execute inside the approved SSH session")
    ssh_port = connection[3]
    ssh_listeners = [line for line in result.stdout.splitlines() if line.split()[3].rsplit(":", 1)[-1] == ssh_port]
    if not ssh_listeners or any(line.split()[3].rsplit(":", 1)[0] not in ("127.0.0.1", "[::1]") for line in ssh_listeners):
        raise ValueError("Current SSH listener is not confined to loopback")
    return {"reverse": lines, "ssh": ssh_listeners}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True, help="Requires separate owner live-execution authorization")
    parser.add_argument("--key-stdin", action="store_true", required=True)
    parser.add_argument("--windows-receipt-base64", required=True)
    parser.add_argument("--review", type=Path, required=True)
    args = parser.parse_args(argv)
    bundle = load_bundle()
    review = require_review(args.review, bundle["freeze_sha256"])
    receipt = json.loads(base64.b64decode(args.windows_receipt_base64, validate=True))
    if receipt["freeze_sha256"] != bundle["freeze_sha256"] or not receipt["authentication_verified"]:
        raise ValueError("Current owned/authenticated Windows receipt is required")
    start = datetime.fromisoformat(receipt["started_utc"]).timestamp()
    deadline = min(start + 1500, datetime.fromisoformat(receipt["total_started_utc"]).timestamp() + 2400)
    if not start <= time.time() < deadline or time.time() - receipt["receipt_epoch"] > 90:
        raise ValueError("Windows receipt is expired or clocks disagree")
    verify_effective(receipt["props"], receipt["startup_log"])
    listeners = verify_forward_listener()
    key = sys.stdin.readline().strip()
    if len(key) < 32:
        raise ValueError("Ephemeral runtime authentication missing from SSH stdin")
    run_id = receipt["run_id"]
    if not run_id or any(c not in "0123456789abcdef-" for c in run_id):
        raise ValueError("Invalid owned run identity")
    output = REPOSITORY / "build" / "test-only" / ("contract-" + run_id)
    output.mkdir(parents=True, exist_ok=False)
    budget = RunBudget(output / "attempts.jsonl", [c["text"] for c in bundle["cases"]["cases"]], deadline)
    counter = [0]

    def record(kind, value):
        counter[0] += 1
        path = output / f"{counter[0]:03d}-{kind}.json"
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def guard(text):
        verify_forward_listener()
        if sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) > 512 * 2**20:
            raise ValueError("Codespace artifact sub-budget exceeded")
        budget.consume(text)

    from app.domain.interpretation import LanguageOutcome, apply_language_policy
    from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter, strict_json
    from fastapi.testclient import TestClient
    from scripts.uc001_contract_check.development import create_development_app

    signal.signal(signal.SIGALRM, deadline_alarm)
    app = None
    record("preconditions", {"receipt": receipt, "review": review, "listeners": listeners})
    try:
        with LlamaCppInterpreter(bundle["config"]["endpoint"], key, bundle["prompt"], before_generation=guard, record=record) as interpreter:
            verify_authentication(interpreter.client)
            props_response = interpreter.client.get("/props"); props_response.raise_for_status()
            props = strict_json(props_response.content)
            verify_effective(props, receipt["startup_log"])
            record("current-props", props)
            app = create_development_app(output / "comparison.sqlite3", interpreter)
            with TestClient(app):
                for case in bundle["cases"]["cases"]:
                    signal.alarm(min(90, max(1, int(deadline - time.time()))))
                    result = None
                    # Keep raw result for policy replay even if API rendering is unavailable.
                    class Capture:
                        def interpret(self, text):
                            nonlocal result
                            result = interpreter.interpret(text)
                            return result
                    from dataclasses import replace
                    # create_app closes over its service, so explicitly compose each API case.
                    from app.interfaces.api import create_app
                    with TestClient(create_app(replace(app.state.comparisons, interpreter=Capture()))) as api:
                        if case["api"]:
                            response = api.post("/api/comparisons", json={"submission_key": str(uuid4()), "text": case["text"],
                                "search_location": {"country_code": "CH"}, "language_context": {"browser_language": "en"}},
                                headers={"X-Submission-Proof": "a" * 64})
                            record("api", {"case": case["id"], "status": response.status_code, "body": response.json()})
                            if response.status_code >= 400:
                                raise ValueError("API technical/structural failure; preserve raw response and stop")
                            expected = case["expected_route"]
                            if expected == "interpretation_capability_unavailable":
                                if response.json().get("issues") != [{"code": expected}]:
                                    raise ValueError("Unsupported control did not route to capability limitation")
                            elif response.json()["outcome"] != expected:
                                raise ValueError("API route differs from frozen expectation")
                        else:
                            result = interpreter.interpret(case["text"])
                    if result is None:
                        raise ValueError("No decoded interpretation captured")
                    record("contract", {"case": case["id"], "result": asdict(result), "semantic_review": "pending"})
                    state = asdict(result); state["recognition"].pop("version")
                    check_case_state(case, state)
                    # Replays do not generate or pretend to validate translations.
                    for context in ({}, {"browser_language": "fr"}, {"preferred_language": "en", "browser_language": "it"}, {"explanation_language_choice": "en"}):
                        try:
                            policy = asdict(apply_language_policy(result, context))
                        except LanguageOutcome as action:
                            policy = {"outcome": action.outcome, "code": action.code, "detail": action.detail}
                        record("policy-replay", {"case": case["id"], "context": context, "result": policy})
                    signal.alarm(0)
            record("completion", {"generations": budget.index, "semantics": "pending qualified review; no capability acceptance"})
    except BaseException as error:
        record("stopped", {"type": type(error).__name__, "message": str(error), "attempts": budget.index})
        raise
    finally:
        signal.alarm(0)
        if app is not None:
            app.state.comparisons.store.engine.dispose()


if __name__ == "__main__":
    main()
