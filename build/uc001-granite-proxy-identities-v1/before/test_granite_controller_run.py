import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.uc001_granite_acquisition_proxy.proxy import BudgetLedger, CEILING
from scripts.uc001_granite_controller.controller import ControllerFailure, run_session


@dataclass
class Process:
    pid: int
    creation_time_100ns: int


class Clock:
    def __init__(self):
        self.now = 100.0
    def __call__(self):
        return self.now
    def sleep(self, amount):
        self.now += amount


class Backend:
    def __init__(self, failure=None, cleanup=True):
        self.failure = failure
        self.clean = cleanup
        self.launched = []
        self.terminated = 0
        self.closed = False
        self.polls = 0
        self.current = None
    def launch(self, *args, **kwargs):
        if self.failure == 'interrupt':
            raise KeyboardInterrupt()
        self.current = Process(100 + len(self.launched), 10000 + len(self.launched))
        self.launched.append(self.current)
        self.polls = 0
        return self.current
    def validate_pid(self, pid, creation_time_100ns=None):
        return Process(pid, creation_time_100ns or 10000)
    def process_exit(self, proc):
        if proc.pid == 200:
            return 0 if self.failure == 'proxy_exit' else None
        self.polls += 1
        return (1 if self.failure == 'worker' else 0) if self.polls >= 2 else None
    def snapshot(self):
        return dict(active_processes=0 if self.polls >= 2 else 1,
                    job_committed_bytes=1024, memory_metric='job_private_commit_bytes', owned=[])
    def terminate(self):
        self.terminated += 1
        self.polls = 2
    def cleanup(self, **kwargs):
        return dict(verified=self.clean, active_processes=0 if self.clean else 1,
                    owned_exits=[], errors=[] if self.clean else ['synthetic descendants remain'])
    def close(self):
        self.closed = True


class Sampler:
    def __init__(self, clock, change=None):
        self.clock, self.change = clock, change
        self.closed = False
    def start(self):
        pass
    def latest(self):
        value = dict(sampled_mono=self.clock(), disk_free_bytes=51539607552,
                     host_free_bytes=32*1024**3, job_committed_bytes=1024,
                     build_output_bytes=0, active_processes=1, owned=[])
        if self.change:
            value.update(self.change)
        return value
    def close(self):
        self.closed = True


class Events:
    def __init__(self, rows):
        self.rows = rows
    def read(self, terminal=False):
        rows, self.rows = self.rows, []
        return rows


def plans(tmp_path, proxy_exit=False, ledger_bad=False, manifest_bad=False):
    import hashlib
    manifest=tmp_path/"built-artifacts.json"
    manifest.write_text(json.dumps([dict(path=str(tmp_path/"bin/llama-server.exe"),bytes=1,sha256="0"*64)]))
    ledger = tmp_path/'proxy.jsonl'
    writer = BudgetLedger(ledger, CEILING, 7)
    writer.record('listening', address=['127.0.0.1',12345], pid=200)
    writer.record('end', status='closed_unqualified', sockets_closed=True)
    writer.close()
    if ledger_bad:
        ledger.write_text('{"event":')
    rows = [dict(event='phase_start', phase='acquisition'),
            dict(event='child_started', label='proxy', pid=200, creation_time_100ns=20000, in_any_job=True),
            dict(event='proxy_started', pid=200, creation_time_100ns=20000, ledger=str(ledger))]
    if not proxy_exit:
        rows += [dict(event='proxy_closing',pid=200,creation_time_100ns=20000),
                 dict(event='child_exit',label='proxy',pid=200,creation_time_100ns=20000,in_any_job=True,exit_code=0),
                 dict(event='acquisition_terminal',ledger_path=str(ledger),ledger_sha256=__import__('hashlib').sha256(ledger.read_bytes()).hexdigest(),cumulative_bytes=7,prior_bytes=7,proxy_pid=200),
                 dict(event='phase_complete',phase='acquisition')]
    return [dict(name='acquisition',argv=['synthetic-acquisition'],cwd=str(tmp_path),env={},
                 stdoutfile=tmp_path/'acq.out',stderrfile=tmp_path/'acq.err',events_reader=Events(rows),
                 expected_prior_bytes=7,ledgerpath=ledger),
            dict(name='build',argv=['synthetic-build'],cwd=str(tmp_path),env={},
                 stdoutfile=tmp_path/'build.out',stderrfile=tmp_path/'build.err',artifact_manifest=manifest,events_reader=Events([
                     dict(event='phase_start',phase='build'),dict(event='build_terminal',artifact_manifest_path=str(manifest),artifact_manifest_sha256='0'*64 if manifest_bad else hashlib.sha256(manifest.read_bytes()).hexdigest(),artifact_count=1),
                     dict(event='phase_complete',phase='build')]))]


class Watchdog:
    def __init__(self, *args, **kwargs):
        self.failure = None
    def start(self):
        pass
    def beat(self, *args):
        pass
    def close(self):
        pass


def execute(tmp_path, backend, sampler_change=None, **changes):
    clock=Clock(); sampler=Sampler(clock,sampler_change)
    return run_session(backend,sampler,plans(tmp_path, **changes),clock=clock,
                       sleep=clock.sleep,watchdog_factory=Watchdog)


def test_complete_two_phase_session_has_one_acquisition_and_one_build_worker(tmp_path):
    backend=Backend()
    result=execute(tmp_path,backend)
    assert result['status']=='controlled_phases_passed'
    assert result['cleanup']['verified'] is True
    assert len(backend.launched)==2 and backend.closed
    assert result['downloaded_upper_bound_bytes']==7


@pytest.mark.parametrize('failure', ['worker','proxy_exit','interrupt'])
def test_failure_or_interruption_terminates_owned_tree_without_retry(tmp_path,failure):
    backend=Backend(failure)
    result=execute(tmp_path,backend,proxy_exit=failure=='proxy_exit')
    assert result['status']=='failure'
    assert backend.terminated>=1 and backend.closed
    assert len(backend.launched)<=1
    assert result['cleanup']['verified'] is True


def test_malformed_proxy_ledger_prevents_next_phase(tmp_path):
    backend=Backend()
    result=execute(tmp_path,backend,ledger_bad=True)
    assert result['status']=='failure' and len(backend.launched)==1
    assert backend.terminated>=1


def test_stale_observation_prevents_even_first_resume(tmp_path):
    backend=Backend()
    result=execute(tmp_path,backend,{'sampled_mono':98.0})
    assert result['status']=='failure' and not backend.launched


def test_failed_measurement_prevents_work_instead_of_substituting_zero(tmp_path):
    backend=Backend()
    result=execute(tmp_path,backend,{'error':'synthetic unavailable measurement'})
    assert result['status']=='failure' and not backend.launched


def test_initial_disk_rejection_prevents_work(tmp_path):
    backend=Backend()
    result=execute(tmp_path,backend,{'disk_free_bytes':51539607551})
    assert result['status']=='failure' and not backend.launched


def test_cleanup_failure_cannot_be_reported_as_success(tmp_path):
    backend=Backend(cleanup=False)
    result=execute(tmp_path,backend)
    assert result['status']=='failure'
    assert result['cleanup']['verified'] is False


def test_controller_stops_when_owned_descendants_survive_worker_exit(tmp_path):
    class ActiveDescendants(Backend):
        def snapshot(self):
            return dict(active_processes=2,job_committed_bytes=1024,owned=[])
    backend=ActiveDescendants()
    result=execute(tmp_path,backend)
    assert result['status']=='failure' and backend.terminated>=1
    assert len(backend.launched)==1


def test_output_measurement_rejects_broken_symlink_instead_of_zero(tmp_path):
    from scripts.uc001_granite_controller.controller import build_output_bytes
    output = tmp_path/'build'
    output.symlink_to(tmp_path/'missing-target',target_is_directory=True)
    with pytest.raises(ControllerFailure):
        build_output_bytes(output)


def test_output_measurement_sums_nested_files_and_rejects_escape(tmp_path):
    from scripts.uc001_granite_controller.controller import build_output_bytes
    (tmp_path/'build/sub').mkdir(parents=True)
    (tmp_path/'build/one').write_bytes(b'ab')
    (tmp_path/'build/sub/two').write_bytes(b'cde')
    assert build_output_bytes(tmp_path/'build')==5
    (tmp_path/'build/sub/link').symlink_to(tmp_path/'build/one')
    with pytest.raises(ControllerFailure):
        build_output_bytes(tmp_path/'build')


def test_partial_worker_events_are_pending_only_until_worker_exit(tmp_path):
    from scripts.uc001_granite_controller.controller import FileEvents
    path=tmp_path/'worker.jsonl';path.write_text('{"event":"phase_start"')
    reader=FileEvents(path)
    assert reader.read()==[]
    with pytest.raises(ControllerFailure):
        reader.read(terminal=True)


def test_malformed_complete_worker_event_is_fatal(tmp_path):
    from scripts.uc001_granite_controller.controller import FileEvents
    path=tmp_path/'worker.jsonl';path.write_text('{bad}\n')
    with pytest.raises(ControllerFailure):
        FileEvents(path).read()


def test_independent_watchdog_stops_owned_job_when_control_loop_stalls(monkeypatch):
    import time
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import controller as module
    monkeypatch.setattr(module,'OBSERVATION_AGE',0.03)
    backend=Backend()
    guard=module.Watchdog(backend)
    guard.beat('acquisition',SimpleNamespace(started_mono=time.monotonic(),build_started_mono=None))
    guard.start()
    try:
        time.sleep(0.12)
        assert guard.failure and backend.terminated==1
    finally:
        guard.close()


def test_slow_sampler_is_unknown_and_does_not_block_the_controller(tmp_path):
    import threading
    from scripts.uc001_granite_controller.controller import ResourceSampler
    blocked=threading.Event()
    class SlowBackend(Backend):
        def snapshot(self):
            blocked.wait(2)
            return super().snapshot()
        def host_resources(self,path):
            return dict(disk_free_bytes=51539607552,host_free_bytes=32*1024**3)
    sampler=ResourceSampler(SlowBackend(),tmp_path)
    sampler.start()
    try:
        assert sampler.latest() is None
        with pytest.raises(ControllerFailure):
            sampler.close()
    finally:
        blocked.set()
        sampler.thread.join(2)


@pytest.mark.parametrize('change',[{'job_committed_bytes':25769803777},
                                  {'build_output_bytes':12884901889},
                                  {'disk_free_bytes':8589934591},
                                  {'host_free_bytes':4294967295}])
def test_resource_breach_during_work_terminates_owned_job(tmp_path,change):
    clock=Clock();backend=Backend()
    class BreachSampler(Sampler):
        def latest(self):
            value=super().latest()
            if backend.launched:
                value.update(change)
            return value
    result=run_session(backend,BreachSampler(clock),plans(tmp_path),clock=clock,
                       sleep=clock.sleep,watchdog_factory=Watchdog)
    assert result['status']=='failure' and backend.terminated>=1
    assert len(backend.launched)==1


def test_build_terminal_manifest_hash_is_independently_checked(tmp_path):
    backend=Backend()
    result=execute(tmp_path,backend,manifest_bad=True)
    assert result['status']=='failure' and backend.terminated>=1
