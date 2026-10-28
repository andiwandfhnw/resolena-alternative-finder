import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.uc001_granite_controller.standins import StandinFailure, run_ownership_selftest


class Clock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


class FakeApi:
    def __init__(self, unrelated, calls):
        self.unrelated = unrelated
        self.calls = calls

    def controller_in_job(self, handle):
        return False

    def open_process(self, pid):
        assert pid == 900
        self.calls.append("retain_unrelated_identity")
        return "unrelated-query-handle"

    def creation_time(self, handle):
        assert handle == "unrelated-query-handle"
        return 600

    def in_job(self, handle, job):
        assert handle == "unrelated-query-handle"
        return False

    def close_handle(self, handle):
        self.calls.append("close_unrelated_query")


class FakeUnrelated:
    def __init__(self, argv, calls, job_ref, die_with_job=False, **kwargs):
        self.pid = 900
        self.calls = calls
        self.job_ref = job_ref
        self.die_with_job = die_with_job
        self.ended = False
        directory = Path(argv[argv.index("--events") + 1])
        (directory / "unrelated.identity.json").write_text(json.dumps({
            "role": "unrelated", "pid": 900, "creation_time_100ns": 600, "parent_pid": os.getpid(),
            "timestamp_utc": "2026-10-25T20:00:00+00:00", "monotonic_ns": 1,
        }))
        calls.append("unrelated_started")

    def poll(self):
        if self.ended or (self.die_with_job and self.job_ref[0].killed):
            return 1
        return None

    def terminate(self):
        self.calls.append("terminate_unrelated_retained_process")
        self.ended = True

    def wait(self, timeout=None):
        assert self.ended
        return 1


class FakeJob:
    def __init__(self, api, calls, *, missing_grandchild=False, bad_order=False,
                 cleanup_verified=True, identity_mismatch=False, interrupt=False, wrong_parent=False, wrong_root=False):
        self.api = api
        self.calls = calls
        self.handle = "private-job"
        self.killed = False
        self.missing_grandchild = missing_grandchild
        self.bad_order = bad_order
        self.cleanup_verified = cleanup_verified
        self.identity_mismatch = identity_mismatch
        self.interrupt = interrupt
        self.wrong_parent = wrong_parent
        self.wrong_root = wrong_root
        self.root = SimpleNamespace(pid=101, creation_time_100ns=10001, resumed=True, assigned=True)
        self.members = [(101, 10001), (102, 10002), (103, 10003)]
        self.calls.append("private_job_created")

    def launch(self, argv, cwd, env, stdoutfile, stderrfile, **kwargs):
        self.calls.append("owned_root_launched_once")
        assert "-I" in argv and argv[argv.index("--child-role") + 1] == "root"
        directory = Path(argv[argv.index("--events") + 1])
        roles = ["root", "child"] if self.missing_grandchild else ["root", "child", "grandchild"]
        for role, (pid, created) in zip(roles, self.members):
            if self.identity_mismatch and role == "child":
                created += 1
            if self.wrong_root:
                if role == "root":
                    pid, created = self.members[1]
                elif role == "child":
                    pid, created = self.members[0]
            parent = os.getpid() if role == "root" else (102 if self.wrong_root else 101) if role == "child" else (101 if self.wrong_root else 102)
            if self.wrong_parent and role == "grandchild":
                parent = 9999
            (directory / f"{role}.identity.json").write_text(json.dumps({
                "role": role, "pid": pid, "creation_time_100ns": created, "parent_pid": parent,
                "timestamp_utc": "2026-10-25T20:00:00+00:00", "monotonic_ns": pid,
            }))
        return self.root

    def drain_events(self):
        names = ["worker_created_suspended", "worker_assigned", "worker_resumed"]
        if self.bad_order:
            names = ["worker_created_suspended", "worker_resumed", "worker_assigned"]
        return [dict(event=name, pid=101, creation_time_100ns=10001) for name in names]

    def snapshot(self):
        if self.interrupt:
            raise KeyboardInterrupt()
        return dict(active_processes=0 if self.killed else len(self.members), owned=[
            dict(pid=pid, creation_time_100ns=created, in_job=True,
                 resumed=True, exit_code=1 if self.killed else None)
            for pid, created in self.members
        ])

    def validate_pid(self, pid, creation_time_100ns=None):
        if (pid, creation_time_100ns) not in self.members:
            raise RuntimeError("identity mismatch")
        return SimpleNamespace(pid=pid, creation_time_100ns=creation_time_100ns)

    def process_exit(self, process):
        return 1 if self.killed else None

    def terminate(self):
        self.calls.append("terminate_private_job_only")
        self.killed = True

    def cleanup(self, timeout_seconds=5):
        self.calls.append("job_cleanup")
        return dict(verified=self.cleanup_verified,
                    active_processes=0 if self.cleanup_verified else 1,
                    owned_exits=[dict(pid=pid, creation_time_100ns=created, exit_code=1)
                                 for pid, created in self.members], errors=[])

    def close(self):
        self.calls.append("private_job_closed")


def run_fake(tmp_path, **job_options):
    calls = []
    job_ref = []
    unrelated = []
    die_with_job = job_options.pop("die_with_job", False)
    clock = Clock()
    api = FakeApi(unrelated, calls)
    def job_factory():
        job = FakeJob(api, calls, **job_options)
        job_ref.append(job)
        return job
    def popen_factory(argv, **kwargs):
        process = FakeUnrelated(argv, calls, job_ref, die_with_job=die_with_job, **kwargs)
        unrelated.append(process)
        return process
    result = run_ownership_selftest(tmp_path / "selftest", python_exe="synthetic-python.exe",
                                    job_factory=job_factory, popen_factory=popen_factory,
                                    clock=clock, sleep=clock.sleep)
    return result, calls


def test_synthetic_selftest_verifies_three_nested_identities_and_unrelated_survival(tmp_path):
    result, calls = run_fake(tmp_path)
    assert result["ownership_self_test_passed"] is True
    assert result["windows_execution"] is False
    assert result["unrelated_survived"] is True
    assert result["cleanup"]["verified"] is True
    assert len(result["owned_identities"]) == 3
    assert calls.count("owned_root_launched_once") == 1
    assert calls.index("terminate_private_job_only") < calls.index("terminate_unrelated_retained_process")
    assert (tmp_path / "selftest/result.json").is_file()
    assert (tmp_path / "selftest/controller.jsonl").is_file()


def test_wrong_assignment_order_never_credits_ownership(tmp_path):
    result, calls = run_fake(tmp_path, bad_order=True)
    assert result["ownership_self_test_passed"] is False
    assert calls.count("owned_root_launched_once") == 1
    assert "terminate_private_job_only" in calls


def test_creation_identity_mismatch_is_failure(tmp_path):
    result, calls = run_fake(tmp_path, identity_mismatch=True)
    assert result["ownership_self_test_passed"] is False
    assert "identity" in result["failure_reason"].lower()
    assert "terminate_private_job_only" in calls


def test_cleanup_with_active_descendants_is_not_success(tmp_path):
    result, _ = run_fake(tmp_path, cleanup_verified=False)
    assert result["ownership_self_test_passed"] is False
    assert result["cleanup"]["active_processes"] == 1


def test_unrelated_process_death_is_not_credited_as_safe_cleanup(tmp_path):
    result, _ = run_fake(tmp_path, die_with_job=True)
    assert result["ownership_self_test_passed"] is False
    assert result["unrelated_survived"] is False


def test_missing_descendant_times_out_without_retry_and_kills_only_private_job(tmp_path):
    result, calls = run_fake(tmp_path, missing_grandchild=True)
    assert result["ownership_self_test_passed"] is False
    assert "deadline" in result["failure_reason"].lower()
    assert calls.count("owned_root_launched_once") == 1
    assert calls.count("terminate_private_job_only") == 1


def test_controller_interruption_still_cleans_owned_job_and_owned_unrelated_standin(tmp_path):
    result, calls = run_fake(tmp_path, interrupt=True)
    assert result["ownership_self_test_passed"] is False
    assert "interrupt" in result["failure_reason"].lower()
    assert "terminate_private_job_only" in calls
    assert "terminate_unrelated_retained_process" in calls


def test_existing_output_is_never_replaced(tmp_path):
    directory = tmp_path / "existing"
    directory.mkdir()
    marker = directory / "old.txt"
    marker.write_text("historical")
    with pytest.raises((FileExistsError, StandinFailure)):
        run_ownership_selftest(directory, job_factory=lambda: pytest.fail("do not launch"))
    assert marker.read_text() == "historical"


def test_linux_default_route_performs_no_native_windows_or_subprocess_operation(tmp_path):
    import os
    if os.name == "nt":
        pytest.skip("Linux guard test")
    with pytest.raises(StandinFailure):
        run_ownership_selftest(tmp_path / "must-not-launch")
    assert not (tmp_path / "must-not-launch").exists()


def test_owned_role_root_must_match_the_launched_retained_process(tmp_path):
    result, _ = run_fake(tmp_path, wrong_root=True)
    assert result["ownership_self_test_passed"] is False


def test_nested_membership_requires_the_actual_parent_chain(tmp_path):
    result, _ = run_fake(tmp_path, wrong_parent=True)
    assert result["ownership_self_test_passed"] is False


def test_standin_children_keep_separate_logs_without_launching_a_real_process(tmp_path, monkeypatch):
    from scripts.uc001_granite_controller import standins as module
    clock = Clock()
    child = SimpleNamespace(ended=False)
    child.poll = lambda: 1 if child.ended else None
    child.terminate = lambda: setattr(child, "ended", True)
    child.wait = lambda timeout: 1
    seen = {}
    def popen(argv, **kwargs):
        seen.update(kwargs)
        assert Path(kwargs["stdout"].name).name == "child.stdout.log"
        assert Path(kwargs["stderr"].name).name == "child.stderr.log"
        return child
    api = SimpleNamespace(k=SimpleNamespace(GetCurrentProcess=lambda: "self"), creation_time=lambda _: 42)
    monkeypatch.setattr(module, "_native_guard", lambda: None)
    monkeypatch.setattr(module, "_job_module", lambda: SimpleNamespace(NativeApi=lambda: api))
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    monkeypatch.setattr(module.time, "monotonic", clock)
    monkeypatch.setattr(module.time, "sleep", clock.sleep)
    module._child("root", tmp_path, 0.1, "synthetic-python.exe")
    assert child.ended
    assert (tmp_path / "root.identity.json").is_file()
    assert (tmp_path / "child.stdout.log").is_file()
    assert seen["close_fds"] is True
