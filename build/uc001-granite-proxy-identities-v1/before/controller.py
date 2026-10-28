"""Independent Windows acquisition/build control; imports never execute a phase."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import threading
import time
from datetime import datetime, timezone

ACQUISITION_SECONDS = 1800
DOWNLOAD_CEILING = 10737418240
BUILD_SECONDS = 2700
MEMORY_CAP = 25769803776
OUTPUT_CAP = 12884901888
INITIAL_DISK = 51539607552
DISK_FLOOR = 8589934592
HOST_FLOOR = 4294967296
OBSERVATION_AGE = 1.0
POLL_SECONDS = 0.05
PROXY_SHA256 = "a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d"


class ControllerFailure(RuntimeError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


class SafetyState:
    def __init__(self, started_mono, max_observation_age=OBSERVATION_AGE):
        if not number(started_mono) or not 0 < max_observation_age <= OBSERVATION_AGE:
            raise ControllerFailure("invalid_clock_or_staleness_bound")
        self.started_mono = started_mono
        self.build_started_mono = None
        self.last_mono = started_mono
        self.max_observation_age = max_observation_age
        self.initial_checked = False

    def start_build(self, now):
        if self.build_started_mono is not None or not self.initial_checked or not number(now) or now < self.last_mono:
            raise ControllerFailure("build_clock_reset_or_invalid_transition")
        self.build_started_mono = now
        self.last_mono = now

    def assess(self, phase, now, observation):
        if not number(now) or now < self.last_mono:
            raise ControllerFailure("monotonic_clock_invalid")
        self.last_mono = now
        if phase not in ("acquisition", "configure", "build"):
            raise ControllerFailure("unknown_phase")
        if phase == "acquisition":
            if self.build_started_mono is not None or now - self.started_mono >= ACQUISITION_SECONDS:
                raise ControllerFailure("acquisition_deadline_or_phase_reentry")
        elif self.build_started_mono is None or now - self.build_started_mono >= BUILD_SECONDS:
            raise ControllerFailure("combined_build_deadline_or_missing_anchor")
        if not isinstance(observation, dict) or observation.get("error"):
            raise ControllerFailure("resource_measurement_failed")
        sampled = observation.get("sampled_mono")
        if not number(sampled) or sampled > now or now - sampled > self.max_observation_age:
            raise ControllerFailure("resource_measurement_stale_or_missing")
        for key in ("disk_free_bytes", "host_free_bytes", "job_committed_bytes", "build_output_bytes"):
            if type(observation.get(key)) is not int or observation[key] < 0:
                raise ControllerFailure("resource_measurement_invalid:" + key)
        if not self.initial_checked:
            if observation["disk_free_bytes"] < INITIAL_DISK:
                raise ControllerFailure("initial_disk_below_minimum")
            self.initial_checked = True
        if observation["disk_free_bytes"] < DISK_FLOOR:
            raise ControllerFailure("disk_floor")
        if observation["host_free_bytes"] < HOST_FLOOR:
            raise ControllerFailure("host_memory_floor")
        if observation["job_committed_bytes"] > MEMORY_CAP or observation.get("memory_limit_event"):
            raise ControllerFailure("job_committed_memory_limit")
        if observation["build_output_bytes"] > OUTPUT_CAP:
            raise ControllerFailure("build_output_limit")


def validate_proxy_terminal(path, expected_prior_bytes, expected_pid=None):
    if type(expected_prior_bytes) is not int or not 0 <= expected_prior_bytes < DOWNLOAD_CEILING:
        raise ControllerFailure("prior_accounting_unknown")
    total = expected_prior_bytes
    opened, ended, amounts = set(), set(), {}
    seen_start = seen_end = seen_listener = False
    last_stamp = -1
    try:
        with Path(path).open("rb") as stream:
            for raw in stream:
                if len(raw) > 8192 or not raw.endswith(b"\n") or seen_end:
                    raise ValueError("partial_or_extra_proxy_record")
                row = strict_json(raw)
                event = row["event"]
                stamp = row["monotonic_ns"]
                if type(stamp) is not int or stamp < last_stamp:
                    raise ValueError("proxy_clock_invalid")
                last_stamp = stamp
                timestamp = datetime.fromisoformat(row["timestamp_utc"])
                if timestamp.tzinfo is None:
                    raise ValueError("proxy_utc_missing")
                key, dest = row.get("tunnel_id"), row.get("destination")
                if event == "start":
                    if seen_start or type(row.get("prior_bytes")) is not int or row.get("prior_bytes") != expected_prior_bytes or row.get("allowance_bytes") != DOWNLOAD_CEILING:
                        raise ValueError("proxy_start_differs")
                    seen_start = True
                elif not seen_start:
                    raise ValueError("proxy_start_missing")
                elif event == "listening":
                    if seen_listener or (expected_pid is not None and row.get("pid") != expected_pid):
                        raise ValueError("proxy_identity_differs")
                    if row.get("address", [None])[0] != "127.0.0.1":
                        raise ValueError("proxy_not_loopback")
                    seen_listener = True
                elif event == "acquisition_clock":
                    if not 0 < row["remaining_seconds"] <= ACQUISITION_SECONDS:
                        raise ValueError("proxy_clock_allowance")
                elif event in ("tunnel_start", "debit", "tunnel_end"):
                    if not isinstance(key, str) or not key or dest != "github.com:443":
                        raise ValueError("proxy_tunnel_identity")
                    if event == "tunnel_start":
                        if key in opened:
                            raise ValueError("duplicate_tunnel")
                        opened.add(key)
                        amounts[key] = 0
                    elif key not in opened or key in ended:
                        raise ValueError("proxy_tunnel_sequence")
                    elif event == "debit":
                        debit = row["bytes_read"]
                        if type(debit) is not int or debit <= 0:
                            raise ValueError("proxy_debit_invalid")
                        total += debit
                        amounts[key] += debit
                    else:
                        ended.add(key)
                    if row.get("tunnel_bytes") != amounts[key]:
                        raise ValueError("proxy_tunnel_total_differs")
                elif event == "end":
                    if row.get("status") != "closed_unqualified" or row.get("sockets_closed") is not True or opened != ended:
                        raise ValueError("proxy_terminal_failed_or_open_tunnels")
                    seen_end = True
                else:
                    raise ValueError("unexpected_proxy_record")
                if type(row.get("cumulative_bytes")) is not int or row["cumulative_bytes"] != total or total >= DOWNLOAD_CEILING:
                    raise ValueError("proxy_accounting_or_exhaustion")
        if not seen_start or not seen_listener or not seen_end:
            raise ValueError("proxy_terminal_missing")
        return total
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        raise ControllerFailure("proxy_ledger_invalid:" + str(error)) from error


class Journal:
    def __init__(self, path):
        self.stream = Path(path).open("x", encoding="utf-8", newline="\n")

    def emit(self, event, **data):
        row = dict(event=event, timestamp_utc=utc(), monotonic_ns=time.monotonic_ns(), **data)
        self.stream.write(json.dumps(row, sort_keys=True) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


class FileEvents:
    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.seen = False

    def read(self, terminal=False):
        try:
            with self.path.open("rb") as stream:
                self.seen = True
                if self.path.stat().st_size < self.offset:
                    raise ControllerFailure("worker_events_truncated")
                stream.seek(self.offset)
                data = stream.read(1024 * 1024)
        except FileNotFoundError:
            if terminal or self.seen:
                raise ControllerFailure("worker_events_missing") from None
            return []
        complete = data.rfind(b"\n") + 1
        tail = data[complete:]
        if len(tail) > 8192 or terminal and tail:
            raise ControllerFailure("worker_events_partial")
        rows = []
        for raw in data[:complete].splitlines():
            if len(raw) > 8192:
                raise ControllerFailure("worker_event_size_invalid")
            try:
                row = strict_json(raw)
                if not isinstance(row, dict) or not isinstance(row.get("event"), str):
                    raise ValueError("event structure")
            except ValueError as error:
                raise ControllerFailure("worker_events_malformed") from error
            rows.append(row)
        self.offset += complete
        return rows


def build_output_bytes(root):
    root = Path(root)
    try:
        info = root.lstat()
    except FileNotFoundError:
        return 0
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ControllerFailure("build_output_redirect")
    total = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        info = directory.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ControllerFailure("build_output_redirect")
        with os.scandir(directory) as entries:
            for entry in entries:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    raise ControllerFailure("build_output_redirect")
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode):
                    total += info.st_size
                else:
                    raise ControllerFailure("build_output_unmeasurable")
    return total


class ResourceSampler:
    def __init__(self, backend, root, clock=time.monotonic):
        self.backend, self.root, self.clock = backend, Path(root), clock
        self.value = None
        self.stop = threading.Event()
        self.thread = None
        self.seen_build = False

    def start(self):
        self.thread = threading.Thread(target=self._run, name="independent-resource-sampler", daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop.is_set():
            started = self.clock()
            try:
                job = self.backend.snapshot()
                host = self.backend.host_resources(self.root.anchor)
                build = self.root / "build"
                if self.seen_build and not build.exists():
                    raise ControllerFailure("build_output_disappeared")
                self.seen_build |= build.exists()
                size = build_output_bytes(build)
                self.value = dict(job, **host, sampled_mono=started,
                                  completed_mono=self.clock(), build_output_bytes=size)
            except BaseException as error:
                self.value = dict(sampled_mono=started, error=str(error))
                return
            self.stop.wait(POLL_SECONDS)

    def latest(self):
        return self.value

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(0.25)
            if self.thread.is_alive():
                raise ControllerFailure("resource_sampler_exit_unverified")


class Watchdog:
    def __init__(self, backend, clock=time.monotonic):
        self.backend, self.clock = backend, clock
        self.last_beat = clock()
        self.deadline = None
        self.failure = None
        self.stop = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, name="independent-owned-job-watchdog", daemon=True)
        self.thread.start()

    def beat(self, phase, state):
        self.last_beat = self.clock()
        self.deadline = (state.started_mono + ACQUISITION_SECONDS if phase == "acquisition"
                         else state.build_started_mono + BUILD_SECONDS)

    def _run(self):
        while not self.stop.wait(POLL_SECONDS):
            now = self.clock()
            if now - self.last_beat > OBSERVATION_AGE or self.deadline is not None and now >= self.deadline:
                self.failure = "controller_stale_or_phase_deadline"
                try:
                    self.backend.terminate()
                except BaseException as error:
                    self.failure += ":termination_failed:" + str(error)
                return

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(0.25)
            if self.thread.is_alive():
                raise ControllerFailure("watchdog_exit_unverified")


class PhaseMonitor:
    def __init__(self, plan, backend, emit):
        self.plan, self.backend, self.emit = plan, backend, emit
        self.children = {}
        self.exits = {}
        self.proxy = None
        self.proxy_closing = False
        self.started = self.complete = False
        self.terminal = None

    def accept(self, rows):
        already_exited = {(r.get("pid"), r.get("creation_time_100ns")) for r in rows if r.get("event") == "child_exit"}
        for row in rows:
            kind = row["event"]
            self.emit("worker_event", phase=self.plan["name"], record=row)
            if kind == "phase_start":
                if self.started or row.get("phase") != self.plan["name"]:
                    raise ControllerFailure("worker_phase_start_invalid")
                self.started = True
            elif kind == "worker_failure":
                raise ControllerFailure("worker_reported_failure:" + row.get("reason", "unknown"))
            elif not self.started:
                raise ControllerFailure("worker_phase_start_missing")
            elif kind == "child_started":
                pid, birth = row.get("pid"), row.get("creation_time_100ns")
                if type(pid) is not int or type(birth) is not int or birth <= 0 or row.get("in_any_job") is not True:
                    raise ControllerFailure("child_identity_or_membership_unknown")
                key = (pid, birth)
                if key in self.children:
                    raise ControllerFailure("duplicate_child_identity")
                self.children[key] = row
                if key not in already_exited:
                    self.backend.validate_pid(pid, birth)
            elif kind == "child_exit":
                key = row.get("pid"), row.get("creation_time_100ns")
                if key not in self.children or key in self.exits or row.get("in_any_job") is not True or row.get("exit_code") != 0:
                    raise ControllerFailure("child_exit_failed_or_unbound")
                self.exits[key] = row
                if self.proxy and key == (self.proxy.pid, self.proxy.creation_time_100ns) and not self.proxy_closing:
                    raise ControllerFailure("proxy_premature_exit")
            elif kind == "proxy_started":
                key = row.get("pid"), row.get("creation_time_100ns")
                if self.proxy is not None or key not in self.children:
                    raise ControllerFailure("proxy_identity_unbound")
                if key in already_exited:
                    from types import SimpleNamespace
                    self.proxy = SimpleNamespace(pid=key[0], creation_time_100ns=key[1])
                else:
                    self.proxy = self.backend.validate_pid(*key)
            elif kind == "proxy_closing":
                if self.proxy is None or row.get("pid") != self.proxy.pid or self.proxy_closing:
                    raise ControllerFailure("proxy_close_sequence_invalid")
                self.proxy_closing = True
            elif kind in ("acquisition_terminal", "build_terminal"):
                if self.terminal is not None or kind != self.plan["name"] + "_terminal":
                    raise ControllerFailure("phase_terminal_invalid")
                self.terminal = row
            elif kind == "phase_complete":
                if self.complete or row.get("phase") != self.plan["name"]:
                    raise ControllerFailure("phase_completion_invalid")
                self.complete = True
            else:
                raise ControllerFailure("unexpected_worker_event:" + kind)

    def poll_proxy(self):
        if self.proxy and not self.proxy_closing and self.backend.process_exit(self.proxy) is not None:
            raise ControllerFailure("proxy_premature_exit")

    def finish(self):
        if not self.complete or self.terminal is None or self.children.keys() != self.exits.keys():
            raise ControllerFailure("worker_terminal_or_child_exit_missing")
        if self.plan["name"] == "acquisition":
            if not self.proxy or not self.proxy_closing:
                raise ControllerFailure("proxy_lifecycle_missing")
            path = Path(self.plan["ledgerpath"])
            if Path(self.terminal.get("ledger_path", "")) != path:
                raise ControllerFailure("proxy_ledger_path_differs")
            total = validate_proxy_terminal(path, self.plan["expected_prior_bytes"], self.proxy.pid)
            if self.terminal.get("cumulative_bytes") != total or self.terminal.get("prior_bytes") != self.plan["expected_prior_bytes"]:
                raise ControllerFailure("worker_proxy_total_differs")
            if self.terminal.get("ledger_sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ControllerFailure("worker_proxy_ledger_hash_differs")
            return total
        manifest = Path(self.plan["artifact_manifest"])
        if (Path(self.terminal.get("artifact_manifest_path", "")) != manifest
                or self.terminal.get("artifact_manifest_sha256") != file_hash(manifest)):
            raise ControllerFailure("build_artifact_manifest_differs")
        entries = strict_json(manifest.read_text())
        if not isinstance(entries, list) or not entries or self.terminal.get("artifact_count") != len(entries):
            raise ControllerFailure("build_artifact_manifest_count_invalid")
        return None


def run_session(backend, sampler, phase_plans, clock=time.monotonic, sleep=time.sleep,
                journal=None, watchdog_factory=Watchdog):
    emit = journal.emit if journal else lambda *a, **k: None
    state = SafetyState(clock())
    guard = watchdog_factory(backend, clock=clock)
    result = dict(status="failure", started_utc=utc(), started_mono=state.started_mono,
                  downloaded_upper_bound_bytes=None, cleanup=None, reason=None)
    reason = None
    try:
        if [p["name"] for p in phase_plans] != ["acquisition", "build"]:
            raise ControllerFailure("fixed_two_phase_plan_required")
        guard.start()
        sampler.start()
        initial_deadline = clock() + OBSERVATION_AGE
        while sampler.latest() is None and clock() < initial_deadline:
            sleep(POLL_SECONDS)
        state.assess("acquisition", clock(), sampler.latest())
        emit("controller_start", acquisition_started_mono=state.started_mono,
             acquisition_started_utc=result["started_utc"], memory_metric="job_committed_bytes")
        for plan in phase_plans:
            phase = plan["name"]
            if phase == "build":
                state.start_build(clock())
            guard.beat(phase, state)
            state.assess(phase, clock(), sampler.latest())
            if plan.get("prepare"):
                plan["prepare"](result["started_utc"])
            worker = backend.launch(plan["argv"], plan["cwd"], plan["env"], plan["stdoutfile"], plan["stderrfile"])
            backend.validate_pid(worker.pid, worker.creation_time_100ns)
            emit("phase_worker", phase=phase, pid=worker.pid, creation_time_100ns=worker.creation_time_100ns)
            reader = plan.get("events_reader") or FileEvents(plan["events"])
            monitor = PhaseMonitor(plan, backend, emit)
            while True:
                guard.beat(phase, state)
                if guard.failure:
                    raise ControllerFailure(guard.failure)
                observation = sampler.latest()
                state.assess(phase, clock(), observation)
                emit("resources", phase=phase, observation=observation)
                if hasattr(backend, "drain_events"):
                    for event in backend.drain_events():
                        emit("ownership", record=event)
                monitor.accept(reader.read())
                monitor.poll_proxy()
                exit_code = backend.process_exit(worker)
                if exit_code is not None:
                    monitor.accept(reader.read(terminal=True))
                    if exit_code != 0:
                        raise ControllerFailure("phase_worker_exit:" + str(exit_code))
                    if backend.snapshot()["active_processes"] != 0:
                        raise ControllerFailure("active_descendants_after_worker_exit")
                    total = monitor.finish()
                    state.assess(phase, clock(), sampler.latest())
                    if total is not None:
                        result["downloaded_upper_bound_bytes"] = total
                    emit("phase_complete", phase=phase, elapsed_seconds=clock() - (
                        state.started_mono if phase == "acquisition" else state.build_started_mono))
                    break
                sleep(POLL_SECONDS)
    except BaseException as error:
        reason = "controller_interrupted" if isinstance(error, KeyboardInterrupt) else str(error)
        try:
            backend.terminate()
        except BaseException as stop_error:
            reason += ";termination_failed:" + str(stop_error)
    finally:
        for component in (sampler, guard):
            try:
                component.close()
            except BaseException as error:
                reason = (reason or "") + ";monitor_exit_failed:" + str(error)
                try:
                    backend.terminate()
                except BaseException:
                    pass
        try:
            result["cleanup"] = backend.cleanup()
            if not result["cleanup"].get("verified"):
                reason = (reason or "") + ";owned_job_cleanup_unverified"
        except BaseException as error:
            result["cleanup"] = dict(verified=False, errors=[str(error)])
            reason = (reason or "") + ";owned_job_cleanup_failed"
        try:
            backend.close()
        except BaseException as error:
            reason = (reason or "") + ";job_handle_close_failed:" + str(error)
        if guard.failure:
            reason = reason or guard.failure
        result.update(status="failure" if reason else "controlled_phases_passed",
                      reason=reason, ended_utc=utc(), ended_mono=clock(),
                      acquisition_started_mono=state.started_mono,
                      build_started_mono=state.build_started_mono)
        try:
            emit("controller_end", result=result)
        except BaseException as error:
            result.update(status="failure", reason="controller_terminal_log_failed:" + str(error))
    return result


FROZEN_CONFIG_SHA256 = "c4610156c24e95cdf1abab658cfde1c18be568940c7cb952c5a673833c620cf4"
FIXED_ROOT = r"C:\Resolena\gn1-20261025"
HELPER_NAMES = {"controller.py", "windows_job.py", "worker.py", "standins.py"}


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def local_module(name):
    import types
    path = Path(__file__).with_name(name + ".py")
    qualified = "_granite_controller_" + name
    module = types.ModuleType(qualified)
    module.__file__ = str(path)
    sys.modules[qualified] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def validate_native_config(config, helper_dir):
    import ntpath
    try:
        if config.get("execution_authorized") is not True or not config.get("owner"):
            raise ValueError("native_execution_not_authorized")
        if ntpath.normcase(config["root"]) != ntpath.normcase(FIXED_ROOT):
            raise ValueError("fixed_native_root_required")
        if set(config["helper_hashes"]) != HELPER_NAMES:
            raise ValueError("controller_manifest_incomplete")
        for name, expected in config["helper_hashes"].items():
            if file_hash(Path(helper_dir) / name) != expected:
                raise ValueError("controller_helper_hash_differs:" + name)
        if file_hash(config["frozen_config"]) != FROZEN_CONFIG_SHA256:
            raise ValueError("frozen_config_differs")
        frozen = json.loads(Path(config["frozen_config"]).read_text())
        expected = {"acquisition_seconds": ACQUISITION_SECONDS, "acquisition_total_bytes": DOWNLOAD_CEILING,
                    "build_seconds": BUILD_SECONDS, "build_output_bytes": OUTPUT_CAP,
                    "maximum_build_process_memory_bytes": MEMORY_CAP, "build_parallelism": 2,
                    "initial_disk_free_bytes": INITIAL_DISK, "stop_disk_free_below_bytes": DISK_FLOOR,
                    "stop_host_free_below_bytes": HOST_FLOOR}
        if any(frozen["operational_limits"][key] != value for key, value in expected.items()):
            raise ValueError("frozen_limit_mismatch")
        worker = local_module("worker")
        module = worker.load_proxy(dict(config, proxy_sha256=PROXY_SHA256))
        prior = module.load_prior(config["prior_receipt"], config["prior_sha256"])
        return dict(config, prior_bytes=prior, proxy_sha256=PROXY_SHA256)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        raise ControllerFailure("native_preflight_failed:" + str(error)) from error


def native_run(config_path, output):
    if os.name != "nt" or sys.version_info[:3] != (3, 12, 11):
        raise ControllerFailure("approved_windows_python_3_12_11_required")
    helper_dir = Path(__file__).resolve().parent
    config = validate_native_config(strict_json(Path(config_path).read_text()), helper_dir)
    worker = local_module("worker")
    environment = worker.validate_environment(os.environ)
    root = Path(config["root"])
    if root.exists():
        raise ControllerFailure("fresh_fixed_native_root_required")
    output = Path(output)
    if output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve()):
        raise ControllerFailure("controller_evidence_must_be_outside_native_root")
    output.mkdir(parents=True, exist_ok=False)
    journal = Journal(output / "controller.jsonl")
    backend = None
    try:
        backend = local_module("windows_job").WindowsJob(memory_limit_bytes=MEMORY_CAP)
        worker_config = output / "worker-config.json"
        def prepare(original_start):
            (root / "evidence").mkdir(parents=True, exist_ok=False)
            worker.write_json(worker_config, {key: value for key, value in dict(
                config, original_start_utc=original_start).items() if key not in ("environment",)})
        plans = []
        for phase in ("acquisition", "build"):
            events = output / (phase + ".events.jsonl")
            plan = dict(name=phase, argv=[sys.executable, "-I", str(helper_dir / "worker.py"),
                        "--phase", phase, "--config", str(worker_config), "--events", str(events)],
                        cwd=str(root), env=environment, stdoutfile=output / (phase + ".stdout.log"),
                        stderrfile=output / (phase + ".stderr.log"), events=events,
                        expected_prior_bytes=config["prior_bytes"], ledgerpath=root / "evidence/acquisition-proxy.jsonl",
                        artifact_manifest=root / "evidence/built-artifacts.json")
            if phase == "acquisition":
                plan["prepare"] = prepare
            plans.append(plan)
        result = run_session(backend, ResourceSampler(backend, root), plans, journal=journal)
        result["scope"] = "source_acquisition_and_model_free_native_build_only"
        worker.write_json(output / "result.json", result)
        return result
    finally:
        if backend and backend.handle is not None:
            backend.close()
        journal.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ownership = commands.add_parser("ownership-self-test")
    ownership.add_argument("--output", required=True, type=Path)
    native = commands.add_parser("native")
    native.add_argument("--config", required=True, type=Path)
    native.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "ownership-self-test":
        result = local_module("standins").run_ownership_selftest(args.output)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ownership_self_test_passed") else 1
    result = native_run(args.config, args.output)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "controlled_phases_passed" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ControllerFailure, OSError, ValueError) as error:
        print(json.dumps(dict(status="failure", reason=str(error))), file=sys.stderr, flush=True)
        raise SystemExit(1)
