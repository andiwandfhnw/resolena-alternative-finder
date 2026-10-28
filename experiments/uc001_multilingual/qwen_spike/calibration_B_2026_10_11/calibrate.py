"""One frozen paired calibration, with unchanged model interpretation checks."""
import copy
import datetime
import fcntl
import hashlib
import http.client
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
PRIOR = PARENT / "restart_2026_10_11"
REPO = HERE.parents[3]
sys.path.insert(0, str(PARENT))
import evaluate_model as harness

spec = importlib.util.spec_from_file_location("calibration_operations", PRIOR / "operations.py")
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, obj):
    path = HERE / name
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as output:
        json.dump(obj, output, ensure_ascii=False, indent=2)
        output.write("\n"); output.flush(); os.fsync(output.fileno())
    temporary.replace(path)


def event(event_name, **data):
    row = {"utc": utc(), "event": event_name, **data}
    with (HERE / "events.jsonl").open("a") as output:
        output.write(json.dumps(row) + "\n"); output.flush(); os.fsync(output.fileno())
    print(json.dumps(row), flush=True)


def assess(obj, text, expected, finish):
    original = copy.deepcopy(obj)
    try:
        errors = harness.validate(original, text)
        semantic = harness.semantic_score(original, expected) if isinstance(original, dict) else {"category": "invalid_output"}
    except (KeyError, TypeError, ValueError) as exc:
        errors = ["malformed_fields: " + str(exc)]; semantic = {"category": "invalid_output"}
    data = obj if isinstance(obj, dict) else {}
    status = data.get("status") == expected["status"]
    language = data.get("language") == expected["language"]
    projected = None; meaning = None; constraints = None
    if expected["status"] == "understood":
        try:
            projected = {"subject": harness.canonical(data.get("subject", {}).get("value")),
                         "action": harness.canonical(data.get("action", {}).get("value")),
                         "goals": sorted(g["value"] for g in data.get("goals", [])),
                         "constraints": {c["kind"]: c["value"] for c in data.get("constraints", [])}}
            meaning = projected["subject"] == expected["subject"] and projected["action"] == expected["action"]
            constraints = projected["goals"] == expected["goals"] and projected["constraints"] == expected["constraints"]
        except (KeyError, TypeError, AttributeError):
            meaning = False; constraints = False
    uncertainty = not expected.get("unresolved_nonempty") or bool(data.get("unresolved"))
    quotes = []
    for label in ["subject", "action"]:
        item = data.get(label)
        if isinstance(item, dict):
            quote = item.get("quote")
            quotes.append({"field": label, "quote": quote,
                           "exact_substring": isinstance(quote, str) and bool(quote) and quote in text,
                           "absent_value": item.get("value") is None})
    for label in ["goals", "constraints"]:
        for index, item in enumerate(data.get(label, []) if isinstance(data.get(label), list) else []):
            if isinstance(item, dict):
                quote = item.get("quote")
                quotes.append({"field": f"{label}[{index}]", "quote": quote,
                               "exact_substring": isinstance(quote, str) and bool(quote) and quote in text,
                               "absent_value": item.get("value") is None})
    grounded = not any("quote" in error or error == "offset" for error in errors)
    passed = not errors and finish != "length" and status and language and uncertainty and meaning is not False and constraints is not False
    return {"structural_errors": errors, "frozen_semantic": semantic, "status_correct": status,
            "language_correct": language, "meaning_correct": meaning, "constraints_preserved": constraints,
            "uncertainty_preserved": uncertainty, "quotes_grounded": grounded, "quotes": quotes,
            "projected_meaning": projected, "pass": passed}


def main():
    if (HERE / "execution.json").exists():
        raise RuntimeError("Calibration already has execution state; no restart/retry")
    freeze = json.loads((HERE / "freeze.json").read_text())
    for name, digest in freeze["files"].items():
        if sha(HERE / name) != digest:
            raise RuntimeError("Frozen file changed: " + name)
    plan = json.loads((HERE / "cases.json").read_text())
    config = json.loads((PRIOR / "config.json").read_text())
    prep = json.loads((PRIOR / "preparation.json").read_text())
    verification = json.loads((PRIOR / "verification.json").read_text())
    scratch = Path(prep["artifact_tree"])
    workspace = REPO / "build/qwen-calibration-B-20261011"
    with (scratch / "restart-owner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_spec = importlib.util.spec_from_file_location("ownership_check", PRIOR / "restart.py")
        owner = importlib.util.module_from_spec(check_spec); check_spec.loader.exec_module(owner)
        active = owner.active_processes(scratch, workspace)
        if active:
            raise RuntimeError("Experiment processes already active: " + json.dumps(active))
        if sha(prep["server"]) != verification["server_sha256"] or sha(prep["model"]) != config["model"]["sha256"]:
            raise RuntimeError("Reusable binary/model hash mismatch; no acquisition/build")
        if owner.available() < config["preflight_memory_min_bytes"] or shutil.disk_usage(scratch).free < config["scratch_budget_bytes"]:
            raise RuntimeError("Preflight RAM/disk guard")
        workspace.mkdir(parents=True, exist_ok=False)
        if subprocess.run(["git", "check-ignore", "--quiet", str(workspace)], cwd=REPO).returncode:
            raise RuntimeError("Workspace storage must be Git-ignored")
        path = workspace / "inference.sock"
        if len(str(path).encode()) >= 108:
            raise RuntimeError("Unix socket path length")
        preserved = {str(p.relative_to(PARENT)): sha(p) for root in [PRIOR, PARENT / "renewed_2026_10_11"]
                     for p in root.rglob("*") if p.is_file() and "build" not in p.relative_to(root).parts}
        started = time.time(); deadline = started + 900
        runtime_args = json.loads((PRIOR / "results.json").read_text())["runtime_args"]
        runtime_args[runtime_args.index("-o") + 1] = str(workspace / "network.trace")
        runtime_args[runtime_args.index("--host") + 1] = str(path)
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
               "TMPDIR": str(Path(prep["temporary_root"]) / "tmp"),
               "LLAMA_CACHE": str(Path(prep["temporary_root"]) / "cache")}
        write("execution.json", {"utc": utc(), "start_epoch": started, "deadline_epoch": deadline,
              "runtime_args": runtime_args, "runtime_env": env, "base_configuration": config,
              "limits": {"total_seconds": 900, "readiness_seconds": 90, "request_seconds": 45},
              "frozen": freeze, "prior_record_sha256": preserved, "pid": os.getpid(),
              "preflight_available_bytes": owner.available(), "preflight_free_disk_bytes": shutil.disk_usage(scratch).free,
              "downloads": 0, "builds": 0, "retries": 0, "artifact_retention": True})
        report = {"status": "loading", "results": [], "current_case": None,
                  "planned_order": plan["execution_order"], "temperature_zero_success": False,
                  "classification": "Synthetic calibration only; frozen evaluation never invoked"}
        metrics = {"peak_owned_rss_bytes": 0, "minimum_available_bytes": owner.available(),
                   "peak_scratch_bytes": 0, "guard_error": None, "inet_activity": False}
        stop = threading.Event(); proc = None; monitor = None; output = None
        active_deadline = {"epoch": deadline}; case_progress = None

        def save():
            report["metrics"] = dict(metrics); report["elapsed_seconds"] = time.time() - started
            write("results.json", report)
            write("progress.json", {"utc": utc(), "state": report["status"], "current_case": report["current_case"],
                  "owned_process_group": proc.pid if proc else None, "completed": len(report["results"]),
                  "deadline_epoch": deadline, "workspace": str(workspace), "retain_artifacts": True})

        def monitor_loop():
            last = 0
            while not stop.wait(.2):
                rss = operations.owned_rss(proc.pid); memory = owner.available()
                metrics["peak_owned_rss_bytes"] = max(metrics["peak_owned_rss_bytes"], rss)
                metrics["minimum_available_bytes"] = min(metrics["minimum_available_bytes"], memory)
                error = operations.guard_error(rss, memory, time.time(), active_deadline["epoch"], config)
                if time.time() >= active_deadline["epoch"]:
                    error = "case_timeout" if active_deadline["epoch"] < deadline else "total_deadline"
                if time.monotonic() - last >= 2:
                    size = sum(p.stat().st_size for root in [scratch, workspace, HERE] for p in root.rglob("*") if p.is_file())
                    metrics["peak_scratch_bytes"] = max(metrics["peak_scratch_bytes"], size)
                    if size > config["scratch_budget_bytes"]:
                        error = "scratch_limit"
                    trace = workspace / "network.trace"
                    if trace.exists() and re.search(r"\bAF_INET6?\b", trace.read_text(errors="replace")):
                        metrics["inet_activity"] = True; error = "unexpected_inet_activity"
                    write("resources.json", {"utc": utc(), **metrics, "current_rss_bytes": rss, "available_bytes": memory})
                    last = time.monotonic()
                if error:
                    metrics["guard_error"] = error; operations.stop_owned(proc); return

        def http_exchange(method, route, body=None, timeout=45):
            conn = harness.LocalHTTP(str(path), min(timeout, max(.01, deadline-time.time())))
            encoded = json.dumps(body) if body is not None else None
            begin = time.monotonic()
            response = None
            try:
                conn.request(method, route, encoded, {"Content-Type": "application/json"} if body is not None else {})
                response = conn.getresponse(); raw = response.read().decode()
                return {"http_status": response.status, "http_headers": response.getheaders(),
                        "raw_body": raw, "wall_seconds": time.monotonic()-begin}
            except BaseException as exc:
                exc.exchange = {"http_status": response.status if response else None,
                                "http_headers": response.getheaders() if response else [],
                                "raw_body_partial": getattr(exc, "partial", b"").decode(errors="replace"),
                                "capture_complete": False, "wall_seconds": time.monotonic()-begin,
                                "exception_type": type(exc).__name__}
                raise
            finally:
                conn.close()

        try:
            save(); event("calibration_started", deadline_epoch=deadline)
            output = (workspace / "inference.log").open("x")
            proc = subprocess.Popen(runtime_args, stdout=output, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            save(); event("model_loading", owned_process_group=proc.pid)
            monitor = threading.Thread(target=monitor_loop, daemon=True); monitor.start()
            report["readiness"] = operations.wait_ready(path, proc, deadline, startup_limit=90)
            if metrics["guard_error"]:
                raise RuntimeError(metrics["guard_error"])
            props = http_exchange("GET", "/props", timeout=5); write("server_properties.json", props)
            if props["http_status"] != 200:
                raise RuntimeError("Properties transport failure")
            event("model_ready", **report["readiness"])
            for index, entry in enumerate(plan["execution_order"], 1):
                if metrics["guard_error"] or time.time() >= deadline or proc.poll() is not None:
                    raise RuntimeError(metrics["guard_error"] or "Server exited/total deadline")
                case = next(c for c in plan["cases"] if c["id"] == entry["case"])
                params = {k: config["inference"][k] for k in ["temperature", "top_p", "top_k", "min_p", "max_tokens"]}
                params["temperature"] = entry["temperature"]
                body = {"messages": [{"role": "system", "content": harness.PROMPT}, {"role": "user", "content": case["text"]}],
                        **params, "seed": 42, "cache_prompt": False, "chat_template_kwargs": {"enable_thinking": False},
                        "response_format": {"type": "json_object", "schema": harness.SCHEMA}}
                stem = f"{index:02d}-{case['id']}-t{entry['temperature']}"
                request = {"index": index, "case": case, "route": "/v1/chat/completions", "body": body,
                           "serialized_body": json.dumps(body), "http_headers": {"Content-Type": "application/json"}}
                write("requests/" + stem + ".json", request)
                rendered = http_exchange("POST", "/apply-template", body, timeout=5)
                write("templates/" + stem + ".json", rendered)
                if rendered["http_status"] != 200:
                    raise RuntimeError("Template diagnostic transport failure")
                case_progress = {"index": index, "id": case["id"], "text": case["text"], "expected": case["expected"],
                                 "temperature": entry["temperature"], "request_record": "requests/" + stem + ".json"}
                report.update(status="running", current_case={"index": index, **entry})
                save(); event("case_started", **report["current_case"])
                active_deadline["epoch"] = min(deadline, time.time()+45)
                exchange = http_exchange("POST", "/v1/chat/completions", body)
                active_deadline["epoch"] = deadline
                write("responses/" + stem + ".json", exchange)
                case_progress["exchange"] = exchange
                if exchange["http_status"] != 200:
                    raise RuntimeError("Completion HTTP " + str(exchange["http_status"]))
                wire = json.loads(exchange["raw_body"])
                choice = wire["choices"][0]; content = choice["message"]["content"]
                actual = harness.parse_content(content)
                case_progress.update(raw_content=content, actual=actual, finish_reason=choice.get("finish_reason"),
                                     usage=wire.get("usage"), timings=wire.get("timings"),
                                     assessment=assess(actual, case["text"], case["expected"], choice.get("finish_reason")))
                report["results"].append(case_progress); report["current_case"] = None
                save(); event("case_completed", index=index, id=case["id"], temperature=entry["temperature"],
                              passed=case_progress["assessment"]["pass"], status_correct=case_progress["assessment"]["status_correct"],
                              seconds=round(exchange["wall_seconds"],3), cache=wire.get("timings",{}).get("cache_n"))
                case_progress = None
                if metrics["guard_error"]:
                    raise RuntimeError(metrics["guard_error"])
            zero = [r for r in report["results"] if r["temperature"] == 0]
            report["temperature_zero_success"] = len(zero) == 6 and all(r["assessment"]["pass"] for r in zero)
            report["status"] = "completed_pass" if report["temperature_zero_success"] else "completed_fail"
        except BaseException as exc:
            report.update(status="stopped", error=metrics["guard_error"] or str(exc))
            if case_progress is not None:
                if hasattr(exc, "exchange"):
                    case_progress["exchange"] = exc.exchange
                    write("responses/" + stem + ".json", exc.exchange)
                case_progress.update(execution_error=report["error"], assessment={"pass": False, "not_assessed": True})
                report["results"].append(case_progress)
            event("calibration_stopped", error=report["error"])
        finally:
            stop.set()
            if monitor:
                monitor.join(timeout=6)
            if proc:
                operations.stop_owned(proc); report["owned_process_exit_code"] = proc.returncode
            if output:
                output.close()
            report["prior_records_preserved"] = all(sha(PARENT / n) == digest for n,digest in preserved.items())
            report["unexecuted_order"] = plan["execution_order"][len(report["results"]):]
            report["retry_or_tuning"] = False; report["heldout_exposed_to_model"] = False
            save()
            write("closeout.json", {"utc": utc(), "status": report["status"], "elapsed_seconds": time.time()-started,
                  "owned_process_exit_code": report.get("owned_process_exit_code"), "prior_records_preserved": report["prior_records_preserved"],
                  "temperature_zero_success": report["temperature_zero_success"], "metrics": metrics,
                  "workspace_retained": str(workspace), "shared_artifacts_retained": str(scratch), "design_acceptance": "pending"})
            event("calibration_finished", status=report["status"], completed=len(report["results"]), success=report["temperature_zero_success"])
        return 0 if report["temperature_zero_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
