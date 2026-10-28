"""One authorized artifact-reusing restart; importing this file executes nothing."""
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "renewed_2026_10_11"
REPO = HERE.parents[3]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, value):
    path = HERE / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


def event(name, **values):
    row = {"utc": utc(), "event": name, **values}
    with (HERE / "events.jsonl").open("a") as output:
        output.write(json.dumps(row) + "\n")
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps(row), flush=True)


def fingerprint(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and "build" not in p.relative_to(root).parts}


def available():
    return next(int(line.split()[1]) * 1024 for line in Path("/proc/meminfo").read_text().splitlines()
                if line.startswith("MemAvailable:"))


def active_processes(scratch, alias):
    found = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            args = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
            exe = os.readlink(p / "exe")
            markers = [str(scratch), str(alias), str(HERE / "restart.py"),
                       str(PRIOR / "run.py"), str(PRIOR / "resume_gate1.py")]
            if any(marker in args or exe.startswith(marker + "/") for marker in markers):
                found.append({"pid": int(p.name), "exe": exe, "args": args})
        except (OSError, ProcessLookupError):
            pass
    return found


def main():
    if (HERE / "execution.json").exists():
        raise RuntimeError("This restart already has execution state; inspect it instead of restarting")
    prior = json.loads((PRIOR / "preparation.json").read_text())
    config = json.loads((PRIOR / "config.json").read_text())
    scratch = Path(prior["temporary_root"])
    if not scratch.is_dir():
        raise RuntimeError("Surviving workspace artifacts absent; no reacquisition authorized")
    alias = REPO / "build/qwen-restart-20261011"
    with (scratch / "restart-owner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active = active_processes(scratch, alias)
        if active:
            raise RuntimeError("Experiment already active: " + json.dumps(active))
        for name, digest in json.loads((PRIOR / "freeze.json").read_text())["files"].items():
            if hashlib.sha256((PRIOR / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Prior frozen artifact changed: " + name)
        if available() < config["preflight_memory_min_bytes"]:
            raise RuntimeError("Preflight RAM guard")
        if shutil.disk_usage(scratch).free < config["scratch_budget_bytes"]:
            raise RuntimeError("Preflight disk guard")
        alias.parent.mkdir(exist_ok=True)
        if alias.is_symlink():
            if alias.resolve() != scratch.resolve():
                raise RuntimeError("Artifact alias belongs to another tree")
        elif alias.exists():
            raise RuntimeError("Refuse replacing existing artifact alias")
        else:
            alias.symlink_to(scratch, target_is_directory=True)
        if len(str(alias / "inference.sock").encode()) >= 108:
            raise RuntimeError("Unix socket path is too long")
        ignored = subprocess.run(["git", "check-ignore", "--quiet", str(alias)], cwd=REPO)
        if ignored.returncode != 0:
            raise RuntimeError("Artifact storage must be Git-ignored")
        preserved = fingerprint(PRIOR)
        started = time.time()
        config["start_utc"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(started))
        deadline = started + config["total_limit_seconds"]
        write("config.json", config)
        for name in ["run.py", "operations.py"]:
            shutil.copyfile(PRIOR / name, HERE / name)
        write("operational_changes.json", {
            "linked_attempt": str(PRIOR), "evaluation_runner_copied_unchanged": True,
            "changes": ["One-shot artifact-reusing orchestration and exclusive lock/process check",
                        "Short Git-ignored workspace alias for Unix socket",
                        "Fresh authorized deadline, cumulative download ledger and periodic durable resources",
                        "Retain workspace artifacts through closeout"],
            "model_prompt_cases_scoring_changed": False})
        files = ["config.json", "run.py", "operations.py", "restart.py",
                 "../evaluate_model.py", "../prepare.py", "../heldout_v2.json",
                 "../calibration.json", "../../heldout.json", "../../prototype.py"]
        write("freeze.json", {"utc": utc(), "files": {
            n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in files},
            "note": "Parent prompt/schema/scorer/cases and renewed evaluator unchanged; operational restart only."})
        write("execution.json", {"start_epoch": started, "deadline_epoch": deadline,
              "utc": utc(), "pid": os.getpid(), "linked_attempt": str(PRIOR),
              "original_deadline_epoch": json.loads((PRIOR / "resumption.json").read_text())["original_deadline_epoch"],
              "artifact_tree": str(scratch), "artifact_alias": str(alias),
              "prior_record_sha256": preserved, "authorization": "Owner authorized fresh two-hour run on 2026-10-11",
              "preflight_available_bytes": available(), "preflight_disk_free_bytes": shutil.disk_usage(scratch).free,
              "active_experiment_processes": active, "retention": "Preserve reusable workspace artifacts; no cleanup"})
        sys.path.insert(0, str(HERE))
        spec = importlib.util.spec_from_file_location("restart_evaluator", HERE / "run.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        runner.DEADLINE = deadline
        state = {"started": utc(), "temporary_root": str(alias), "artifact_tree": str(scratch),
                 "downloads": prior["downloads"].copy(), "steps": [], "status": "running"}
        metrics = {"peak_owned_rss_bytes": 0, "minimum_available_bytes": available(), "peak_temporary_bytes": 0}
        processes = []

        def sample(group=None):
            rss = runner.owned_rss(group) if group else 0
            mem = available()
            size = runner.disk_bytes(scratch)
            metrics["peak_owned_rss_bytes"] = max(metrics["peak_owned_rss_bytes"], rss)
            metrics["minimum_available_bytes"] = min(metrics["minimum_available_bytes"], mem)
            metrics["peak_temporary_bytes"] = max(metrics["peak_temporary_bytes"], size)
            row = {"utc": utc(), "owned_process_group": group, "owned_rss_bytes": rss,
                   "available_memory_bytes": mem, "temporary_bytes": size}
            with (HERE / "resource_samples.jsonl").open("a") as output:
                output.write(json.dumps(row) + "\n"); output.flush(); os.fsync(output.fileno())
            write("resources.json", {**metrics, "latest": row})
            return size

        def guard(group=None):
            error = runner.guard_error(runner.owned_rss(group) if group else 0, available(), time.time(), deadline, config)
            if error:
                raise RuntimeError(error)
            if runner.disk_bytes(scratch) > config["scratch_budget_bytes"]:
                raise RuntimeError("scratch_limit")

        def command(args, name, limit):
            guard()
            log = HERE / (name + ".log")
            begin = time.monotonic()
            env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                   "TMPDIR": str(alias / "tmp"), "LLAMA_CACHE": str(alias / "cache")}
            with log.open("x") as output:
                proc = subprocess.Popen(args, stdout=output, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                processes.append(proc)
                event("command_started", step=name, args=args, owned_process_group=proc.pid)
                write("progress.json", {"gate": 1, "state": name, "owned_process_group": proc.pid, "scratch": str(alias)})
                last_sample = 0
                try:
                    while proc.poll() is None:
                        guard(proc.pid)
                        if time.monotonic() - begin > limit:
                            raise RuntimeError(name + " timeout")
                        if time.monotonic() - last_sample > 5:
                            sample(proc.pid); last_sample = time.monotonic()
                        time.sleep(.2)
                finally:
                    runner.stop_owned(proc)
                    row = {"name": name, "args": args, "exit_code": proc.returncode,
                           "elapsed_seconds": time.monotonic() - begin}
                    state["steps"].append(row); write("preparation.json", state)
                    event("command_finished", **row); sample()
                if proc.returncode:
                    raise RuntimeError(name + " failed; stop without retry")

        def download_model(dest):
            info = config["model"]
            counted = sum(d["bytes"] for d in state["downloads"])
            if counted + info["bytes"] > config["download_budget_bytes"]:
                raise RuntimeError("Cumulative download preflight")
            if (HERE / "download.json").exists() or dest.with_suffix(".gguf.part").exists():
                raise RuntimeError("Model download already attempted; no retry")
            ledger = {"status": "started", "utc": utc(), "prior_bytes": counted, "received_bytes": 0,
                      "url": "https://huggingface.co/" + info["repo"] + "/resolve/" + info["revision"] + "/" + info["file"]}
            write("download.json", ledger); event("model_download_started", **ledger)
            write("progress.json", {"gate": 1, "state": "model_download", "scratch": str(alias)})
            digest = hashlib.sha256(); partial = dest.with_suffix(".gguf.part")
            try:
                with urllib.request.urlopen(ledger["url"], timeout=30) as response, partial.open("xb") as output:
                    while True:
                        guard()
                        block = response.read(4 * 1024 * 1024)
                        if not block:
                            break
                        output.write(block); output.flush(); os.fsync(output.fileno()); digest.update(block)
                        ledger["received_bytes"] += len(block)
                        write("download.json", ledger)
                        if counted + ledger["received_bytes"] > config["download_budget_bytes"]:
                            raise RuntimeError("Cumulative download guard")
                if ledger["received_bytes"] != info["bytes"] or digest.hexdigest() != info["sha256"]:
                    raise RuntimeError("Model checksum/size mismatch")
                partial.replace(dest)
                ledger.update(status="verified", sha256=digest.hexdigest(), finished=utc())
                state["downloads"].append({"url": ledger["url"], "file": dest.name,
                                          "bytes": ledger["received_bytes"], "sha256": digest.hexdigest()})
                event("model_download_verified", bytes=ledger["received_bytes"], sha256=digest.hexdigest())
            except BaseException as exc:
                ledger.update(status="stopped", error=str(exc)); raise
            finally:
                write("download.json", ledger); write("preparation.json", state)

        event("restart_started", start_epoch=started, deadline_epoch=deadline, prior_download_bytes=sum(d["bytes"] for d in state["downloads"]))
        write("preparation.json", state)
        status = "stopped"; error = None; code = 1; telemetry_stop = threading.Event(); telemetry = None
        try:
            sample(); runner.verify_freeze()
            cmake = scratch / "cmake-3.31.6-linux-x86_64/bin/cmake"
            server = scratch / "build/bin/llama-server"
            if not server.exists():
                command([str(cmake), "--build", str(scratch / "build"), "--target", "llama-server", "-j1"], "build", config["build_limit_seconds"])
            command([str(server), "--version"], "runtime_version", 30)
            model = scratch / config["model"]["file"]
            if model.exists():
                if model.stat().st_size != config["model"]["bytes"] or hashlib.sha256(model.read_bytes()).hexdigest() != config["model"]["sha256"]:
                    raise RuntimeError("Existing model invalid; no replacement acquisition")
                event("model_reused", path=str(model))
            else:
                download_model(model)
            state.update(status="prepared", server=str(server), model=str(model), finished=utc())
            write("preparation.json", state); event("gate_1_passed")

            def telemetry_loop():
                while not telemetry_stop.wait(5):
                    try:
                        progress = json.loads((HERE / "progress.json").read_text())
                        sample(progress.get("owned_process_group"))
                    except (OSError, ValueError):
                        pass

            telemetry = threading.Thread(target=telemetry_loop, daemon=True); telemetry.start()
            code = runner.evaluate()
            result = json.loads((HERE / "results.json").read_text())
            status = result["status"]; error = result.get("error")
        except BaseException as exc:
            error = str(exc)
            state.update(status="stopped", error=error); write("preparation.json", state)
            write("progress.json", {"state": "stopped", "error": error, "scratch": str(alias)})
            event("restart_stopped", error=error)
        finally:
            telemetry_stop.set()
            if telemetry:
                telemetry.join(timeout=3)
            for proc in processes:
                runner.stop_owned(proc)
            sample()
            unchanged = fingerprint(PRIOR) == preserved
            write("closeout.json", {"utc": utc(), "status": status, "error": error, "exit_code": code,
                  "elapsed_seconds": time.time() - started, "deadline_epoch": deadline, "resources": metrics,
                  "prior_records_preserved": unchanged, "artifact_tree_retained": str(scratch),
                  "verified_cumulative_download_bytes": sum(d["bytes"] for d in state["downloads"]),
                  "design_acceptance": "pending", "automatic_restart": False})
            event("restart_finished", status=status, error=error, exit_code=code, prior_records_preserved=unchanged)
        return code


if __name__ == "__main__":
    raise SystemExit(main())
