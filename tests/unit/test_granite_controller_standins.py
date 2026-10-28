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
    if "cleanup_verified" in job_options:
        job_options["cleanup_unverified"] = not job_options.pop("cleanup_verified")
    if "wrong_parent" in job_options:
        job_options["wrong_owned_parent"] = job_options.pop("wrong_parent")
    with pytest.MonkeyPatch.context() as monkeypatch:
        return run_split(tmp_path, monkeypatch, **job_options)


def test_synthetic_selftest_verifies_three_nested_identities_and_unrelated_survival(tmp_path):
    result, calls = run_fake(tmp_path)
    assert result["ownership_self_test_passed"] is True
    assert result["windows_execution"] is False
    assert result["unrelated_survived"] is True
    assert result["cleanup"]["verified"] is True
    assert len(result["owned_identities"]) == 6
    assert calls.count("owned_root_launched_once") == 1
    assert calls.index("terminate_private_job_only") < calls.index(("terminate_identity", LAUNCHER))
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
    assert ("terminate_identity", LAUNCHER) in calls


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
    child = SimpleNamespace(ended=False, pid=102, _handle=102)
    child.poll = lambda: 1 if child.ended else None
    child.terminate = lambda: setattr(child, "ended", True)
    child.wait = lambda timeout: 1
    seen = {}
    def popen(argv, **kwargs):
        seen.update(kwargs)
        assert Path(kwargs["stdout"].name).name == "child.stdout.log"
        assert Path(kwargs["stderr"].name).name == "child.stderr.log"
        return child
    api = SimpleNamespace(
        k=SimpleNamespace(GetCurrentProcess=lambda: "self"),
        creation_time=lambda handle: 42 if handle == "self" else 43,
        process_id=lambda handle: os.getpid() if handle == "self" else 102,
        parent_pid=lambda handle: os.getppid() if handle == "self" else os.getpid(),
        open_process=lambda pid, **kwargs: "child-launcher",
        close_handle=lambda handle: None,
    )
    monkeypatch.setattr(module, "_native_guard", lambda: None)
    monkeypatch.setattr(module, "_job_module", lambda: SimpleNamespace(NativeApi=lambda: api))
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    monkeypatch.setattr(module.time, "monotonic", clock)
    monkeypatch.setattr(module.time, "sleep", clock.sleep)
    module._child("root", tmp_path, 0.1, "synthetic-python.exe")
    assert child.ended
    assert (tmp_path / "root.identity.json").is_file()
    assert (tmp_path / "child.stdout.log").is_file()
    launcher = json.loads((tmp_path / "child.launcher.identity.json").read_text())
    assert (launcher["pid"], launcher["creation_time_100ns"], launcher["parent_pid"]) == (102, 43, os.getpid())
    assert seen["close_fds"] is True


CONTROLLER = 60320
LAUNCHER = 61196
LAUNCHER_BIRTH = 134374354509552652
INTERPRETER = 61020
INTERPRETER_BIRTH = 134374354509736275
SPLIT_OWNED = {
    'root': ((101, 134374354509800000, CONTROLLER), (201, 134374354509810000, 101)),
    'child': ((102, 134374354509820000, 201), (202, 134374354509830000, 102)),
    'grandchild': ((103, 134374354509840000, 202), (203, 134374354509850000, 103)),
}


class SplitApi:
    def __init__(self, calls, options):
        self.calls, self.options, self.reads, self.processes = calls, options, {}, {}
        self.add(LAUNCHER, LAUNCHER_BIRTH, CONTROLLER, False, 'launcher', 'unrelated')
        self.add(INTERPRETER, INTERPRETER_BIRTH, LAUNCHER, False, 'interpreter', 'unrelated')
    def add(self, pid, birth, parent, member, kind, role, alive=True):
        self.processes[pid] = dict(pid=pid,creation_time_100ns=birth,parent_pid=parent,
                                   member=member,kind=kind,role=role,alive=alive)
    def controller_in_job(self, handle):
        return False
    def open_process(self, pid, **kwargs):
        if pid not in self.processes:
            raise RuntimeError('unknown process')
        self.calls.append(('open_process',pid,kwargs))
        return f'handle-{pid}'
    def process_id(self, handle):
        return int(handle.removeprefix('handle-'))
    def parent_pid(self, handle):
        return self.processes[self.process_id(handle)]['parent_pid']
    def creation_time(self, handle):
        pid=self.process_id(handle);self.reads[pid]=self.reads.get(pid,0)+1
        changed=(pid==LAUNCHER and self.options.get('changed_launcher_creation')
                 or pid==INTERPRETER and self.options.get('changed_interpreter_creation'))
        return self.processes[pid]['creation_time_100ns']+(1 if changed and self.reads[pid]>=2 else 0)
    def in_job(self, handle, job):
        return self.processes[self.process_id(handle)]['member']
    def exit_code(self, handle):
        return None if self.processes[self.process_id(handle)]['alive'] else 1
    def terminate_process(self, handle):
        pid=self.process_id(handle);self.calls.append(('terminate_identity',pid))
        stuck=(pid==LAUNCHER and self.options.get('launcher_stuck')
               or pid==INTERPRETER and self.options.get('interpreter_stuck'))
        if not stuck:
            self.processes[pid]['alive']=False
    def children_of(self, parents, timeout_seconds=None):
        result={(pid,row['parent_pid']) for pid,row in self.processes.items()
                if row['alive'] and row['parent_pid'] in parents}
        after_stop = (self.options.get('unknown_after_job') and self.options.get('job_ref')
                      and self.options['job_ref'][0].killed)
        if self.options.get('unknown_outside') or after_stop:
            result.add((98765,LAUNCHER))
        return result
    def close_handle(self, handle):
        self.calls.append(('close_handle',self.process_id(handle)))


class SplitUnrelated:
    def __init__(self, argv, api, calls, jobs, **kwargs):
        self.pid,self._handle=LAUNCHER,f'handle-{LAUNCHER}'
        self.api,self.calls,self.jobs=api,calls,jobs
        directory=Path(argv[argv.index('--events')+1])
        if not api.options.get('missing_interpreter'):
            parent=CONTROLLER if api.options.get('wrong_parent') else LAUNCHER
            (directory/'unrelated.identity.json').write_text(json.dumps(dict(
                role='unrelated',pid=INTERPRETER,creation_time_100ns=INTERPRETER_BIRTH,
                parent_pid=parent,timestamp_utc='2026-10-25T20:00:00+00:00',monotonic_ns=1)))
        calls.append('unrelated_started')
    def poll(self):
        if self.api.options.get('die_with_job') and self.jobs[0].killed:
            self.api.processes[LAUNCHER]['alive']=False
            self.api.processes[INTERPRETER]['alive']=False
        return self.api.exit_code(self._handle)
    def terminate(self):
        self.calls.append('terminate_unrelated_retained_process')
        self.api.terminate_process(self._handle)
    def wait(self, timeout=None):
        if self.poll() is None:
            raise TimeoutError('retained launcher has not exited')
        return 1


class SplitJob:
    def __init__(self, api, calls, options):
        self.api,self.calls,self.options=api,calls,options
        self.handle,self.killed,self.launched='private-job',False,False
        self.snapshot_calls=0
        self.members=[]
        for role,pair in SPLIT_OWNED.items():
            for kind,(pid,birth,parent) in zip(('launcher','interpreter'),pair):
                self.members.append((pid,birth));api.add(pid,birth,parent,True,kind,role,alive=False)
        if options.get('unknown_extra'):
            self.members.append((999,134374354509900000));api.add(999,134374354509900000,201,True,'unknown','unknown',alive=False)
        self.root=SimpleNamespace(pid=101,creation_time_100ns=SPLIT_OWNED['root'][0][1],
                                  handle='handle-101',resumed=True,assigned=True)
        calls.append('private_job_created')
    def launch(self, argv, cwd, env, stdoutfile, stderrfile, **kwargs):
        self.calls.append('owned_root_launched_once');self.launched=True
        for pid,_ in self.members:
            self.api.processes[pid]['alive']=True
        directory=Path(argv[argv.index('--events')+1])
        for role,pair in SPLIT_OWNED.items():
            if role=='grandchild' and self.options.get('missing_grandchild'):
                continue
            for kind,(pid,birth,parent) in zip(('launcher','interpreter'),pair):
                if kind=='interpreter' and role=='child' and self.options.get('identity_mismatch'):
                    birth+=1
                if kind=='interpreter' and role=='root' and self.options.get('wrong_root'):
                    pid,birth,parent=SPLIT_OWNED['child'][1]
                if kind=='interpreter' and role=='grandchild' and self.options.get('wrong_owned_parent'):
                    parent=9999
                name=f'{role}.identity.json' if kind=='interpreter' else f'{role}.launcher.identity.json'
                (directory/name).write_text(json.dumps(dict(role=role,kind=kind,pid=pid,
                    creation_time_100ns=birth,parent_pid=parent,timestamp_utc='2026-10-25T20:00:00+00:00',monotonic_ns=pid)))
        return self.root
    def drain_events(self):
        names=['worker_created_suspended','worker_assigned','worker_resumed']
        if self.options.get('bad_order'):
            names=['worker_created_suspended','worker_resumed','worker_assigned']
        return [dict(event=name,pid=101,creation_time_100ns=SPLIT_OWNED['root'][0][1]) for name in names]
    def snapshot(self):
        if self.options.get('interrupt'):
            raise KeyboardInterrupt()
        self.snapshot_calls+=1
        observed=self.members
        if self.options.get('first_snapshot_five') and self.snapshot_calls==1 and self.launched and not self.killed:
            observed=self.members[:-1]
        return dict(total_processes=len(observed) if self.launched else 0,
                    active_processes=sum(self.api.processes[p]['alive'] for p,b in observed),owned=[
            dict(pid=p,creation_time_100ns=b,in_job=True,resumed=True,
                 exit_code=None if self.api.processes[p]['alive'] else 1)
            for p,b in observed if self.launched])
    def validate_pid(self, pid, creation_time_100ns=None):
        if (pid,creation_time_100ns) not in self.members:
            raise RuntimeError('identity mismatch')
        return SimpleNamespace(pid=pid,creation_time_100ns=creation_time_100ns,handle=f'handle-{pid}',assigned=True,resumed=True)
    def process_exit(self, process):
        return self.api.exit_code(f'handle-{process.pid}')
    def terminate(self):
        self.calls.append('terminate_private_job_only');self.killed=True
        for pid,_ in self.members:
            self.api.processes[pid]['alive']=False
        if self.options.get('die_with_job'):
            self.api.processes[LAUNCHER]['alive']=False
            self.api.processes[INTERPRETER]['alive']=False
    def cleanup(self, timeout_seconds=5):
        self.calls.append('job_cleanup');verified=not self.options.get('cleanup_unverified')
        subset=self.options.get('owned_cleanup_only')
        return dict(verified=verified,active_processes=0 if verified else 1,errors=[],
            total_processes=(len(self.members)+(1 if self.options.get('late_unknown_cleanup') else 0)) if self.launched else 0,
            owned_exits=[dict(pid=p,creation_time_100ns=b,
                exit_code=1 if subset is None or self.api.processes[p]['kind']==subset else None)
                for p,b in self.members if self.launched])
    def close(self):
        self.calls.append('private_job_closed')


def run_split(tmp_path, monkeypatch, **options):
    from scripts.uc001_granite_controller import standins as module
    monkeypatch.setattr(module.os,'getpid',lambda:CONTROLLER)
    calls,jobs=[],[]
    options=dict(options,job_ref=jobs)
    api=SplitApi(calls,options)
    def job_factory():
        job=SplitJob(api,calls,options);jobs.append(job);return job
    def popen_factory(argv,**kwargs):
        return SplitUnrelated(argv,api,calls,jobs,**kwargs)
    clock=Clock()
    result=run_ownership_selftest(tmp_path/'selftest',python_exe='synthetic-python.exe',
        job_factory=job_factory,popen_factory=popen_factory,clock=clock,sleep=clock.sleep)
    return result,calls


def test_exact_owner_launcher_split_has_two_unrelated_and_six_owned_identities(tmp_path,monkeypatch):
    result,calls=run_split(tmp_path,monkeypatch)
    assert result['ownership_self_test_passed'] is True
    assert result['controller_pid']==60320
    identities={(r['kind'],r['pid'],r['creation_time_100ns'],r['parent_pid'])
                for r in result['unrelated_identities']}
    assert identities=={('launcher',61196,134374354509552652,60320),
                        ('interpreter',61020,134374354509736275,61196)}
    assert len(result['owned_identities'])==6
    assert {r['kind'] for r in result['owned_identities']}=={'launcher','interpreter'}
    assert {(r['pid'],r['creation_time_100ns']) for r in result['owned_identities']}=={
        (pid,birth) for pair in SPLIT_OWNED.values() for pid,birth,parent in pair}
    assert result['windows_execution'] is False
    assert result['cleanup']['verified'] is True
    assert result['unrelated_survived'] and result['unrelated_cleanup_verified']
    assert {r['pid']:r['exit_code'] for r in result['unrelated_exits']}=={61196:1,61020:1}
    assert calls.count('owned_root_launched_once')==1


@pytest.mark.parametrize('option',['wrong_parent','changed_launcher_creation','changed_interpreter_creation',
    'missing_interpreter','identity_mismatch','wrong_root','wrong_owned_parent','unknown_extra','unknown_outside'])
def test_split_unknown_or_changed_identity_fails_closed(tmp_path,monkeypatch,option):
    result,calls=run_split(tmp_path,monkeypatch,**{option:True})
    assert result['ownership_self_test_passed'] is False
    assert 'terminate_private_job_only' in calls
    assert calls.count('owned_root_launched_once')<=1


@pytest.mark.parametrize('stuck',['launcher_stuck','interpreter_stuck'])
def test_split_unrelated_cleanup_requires_both_exits(tmp_path,monkeypatch,stuck):
    result,calls=run_split(tmp_path,monkeypatch,**{stuck:True})
    assert result['ownership_self_test_passed'] is False
    assert result['unrelated_cleanup_verified'] is False


@pytest.mark.parametrize('kind',['launcher','interpreter'])
def test_split_owned_cleanup_requires_both_kinds(tmp_path,monkeypatch,kind):
    result,calls=run_split(tmp_path,monkeypatch,owned_cleanup_only=kind)
    assert result['ownership_self_test_passed'] is False


def test_unknown_outside_process_after_private_job_termination_is_not_ignored(tmp_path,monkeypatch):
    result,calls=run_split(tmp_path,monkeypatch,unknown_after_job=True)
    assert result['ownership_self_test_passed'] is False
    assert result['unrelated_cleanup_verified'] is False
    assert ('terminate_identity',98765) not in calls


def test_watchdog_stops_both_outside_handles_when_job_observation_blocks(tmp_path,monkeypatch):
    import threading
    import time
    from scripts.uc001_granite_controller import standins as module
    monkeypatch.setattr(module.os,'getpid',lambda:CONTROLLER)
    calls,jobs=[],[]
    released=threading.Event()
    class SignalingApi(SplitApi):
        def terminate_process(self,handle):
            super().terminate_process(handle)
            if self.process_id(handle)==INTERPRETER:
                released.set()
    api=SignalingApi(calls,{})
    class BlockedJob(SplitJob):
        def snapshot(self):
            released.wait(0.6)  # bounded fallback for the original missing watchdog path
            return super().snapshot()
    def job_factory():
        job=BlockedJob(api,calls,{});jobs.append(job);return job
    def popen_factory(argv,**kwargs):
        return SplitUnrelated(argv,api,calls,jobs,**kwargs)
    started=time.monotonic()
    result=run_ownership_selftest(tmp_path/'selftest',python_exe='synthetic-python.exe',
        job_factory=job_factory,popen_factory=popen_factory,
        clock=time.monotonic,sleep=time.sleep,timeout_seconds=0.1)
    assert result['ownership_self_test_passed'] is False
    assert result['windows_execution'] is False
    assert released.is_set()
    assert 'terminate_private_job_only' in calls
    assert ('terminate_identity',LAUNCHER) in calls
    assert ('terminate_identity',INTERPRETER) in calls
    assert time.monotonic()-started<0.5


def test_unknown_process_in_final_job_total_prevents_cleanup_success(tmp_path,monkeypatch):
    result,calls=run_split(tmp_path,monkeypatch,late_unknown_cleanup=True)
    assert result['ownership_self_test_passed'] is False
    assert result['cleanup']['total_processes']==7
    assert result['cleanup']['active_processes']==0


def test_membership_is_refreshed_after_all_six_handles_are_verified(tmp_path,monkeypatch):
    result,calls=run_split(tmp_path,monkeypatch,first_snapshot_five=True)
    assert result['ownership_self_test_passed'] is True
    assert len(result['owned_identities'])==6
    assert result['cleanup']['total_processes']==6


def edge_diagnostic_rows(tmp_path):
    rows=[json.loads(line) for line in (tmp_path/'selftest/controller.jsonl').read_text().splitlines()]
    return rows,[row for row in rows if row['event']=='scoped_child_edges']


def test_edge_diagnostic_expected_pair_only_has_bounded_timestamped_evidence(tmp_path,monkeypatch):
    original=SplitApi.children_of
    queries=[]
    def scoped(self,parents,timeout_seconds=None):
        queries.append(set(parents))
        self.add(77777,999,88888,False,'unrelated-system-name','unrelated-system-role')
        return original(self,parents,timeout_seconds)
    monkeypatch.setattr(SplitApi,'children_of',scoped)
    result,calls=run_split(tmp_path,monkeypatch)
    assert result['ownership_self_test_passed'] is True
    rows,observations=edge_diagnostic_rows(tmp_path)
    assert observations
    owned_parents={pid for pair in SPLIT_OWNED.values() for pid,birth,parent in pair}
    assert all(parents in ({LAUNCHER,INTERPRETER},owned_parents) for parents in queries)
    for row in observations:
        assert row['status']=='observed'
        assert '77777' not in json.dumps(row)
        assert 'unrelated-system-name' not in json.dumps(row)
        if {ref['parent_pid'] for ref in row['scoped_parents']}==owned_parents:
            assert {(edge['child_pid'],edge['parent_pid']) for edge in row['observed_edges']}=={
                (201,101),(102,201),(202,102),(103,202),(203,103)}
            continue
        assert row['scoped_parents']==[
            dict(parent_pid=LAUNCHER,parent_kind='launcher'),
            dict(parent_pid=INTERPRETER,parent_kind='interpreter')]
        assert row['observation_started_monotonic']<=row['observation_monotonic']<=row['monotonic']
        assert row['observation_started_utc'] and row['observation_utc']
        assert row['observed_edges']==[dict(parent_pid=LAUNCHER,child_pid=INTERPRETER,
            parent_kind='launcher',observation_utc=row['observation_utc'],
            observation_monotonic=row['observation_monotonic'],
            child_creation_time_100ns=INTERPRETER_BIRTH,
            child_creation_source='previously_verified_retained_identity')]
        assert '77777' not in json.dumps(row)
        assert 'unrelated-system-name' not in json.dumps(row)


@pytest.mark.parametrize('extras',[
    {(99001,INTERPRETER)},
    {(99002,LAUNCHER)},
    {(99001,INTERPRETER),(99002,LAUNCHER),(99003,INTERPRETER)},
])
def test_edge_diagnostic_extras_are_recorded_before_unchanged_failure(tmp_path,monkeypatch,extras):
    original=SplitApi.children_of
    monkeypatch.setattr(SplitApi,'children_of',lambda self,parents,timeout_seconds=None:
        original(self,parents,timeout_seconds)|extras)
    result,calls=run_split(tmp_path,monkeypatch)
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'
    assert result['ownership_self_test_passed'] is False
    assert result['suspended_assignment_order_verified'] is False
    assert result['owned_identities']==[]
    assert 'owned_root_launched_once' not in calls
    assert result['unrelated_survived'] is False
    assert result['unrelated_cleanup_verified'] is False
    rows,observations=edge_diagnostic_rows(tmp_path)
    assert {(r['child_pid'],r['parent_pid']) for r in observations[0]['observed_edges']}==extras|{(INTERPRETER,LAUNCHER)}
    assert rows.index(observations[0])<next(i for i,r in enumerate(rows) if r['event']=='private_job_termination_requested')
    for edge in observations[0]['observed_edges']:
        assert edge['parent_kind']==('launcher' if edge['parent_pid']==LAUNCHER else 'interpreter')
        if (edge['child_pid'],edge['parent_pid']) in extras:
            assert edge['child_creation_time_100ns'] is None
            assert edge['child_creation_source']=='no_retained_verified_handle'
            assert not any(call[:2]==('open_process',edge['child_pid']) for call in calls if isinstance(call,tuple))


@pytest.mark.parametrize('malformed',[
    None, [], {(0,LAUNCHER)}, {(True,LAUNCHER)}, {(99001,88888)},
    {(99001,LAUNCHER,123)}, {('unrelated-process-name',LAUNCHER)},
])
def test_edge_diagnostic_malformed_observation_is_sanitized_and_fails_closed(tmp_path,monkeypatch,malformed):
    monkeypatch.setattr(SplitApi,'children_of',lambda *args,**kwargs:malformed)
    result,calls=run_split(tmp_path,monkeypatch)
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'
    assert 'owned_root_launched_once' not in calls
    _,observations=edge_diagnostic_rows(tmp_path)
    assert observations[0]['status']=='malformed'
    assert observations[0]['observed_edges'] is None
    assert '88888' not in json.dumps(observations)
    assert 'unrelated-process-name' not in json.dumps(observations)


def test_edge_diagnostic_failed_toolhelp_observation_is_unknown_never_empty_success(tmp_path,monkeypatch):
    def failed(*args,**kwargs):
        raise RuntimeError('scoped Toolhelp failure')
    monkeypatch.setattr(SplitApi,'children_of',failed)
    result,calls=run_split(tmp_path,monkeypatch)
    assert result['failure_reason']=='RuntimeError: scoped Toolhelp failure'
    assert 'owned_root_launched_once' not in calls
    _,observations=edge_diagnostic_rows(tmp_path)
    assert observations[0]['status']=='failed'
    assert observations[0]['error_type']=='RuntimeError'
    assert observations[0]['observed_edges'] is None


def test_edge_diagnostic_journal_write_failure_cannot_reach_owned_launch(tmp_path,monkeypatch):
    from scripts.uc001_granite_controller import standins as module
    original=module.Journal.record
    def record(self,event,**values):
        if event=='scoped_child_edges':
            raise OSError('diagnostic journal unavailable')
        return original(self,event,**values)
    monkeypatch.setattr(module.Journal,'record',record)
    result,calls=run_split(tmp_path,monkeypatch)
    assert result['ownership_self_test_passed'] is False
    assert result['failure_reason']=='OSError: diagnostic journal unavailable'
    assert 'owned_root_launched_once' not in calls


SYNTHETIC_UNKNOWN_PID = 38564
SYNTHETIC_UNKNOWN_BIRTH = 134375170217600000


class UnknownIdentityApi(SplitApi):
    def __init__(self,calls,options):
        super().__init__(calls,options)
        if not options.get('expected_only'):
            self.add(SYNTHETIC_UNKNOWN_PID,SYNTHETIC_UNKNOWN_BIRTH,options.get('unknown_parent_pid',LAUNCHER),
                     False,'unknown','unclassified')
        self.unknown_birth_reads=0
    def open_query_process(self,pid):
        assert pid==SYNTHETIC_UNKNOWN_PID
        self.calls.append(('open_query_only',pid))
        if self.options.get('open_error'):
            error=OSError('synthetic native open failure')
            error.winerror=self.options['open_error']
            raise error
        return f'handle-{pid}'
    def creation_time(self,handle):
        if super().process_id(handle)==SYNTHETIC_UNKNOWN_PID:
            self.unknown_birth_reads+=1
            limit=3 if self.options.get('change_at_cleanup') else 2
            if self.options.get('changed_unknown_birth') and self.unknown_birth_reads>=limit:
                return SYNTHETIC_UNKNOWN_BIRTH+1
            return SYNTHETIC_UNKNOWN_BIRTH
        return super().creation_time(handle)
    def process_id(self,handle):
        pid=super().process_id(handle)
        if (pid==SYNTHETIC_UNKNOWN_PID and self.options.get('changed_unknown_pid')
                and self.unknown_birth_reads>=1):
            return SYNTHETIC_UNKNOWN_PID+1
        return pid
    def parent_pid(self,handle):
        if super().process_id(handle)==SYNTHETIC_UNKNOWN_PID and self.options.get('unknown_parent_mismatch'):
            return 99999
        return super().parent_pid(handle)
    def in_job(self,handle,job):
        if super().process_id(handle)==SYNTHETIC_UNKNOWN_PID:
            return self.options.get('unknown_membership',False)
        return super().in_job(handle,job)
    def image_path(self,handle):
        assert super().process_id(handle)==SYNTHETIC_UNKNOWN_PID
        if self.options.get('path_failure'):
            raise OSError('synthetic image query failure')
        return self.options.get('unknown_path',r'C:\Synthetic\unknown.exe')
    def query_exit_code(self,handle):
        assert super().process_id(handle)==SYNTHETIC_UNKNOWN_PID
        self.calls.append(('unknown_exit_query',SYNTHETIC_UNKNOWN_PID))
        return 259
    def terminate_process(self,handle):
        if super().process_id(handle)==SYNTHETIC_UNKNOWN_PID:
            self.calls.append(('unknown_termination_attempt',SYNTHETIC_UNKNOWN_PID))
        assert super().process_id(handle)!=SYNTHETIC_UNKNOWN_PID,'unknown child termination forbidden'
        return super().terminate_process(handle)
    def close_handle(self,handle):
        self.calls.append(('close_query_or_known_handle',super().process_id(handle)))


def run_unknown_identity(tmp_path,monkeypatch,**options):
    monkeypatch.setitem(globals(),'SplitApi',UnknownIdentityApi)
    result,calls=run_split(tmp_path,monkeypatch,**options)
    assert ('unknown_termination_attempt',SYNTHETIC_UNKNOWN_PID) not in calls
    rows=[json.loads(line) for line in (tmp_path/'selftest/controller.jsonl').read_text().splitlines()]
    observations=[row for row in rows if row['event']=='unknown_child_identity']
    return result,calls,rows,observations


def test_identity_diagnostic_expected_interpreter_only_opens_no_unknown_handle(tmp_path,monkeypatch):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,expected_only=True)
    assert result['ownership_self_test_passed'] is True
    assert observations==[]
    assert not any(isinstance(call,tuple) and call[0]=='open_query_only' for call in calls)


@pytest.mark.parametrize('path',[r'C:\Synthetic\unknown.exe',r'C:\Windows\System32\conhost.exe',r'D:\Other\conhost.exe'])
def test_identity_diagnostic_queryable_paths_remain_untrusted_and_rejected(tmp_path,monkeypatch,path):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,unknown_path=path)
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'
    assert result['ownership_self_test_passed'] is False
    assert 'owned_root_launched_once' not in calls
    assert observations
    first=observations[0]
    assert first['status']=='identity_bound_unknown'
    assert first['observed_child_pid']==SYNTHETIC_UNKNOWN_PID
    assert first['observed_parent_pid']==LAUNCHER
    assert first['native_pid']==SYNTHETIC_UNKNOWN_PID
    assert first['creation_time_100ns']==SYNTHETIC_UNKNOWN_BIRTH
    assert first['native_parent_pid']==LAUNCHER
    assert first['in_private_job'] is False
    assert first['image_path']==path
    assert first['image_path_status']=='observed'
    assert first['raw_exit_code']==259
    assert first['exit_state']=='active_or_exit_code_259'
    assert first['identity_bound'] is True
    assert first['role_accepted'] is False
    assert first['snapshot_to_handle_identity']=='not_established'
    assert calls.count(('open_query_only',SYNTHETIC_UNKNOWN_PID))==1
    assert calls.count(('close_query_or_known_handle',SYNTHETIC_UNKNOWN_PID))==1
    edge_index=next(i for i,row in enumerate(rows) if row['event']=='scoped_child_edges')
    assert edge_index<rows.index(first)<next(i for i,row in enumerate(rows) if row['event']=='private_job_termination_requested')
    rechecks=[row for row in observations if row['phase']=='before_private_job_cleanup']
    assert rechecks and rechecks[0]['identity_bound'] is True
    assert not any(isinstance(call,tuple) and call[:2]==('terminate_identity',SYNTHETIC_UNKNOWN_PID) for call in calls)


@pytest.mark.parametrize('error,status',[(87,'not_found_or_invalid_pid_before_binding'),(5,'process_open_failed')])
def test_identity_diagnostic_disappeared_or_unqueryable_process_remains_unknown(tmp_path,monkeypatch,error,status):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,open_error=error)
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'
    assert observations[0]['status']==status
    assert observations[0]['open_error_winerror']==error
    assert observations[0]['identity_bound'] is False
    assert observations[0]['image_path'] is None
    assert observations[0]['role_accepted'] is False
    assert calls.count(('open_query_only',SYNTHETIC_UNKNOWN_PID))==1
    assert not any(isinstance(call,tuple) and call[0]=='close_query_or_known_handle'
                   and call[1]==SYNTHETIC_UNKNOWN_PID for call in calls)


@pytest.mark.parametrize('option',['changed_unknown_pid','changed_unknown_birth'])
def test_identity_diagnostic_changed_identity_is_never_bound(tmp_path,monkeypatch,option):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,**{option:True})
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'
    assert observations[0]['status']=='identity_changed'
    assert observations[0]['identity_bound'] is False
    assert calls.count(('close_query_or_known_handle',SYNTHETIC_UNKNOWN_PID))==1


@pytest.mark.parametrize('options,status',[
    ({'unknown_parent_mismatch':True},'parent_mismatch'),
    ({'unknown_membership':True},'job_membership_mismatch'),
    ({'unknown_membership':None},'job_membership_unknown'),
    ({'path_failure':True},'path_query_failed'),
])
def test_identity_diagnostic_native_query_gaps_cannot_accept_unknown(tmp_path,monkeypatch,options,status):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,**options)
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'
    assert observations[0]['status']==status
    assert observations[0]['role_accepted'] is False
    assert 'owned_root_launched_once' not in calls


def test_identity_diagnostic_revalidates_retained_handle_before_cleanup(tmp_path,monkeypatch):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,
        changed_unknown_birth=True,change_at_cleanup=True)
    assert observations[0]['identity_bound'] is True
    recheck=next(row for row in observations if row['phase']=='before_private_job_cleanup')
    assert recheck['status']=='identity_changed'
    assert recheck['identity_bound'] is False
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'


def test_identity_diagnostic_journal_failure_still_closes_unknown_without_termination(tmp_path,monkeypatch):
    from scripts.uc001_granite_controller import standins as module
    original=module.Journal.record
    def record(self,event,**values):
        if event=='unknown_child_identity':
            raise OSError('unknown identity journal unavailable')
        return original(self,event,**values)
    monkeypatch.setattr(module.Journal,'record',record)
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch)
    assert result['ownership_self_test_passed'] is False
    assert 'owned_root_launched_once' not in calls
    assert calls.count(('close_query_or_known_handle',SYNTHETIC_UNKNOWN_PID))==1


def test_identity_diagnostic_child_of_verified_interpreter_stays_untrusted(tmp_path,monkeypatch):
    result,calls,rows,observations=run_unknown_identity(tmp_path,monkeypatch,unknown_parent_pid=INTERPRETER)
    assert observations[0]['status']=='identity_bound_unknown'
    assert observations[0]['parent_kind']=='interpreter'
    assert observations[0]['native_parent_pid']==INTERPRETER
    assert result['failure_reason']=='StandinFailure: unknown additional unrelated process'


CONSOLE_PID = 50704
CONSOLE_BIRTH = LAUNCHER_BIRTH + 1
OWNED_CONSOLES = {'root':301,'child':302,'grandchild':303}


class ConsoleApi(SplitApi):
    def __init__(self,calls,options):
        super().__init__(calls,options)
        self.console_reads={}
        if not options.get('no_outside_console'):
            self.add(CONSOLE_PID,CONSOLE_BIRTH,LAUNCHER,False,'console','unrelated')
        if options.get('two_consoles') or options.get('third_child'):
            self.add(50705,CONSOLE_BIRTH+1,LAUNCHER,False,
                     'unknown' if options.get('third_child') else 'console','unrelated')
        if options.get('second_interpreter'):
            self.add(50706,CONSOLE_BIRTH+2,LAUNCHER,False,'unknown','unrelated')
        if options.get('console_under_interpreter'):
            self.processes[CONSOLE_PID]['parent_pid']=INTERPRETER
        if options.get('console_predates_launcher'):
            self.processes[CONSOLE_PID]['creation_time_100ns']=LAUNCHER_BIRTH-1
    def system_console_path(self):
        if self.options.get('system_directory_failure'):
            raise OSError('native system directory unavailable')
        return self.options.get('system_console',r'R:\NativeWindows\System32\conhost.exe')
    def open_query_process(self,pid):
        self.calls.append(('query_only',pid))
        if self.options.get('console_unqueryable'):
            raise OSError('query denied')
        return f'handle-{pid}'
    def process_id(self,handle):
        pid=super().process_id(handle)
        if pid==CONSOLE_PID and self.options.get('console_pid_changed') and self.console_reads.get(pid,0):
            return pid+1000
        return pid
    def creation_time(self,handle):
        pid=super().process_id(handle)
        if self.processes[pid]['kind']=='console':
            self.console_reads[pid]=self.console_reads.get(pid,0)+1
            value=self.processes[pid]['creation_time_100ns']
            changed=self.options.get('console_birth_changed') and self.console_reads[pid]>=2
            return value+1 if changed else value
        return super().creation_time(handle)
    def parent_pid(self,handle):
        pid=super().process_id(handle)
        if self.processes[pid]['kind']=='console' and self.options.get('console_parent_mismatch'):
            return 99999
        return self.processes[pid]['parent_pid']
    def in_job(self,handle,job):
        pid=super().process_id(handle)
        if self.processes[pid]['kind']=='console':
            if pid in OWNED_CONSOLES.values() and self.options.get('owned_membership_mismatch'):return False
            if pid in OWNED_CONSOLES.values() and self.options.get('owned_membership_unknown'):return None
            if self.options.get('console_membership_unknown'):return None
            if self.options.get('console_membership_mismatch'):return not self.processes[pid]['member']
        return self.processes[pid]['member']
    def image_path(self,handle):
        pid=super().process_id(handle)
        if self.options.get('console_path_failure'):
            raise OSError('image path unavailable')
        if self.processes[pid]['kind']!='console':return r'D:\Untrusted\python.exe'
        if self.options.get('path_changed_at_cleanup') and self.options['job_ref'][0].killed:
            return r'D:\Untrusted\conhost.exe'
        return self.options.get('console_path',self.system_console_path())
    def query_exit_code(self,handle):
        pid=super().process_id(handle)
        row=self.processes[pid]
        if self.options.get('console_exit_query_failure'):
            raise OSError('exit query unavailable')
        if (row['kind']=='console' and not row['member'] and not self.options.get('console_stuck')
                and not self.processes[LAUNCHER]['alive'] and not self.processes[INTERPRETER]['alive']):
            row['alive']=False
        return 259 if row['alive'] else 0
    def exit_code(self,handle):
        pid=super().process_id(handle)
        if self.processes[pid]['kind']=='console':
            return None if self.processes[pid]['alive'] else 0
        return super().exit_code(handle)
    def children_of(self,parents,timeout_seconds=None):
        result=super().children_of(parents,timeout_seconds)
        if self.options.get('missing_interpreter_edge'):
            result.discard((INTERPRETER,LAUNCHER))
        if self.options['job_ref'] and self.options['job_ref'][0].killed:
            if self.options.get('console_vanished'):
                result.discard((CONSOLE_PID,LAUNCHER))
            if self.options.get('console_replacement'):
                result.discard((CONSOLE_PID,LAUNCHER))
                self.add(50707,CONSOLE_BIRTH+3,LAUNCHER,False,'console','unrelated')
                result.add((50707,LAUNCHER))
        return result
    def terminate_process(self,handle):
        pid=super().process_id(handle)
        if self.processes[pid]['kind'] in {'console','unknown'}:
            self.calls.append(('unclassified_or_helper_termination',pid))
            raise AssertionError('console/unknown direct termination forbidden')
        return super().terminate_process(handle)
    def close_handle(self,handle):
        self.calls.append(('close_retained',super().process_id(handle)))
        if self.processes[super().process_id(handle)]['kind']=='console' and self.options.get('helper_close_failure'):
            raise OSError('retained helper close failed')


class ConsoleJob(SplitJob):
    def __init__(self,api,calls,options):
        super().__init__(api,calls,options)
        if options.get('owned_consoles'):
            for role,pid in OWNED_CONSOLES.items():
                launcher=SPLIT_OWNED[role][0]
                self.members.append((pid,launcher[1]+1))
                api.add(pid,launcher[1]+1,launcher[0],True,'console',role,alive=False)
                if role=='root' and options.get('owned_helper_under_interpreter'):
                    api.processes[pid]['parent_pid']=SPLIT_OWNED['root'][1][0]
        if options.get('owned_unknown_third'):
            self.members.append((399,134374354509999999))
            api.add(399,134374354509999999,101,True,'unknown','root',alive=False)
    def cleanup(self,timeout_seconds=5):
        value=super().cleanup(timeout_seconds)
        for row in value['owned_exits']:
            if row['pid'] in OWNED_CONSOLES.values():
                row['exit_code']=None if self.options.get('owned_helper_exit_missing') else 0
        return value


def run_console(tmp_path,monkeypatch,**options):
    monkeypatch.setitem(globals(),'SplitApi',ConsoleApi)
    monkeypatch.setitem(globals(),'SplitJob',ConsoleJob)
    result,calls=run_split(tmp_path,monkeypatch,**options)
    assert not any(isinstance(row,tuple) and row[0]=='unclassified_or_helper_termination' for row in calls)
    rows=[json.loads(line) for line in (tmp_path/'selftest/controller.jsonl').read_text().splitlines()]
    return result,calls,rows


def test_console_role_optional_absence_preserves_six_base_identities(tmp_path,monkeypatch):
    result,calls,rows=run_console(tmp_path,monkeypatch,no_outside_console=True)
    assert result['ownership_self_test_passed'] is True
    assert result['console_helpers']==[]
    assert result['console_helper_cleanup_verified'] is True
    assert result['cleanup']['total_processes']==6


def test_console_role_one_system_sibling_is_retained_and_exit_verified(tmp_path,monkeypatch):
    result,calls,rows=run_console(tmp_path,monkeypatch)
    assert result['ownership_self_test_passed'] is True
    assert result['console_helper_cleanup_verified'] is True
    assert len(result['console_helpers'])==1
    helper=result['console_helpers'][0]
    assert (helper['pid'],helper['creation_time_100ns'],helper['parent_pid'])==(CONSOLE_PID,CONSOLE_BIRTH,LAUNCHER)
    assert helper['kind']=='console_helper'
    assert result['console_helper_exits'][0]['identity_verified'] is True
    assert result['console_helper_exits'][0]['exit_code']==0
    assert result['console_helper_exits'][0]['exit_proof']=='retained_query_non259'
    assert result['console_helper_exits'][0]['direct_termination_requested'] is False
    assert calls.count(('query_only',CONSOLE_PID))==1
    assert calls.count(('close_retained',CONSOLE_PID))==1
    assert any(row['event']=='console_helper_revalidated' for row in rows)


def test_console_role_owned_helpers_use_exact_job_accounting_and_nested_base_edges(tmp_path,monkeypatch):
    result,calls,rows=run_console(tmp_path,monkeypatch,owned_consoles=True)
    assert result['ownership_self_test_passed'] is True
    assert len(result['owned_identities'])==6
    assert {row['pid'] for row in result['console_helpers']}=={CONSOLE_PID,*OWNED_CONSOLES.values()}
    assert result['cleanup']['total_processes']==9
    assert result['cleanup']['active_processes']==0
    assert {row['pid'] for row in result['cleanup']['owned_exits']}=={101,201,102,202,103,203,*OWNED_CONSOLES.values()}
    assert len(result['console_helper_exits'])==4
    assert all(row['identity_verified'] and type(row['exit_code']) is int for row in result['console_helper_exits'])
    assert all(row['exit_proof']=='private_job_wait_and_query' for row in result['console_helper_exits'] if row['role']!='unrelated')
    assert all(row['private_job_cleanup_scope'] is (row['role']!='unrelated') for row in result['console_helper_exits'])
    assert all('private_job_termination_applied' not in row for row in result['console_helper_exits'])
    assert all(helper['parent_pid'] in {LAUNCHER,101,102,103} for helper in result['console_helpers'])


@pytest.mark.parametrize('options',[
    {'missing_interpreter_edge':True},{'second_interpreter':True},{'two_consoles':True},
    {'console_under_interpreter':True},{'console_path':r'D:\Fake\conhost.exe'},
    {'console_path':r'R:\NativeWindows\System32\notepad.exe'},
    {'console_birth_changed':True},{'console_pid_changed':True},{'console_parent_mismatch':True},
    {'console_membership_mismatch':True},{'console_membership_unknown':True},
    {'console_path_failure':True},{'console_unqueryable':True},{'third_child':True},
    {'console_predates_launcher':True},{'system_directory_failure':True},{'console_exit_query_failure':True},
])
def test_console_role_incomplete_or_additional_outside_shape_fails_without_promotion(tmp_path,monkeypatch,options):
    result,calls,rows=run_console(tmp_path,monkeypatch,**options)
    assert result['ownership_self_test_passed'] is False
    assert result['console_helpers']==[]
    assert 'owned_root_launched_once' not in calls


@pytest.mark.parametrize('options',[
    {'console_stuck':True},{'console_vanished':True},{'console_replacement':True},
    {'path_changed_at_cleanup':True},
])
def test_console_role_accepted_identity_cannot_be_replaced_or_ignored_during_cleanup(tmp_path,monkeypatch,options):
    result,calls,rows=run_console(tmp_path,monkeypatch,**options)
    assert len(result['console_helpers'])==1
    assert result['ownership_self_test_passed'] is False
    assert result['console_helper_cleanup_verified'] is False or result['failure_reason'] is not None


@pytest.mark.parametrize('options',[
    {'owned_helper_exit_missing':True},{'owned_unknown_third':True},{'late_unknown_cleanup':True},
])
def test_console_role_owned_cleanup_needs_all_helper_exits_and_exact_lifetime_count(tmp_path,monkeypatch,options):
    result,calls,rows=run_console(tmp_path,monkeypatch,owned_consoles=True,**options)
    assert result['ownership_self_test_passed'] is False
    assert result['cleanup']['verified'] is False or result['console_helper_cleanup_verified'] is False


def test_console_role_full_native_system_path_uses_windows_case_semantics(tmp_path,monkeypatch):
    result,calls,rows=run_console(tmp_path,monkeypatch,
        system_console=r'S:\ActualWindows\system32\conhost.exe',
        console_path=r's:\actualwindows\System32\CONHOST.EXE')
    assert result['ownership_self_test_passed'] is True


@pytest.mark.parametrize('option',['owned_membership_mismatch','owned_membership_unknown','owned_helper_under_interpreter'])
def test_console_role_owned_membership_and_launcher_parent_are_required(tmp_path,monkeypatch,option):
    result,calls,rows=run_console(tmp_path,monkeypatch,owned_consoles=True,**{option:True})
    assert result['ownership_self_test_passed'] is False
    assert {row['role'] for row in result['console_helpers']}=={'unrelated'}


def test_console_role_handle_close_failure_is_not_verified_cleanup(tmp_path,monkeypatch):
    result,calls,rows=run_console(tmp_path,monkeypatch,helper_close_failure=True)
    assert result['ownership_self_test_passed'] is False
    assert result['console_helper_cleanup_verified'] is False
