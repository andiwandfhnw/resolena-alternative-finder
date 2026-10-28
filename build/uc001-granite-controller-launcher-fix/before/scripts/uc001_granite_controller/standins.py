"""Harmless opt-in Windows ownership self-test; no acquisition or build actions."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone


class StandinFailure(RuntimeError):
    pass


def _job_module():
    name = "granite_controller_standin_windows_job"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("windows_job.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _native_guard():
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8 or sys.version_info[:3] != (3, 12, 11):
        raise StandinFailure("Windows x64 / Python 3.12.11 required; no native operation performed")


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _write_new(path, value):
    with Path(path).open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True) + "\n").encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())


class Journal:
    def __init__(self, path, clock):
        self.stream = Path(path).open("xb")
        self.clock = clock
        self.lock = threading.Lock()

    def record(self, event, **values):
        row = dict(event=event, timestamp_utc=_utc(), monotonic=self.clock(), **values)
        data = (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
        with self.lock:
            self.stream.write(data)
            self.stream.flush()
            os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def _identity(path, role):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if (value.get("role") != role or type(value.get("pid")) is not int or value["pid"] <= 0
            or type(value.get("creation_time_100ns")) is not int or value["creation_time_100ns"] <= 0
            or type(value.get("parent_pid")) is not int or value["parent_pid"] <= 0):
        raise StandinFailure("stand-in creation identity malformed")
    return value


def run_ownership_selftest(output, python_exe=sys.executable, *, job_factory=None,
                           popen_factory=subprocess.Popen, clock=time.monotonic,
                           sleep=time.sleep, timeout_seconds=20):
    native = job_factory is None
    if native:
        _native_guard()
        if not Path(python_exe).is_absolute() or not Path(python_exe).is_file():
            raise StandinFailure("explicit existing Python executable required")
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 20:
        raise StandinFailure("ownership self-test deadline must be at most 20 seconds")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started, started_utc = clock(), _utc()
    deadline = started + timeout_seconds
    journal = Journal(output / "controller.jsonl", clock)
    job = None
    unrelated = None
    unrelated_handle = None
    unrelated_created = None
    worker = None
    expired = threading.Event()
    watchdog_stop = threading.Event()
    terminated = threading.Event()
    terminate_lock = threading.Lock()
    watchdog = None
    result = dict(ownership_self_test_passed=False, windows_execution=native,
                  synthetic_injected=not native, started_utc=started_utc,
                  started_monotonic=started, timeout_seconds=timeout_seconds,
                  controller_pid=os.getpid(), controller_outside_private_job=False,
                  suspended_assignment_order_verified=False, owned_identities=[],
                  unrelated_survived=False, unrelated_cleanup_verified=False,
                  cleanup=dict(verified=False, active_processes=None, owned_exits=[]),
                  failure_reason=None, cleanup_errors=[], resource_fit_established=False,
                  model_started=False, gpu_probe=False, acquisition_or_build=False,
                  helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    def failure(reason):
        if result["failure_reason"] is None:
            result["failure_reason"] = str(reason)

    def terminate_once():
        with terminate_lock:
            if job is not None and not terminated.is_set():
                terminated.set()
                job.terminate()
                journal.record("private_job_termination_requested")

    def check_deadline():
        if expired.is_set() or clock() >= deadline:
            raise StandinFailure("ownership self-test deadline")

    def watchdog_main():
        if not watchdog_stop.wait(max(0, deadline - clock())):
            expired.set()
            try:
                terminate_once()
            except BaseException as error:
                result["cleanup_errors"].append("deadline termination: " + str(error))

    try:
        journal.record("selftest_start", native_windows=native, timeout_seconds=timeout_seconds)
        job = job_factory() if job_factory else _job_module().WindowsJob()
        result["controller_outside_private_job"] = not job.api.controller_in_job(job.handle)
        if not result["controller_outside_private_job"]:
            raise StandinFailure("controller is inside its private job")
        if native:
            watchdog = threading.Thread(target=watchdog_main, name="ownership-selftest-deadline", daemon=True)
            watchdog.start()
        check_deadline()
        argv = [str(python_exe), "-I", str(Path(__file__).resolve()),
                "--child-role", "unrelated", "--events", str(output), "--safety-seconds", "30"]
        with (output / "unrelated.stdout.log").open("xb") as stdout, (output / "unrelated.stderr.log").open("xb") as stderr:
            unrelated = popen_factory(argv, cwd=str(output), env=dict(os.environ), stdin=subprocess.DEVNULL,
                                      stdout=stdout, stderr=stderr, close_fds=True,
                                      creationflags=0x08000000 if native else 0)
        if unrelated.poll() is not None:
            raise StandinFailure("unrelated stand-in exited prematurely")
        unrelated_handle = job.api.open_process(unrelated.pid)
        unrelated_created = job.api.creation_time(unrelated_handle)
        if job.api.in_job(unrelated_handle, job.handle):
            raise StandinFailure("unrelated stand-in was included in private job")
        while not (output / "unrelated.identity.json").is_file():
            check_deadline()
            if unrelated.poll() is not None:
                raise StandinFailure("unrelated stand-in exited before identity evidence")
            sleep(0.01)
        unrelated_record = _identity(output / "unrelated.identity.json", "unrelated")
        if ((unrelated_record["pid"], unrelated_record["creation_time_100ns"]) != (unrelated.pid, unrelated_created)
                or unrelated_record["parent_pid"] != os.getpid()):
            raise StandinFailure("unrelated creation identity mismatch")
        result["unrelated_identity"] = unrelated_record
        journal.record("unrelated_identity_retained", pid=unrelated.pid, creation_time_100ns=unrelated_created)
        argv[argv.index("--child-role") + 1] = "root"
        worker = job.launch(argv, str(output), dict(os.environ), output / "root.stdout.log", output / "root.stderr.log")
        events = job.drain_events()
        names = [row["event"] for row in events if row.get("pid") == worker.pid]
        required = ["worker_created_suspended", "worker_assigned", "worker_resumed"]
        if [name for name in names if name in required] != required or not worker.assigned or not worker.resumed:
            raise StandinFailure("suspended assignment/resume order not verified")
        result["suspended_assignment_order_verified"] = True
        for row in events:
            journal.record("backend_event", value=row)
        roles = ("root", "child", "grandchild")
        while True:
            check_deadline()
            if job.process_exit(worker) is not None:
                raise StandinFailure("owned root exited prematurely")
            snapshot = job.snapshot()
            journal.record("owned_observation", snapshot=snapshot)
            if all((output / f"{role}.identity.json").is_file() for role in roles):
                records = [_identity(output / f"{role}.identity.json", role) for role in roles]
                if len({row["pid"] for row in records}) != 3:
                    raise StandinFailure("distinct nested owned PIDs not established")
                if (records[0]["pid"], records[0]["creation_time_100ns"]) != (worker.pid, worker.creation_time_100ns):
                    raise StandinFailure("role root does not match retained worker identity")
                expected_parents = [os.getpid(), records[0]["pid"], records[1]["pid"]]
                if [row["parent_pid"] for row in records] != expected_parents:
                    raise StandinFailure("nested parent identity chain differs")
                for row in records:
                    job.validate_pid(row["pid"], row["creation_time_100ns"])
                members = {(row["pid"], row["creation_time_100ns"])
                           for row in snapshot["owned"] if row["in_job"] and row["exit_code"] is None}
                expected = {(row["pid"], row["creation_time_100ns"]) for row in records}
                if not expected <= members or snapshot["active_processes"] < 3:
                    raise StandinFailure("nested private-job membership is unknown")
                result["owned_identities"] = records
                journal.record("three_nested_identities_verified", identities=records)
                break
            sleep(0.01)
    except BaseException as error:
        failure("controller_interruption" if isinstance(error, KeyboardInterrupt)
                else type(error).__name__ + ": " + str(error))
    finally:
        if job is not None:
            try:
                terminate_once()
            except BaseException as error:
                result["cleanup_errors"].append("private job termination: " + str(error))
                failure("private job termination failed")
            try:
                result["cleanup"] = job.cleanup(timeout_seconds=max(0, min(5, deadline - clock())))
                expected = {(row["pid"], row["creation_time_100ns"]) for row in result["owned_identities"]}
                exits = {(row["pid"], row["creation_time_100ns"]) for row in result["cleanup"].get("owned_exits", [])
                         if type(row.get("exit_code")) is int}
                if (result["cleanup"].get("verified") is not True
                        or result["cleanup"].get("active_processes") != 0 or not expected <= exits):
                    failure("owned job cleanup/identity exits unverified")
                journal.record("private_job_cleanup", cleanup=result["cleanup"])
            except BaseException as error:
                result["cleanup_errors"].append("private job cleanup: " + str(error))
                failure("private job cleanup failed")
        if unrelated is not None:
            try:
                identity_ok = unrelated_handle is not None and job.api.creation_time(unrelated_handle) == unrelated_created
                result["unrelated_survived"] = identity_ok and unrelated.poll() is None
                journal.record("unrelated_after_private_job_termination", survived=result["unrelated_survived"],
                               pid=unrelated.pid, creation_time_100ns=unrelated_created)
                if not result["unrelated_survived"]:
                    failure("unrelated stand-in did not survive private-job termination")
                if unrelated.poll() is None:
                    unrelated.terminate()
                    unrelated.wait(timeout=max(0.01, min(5, deadline - clock())))
                result["unrelated_cleanup_verified"] = unrelated.poll() is not None
                if not result["unrelated_cleanup_verified"]:
                    failure("owned unrelated stand-in cleanup unverified")
            except BaseException as error:
                result["cleanup_errors"].append("owned unrelated stand-in cleanup: " + str(error))
                failure("owned unrelated stand-in cleanup failed")
        if unrelated_handle is not None:
            try:
                job.api.close_handle(unrelated_handle)
            except BaseException as error:
                result["cleanup_errors"].append("unrelated query handle: " + str(error))
                failure("unrelated query handle cleanup failed")
        if job is not None:
            try:
                job.close()
            except BaseException as error:
                result["cleanup_errors"].append("private job handle: " + str(error))
                failure("private job handle cleanup failed")
        watchdog_stop.set()
        if watchdog is not None:
            watchdog.join(1)
            if watchdog.is_alive():
                failure("ownership watchdog exit unverified")
        if expired.is_set() or clock() >= deadline:
            failure("ownership self-test deadline")
        result["ownership_self_test_passed"] = (result["failure_reason"] is None
            and result["controller_outside_private_job"] and result["suspended_assignment_order_verified"]
            and len(result["owned_identities"]) == 3 and result["unrelated_survived"]
            and result["unrelated_cleanup_verified"] and result["cleanup"].get("verified") is True)
        result["ended_utc"], result["ended_monotonic"] = _utc(), clock()
        result["elapsed_seconds"] = result["ended_monotonic"] - started
        journal.record("selftest_end", passed=result["ownership_self_test_passed"],
                       failure_reason=result["failure_reason"], elapsed_seconds=result["elapsed_seconds"])
        journal.close()
        _write_new(output / "result.json", result)
    return result


def _child(role, events, safety_seconds, python_exe):
    _native_guard()
    if role not in {"root", "child", "grandchild", "unrelated"} or not 0 < safety_seconds <= 30:
        raise StandinFailure("unapproved harmless stand-in role or safety deadline")
    events = Path(events).resolve(strict=True)
    if not events.is_dir():
        raise StandinFailure("existing self-test event directory required")
    module = _job_module()
    api = module.NativeApi()
    identity = dict(role=role, pid=os.getpid(), parent_pid=os.getppid(),
                    creation_time_100ns=api.creation_time(api.k.GetCurrentProcess()),
                    timestamp_utc=_utc(), monotonic_ns=time.monotonic_ns())
    pending = events / f"{role}.identity.pending"
    final = events / f"{role}.identity.json"
    _write_new(pending, identity)
    if final.exists():
        raise StandinFailure("stand-in identity already exists")
    os.replace(pending, final)
    child = None
    deadline = time.monotonic() + safety_seconds
    try:
        if role in {"root", "child"}:
            next_role = "child" if role == "root" else "grandchild"
            with (events / f"{next_role}.stdout.log").open("xb") as stdout, (events / f"{next_role}.stderr.log").open("xb") as stderr:
                child = subprocess.Popen([str(python_exe), "-I", str(Path(__file__).resolve()),
                                          "--child-role", next_role, "--events", str(events),
                                          "--safety-seconds", str(safety_seconds)],
                                         stdin=subprocess.DEVNULL, stdout=stdout,
                                         stderr=stderr, close_fds=True, creationflags=0x08000000)
        while time.monotonic() < deadline:
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-role", choices=("root", "child", "grandchild", "unrelated"), required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--safety-seconds", type=float, default=30)
    args = parser.parse_args()
    _child(args.child_role, args.events, args.safety_seconds, sys.executable)


if __name__ == "__main__":
    try:
        main()
    except (StandinFailure, OSError, ValueError) as error:
        print(json.dumps(dict(status="failure", reason=str(error))), file=sys.stderr)
        raise SystemExit(1)
