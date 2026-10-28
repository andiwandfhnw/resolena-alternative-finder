import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.uc001_granite_acquisition_proxy.proxy import BudgetLedger, CEILING
from scripts.uc001_granite_controller.controller import ControllerFailure, run_session


class BindingApi:
    def __init__(self, backend):
        self.backend = backend
        self.reads = {}
        self.closed = []
    def process_id(self, handle):
        pid = int(handle.split(':')[1])
        return pid + 10 if self.backend.damage == 'handle_pid' and pid == 201 else pid
    def creation_time(self, handle):
        pid = int(handle.split(':')[1])
        self.reads[pid] = self.reads.get(pid, 0) + 1
        value = self.backend.facts[pid]['birth']
        return value + 1 if self.backend.damage == 'birth_change' and pid == 201 and self.reads[pid] > 1 else value
    def parent_pid(self, handle):
        return self.backend.facts[int(handle.split(':')[1])]['parent']
    def in_job(self, handle, job):
        assert job == 'private-job'
        return self.backend.facts[int(handle.split(':')[1])]['member']
    def children_of(self, parents, timeout_seconds=1):
        return {(pid, fact['parent']) for pid,fact in self.backend.facts.items()
                if fact['parent'] in parents and fact['exit'] is None}
    def open_query_process(self, pid):
        assert pid in self.backend.facts
        return 'query:' + str(pid)
    def image_path(self, handle):
        return self.backend.facts[int(handle.split(':')[1])].get('image', r'D:\Unknown\extra.exe')
    def query_exit_code(self, handle):
        code = self.backend.facts[int(handle.split(':')[1])]['exit']
        return 259 if code is None else code
    def system_console_path(self):
        return r'R:\Windows\System32\conhost.exe'
    def close_handle(self, handle):
        self.closed.append(handle)


class BindingBackend:
    def __init__(self, split=True, damage=None, extra=False, helper=False):
        from types import SimpleNamespace
        self.handle, self.damage = 'private-job', damage
        self.facts = {200:dict(birth=20000,parent=100,member=True,exit=None)}
        if split:
            self.facts[201] = dict(birth=20001,parent=200,member=True,exit=None)
        if extra or helper:
            self.facts[202] = dict(birth=20002,parent=200,member=True,exit=None,
                                  image=r'R:\Windows\System32\conhost.exe' if helper else r'D:\Unknown\extra.exe')
        if damage == 'parent':self.facts[201]['parent'] = 999
        if damage == 'membership':self.facts[201]['member'] = False
        self.api = BindingApi(self)
        self.retained = {pid:SimpleNamespace(pid=pid,creation_time_100ns=fact['birth'],handle='process:'+str(pid))
                         for pid,fact in self.facts.items()}
    def validate_pid(self, pid, creation_time_100ns=None):
        value = self.retained[pid]
        if (creation_time_100ns is not None and value.creation_time_100ns != creation_time_100ns
                or self.facts[pid]['member'] is not True):
            raise ControllerFailure('synthetic exact Job identity mismatch')
        return value
    def process_exit(self, process):
        return self.facts[process.pid]['exit']


def proxy_identity(pid, birth, parent):
    return dict(pid=pid,creation_time_100ns=birth,parent_pid=parent,in_any_job=True)


def proxy_binding_monitor(tmp_path, *, split=True, damage=None, extra=False, helper=False, ledger_pid=None):
    import hashlib
    from scripts.uc001_granite_controller.controller import PhaseMonitor
    backend = BindingBackend(split, damage, extra, helper)
    launcher = proxy_identity(200,20000,100)
    interpreter = proxy_identity(201,20001,200) if split else dict(launcher)
    ledger = tmp_path/'binding-ledger.jsonl'
    writer = BudgetLedger(ledger, CEILING, 7)
    writer.record('listening', address=['127.0.0.1',12345], pid=ledger_pid or interpreter['pid'])
    writer.record('end', status='closed_unqualified', sockets_closed=True)
    writer.close()
    plan = dict(name='acquisition',ledgerpath=ledger,expected_prior_bytes=7)
    ack, journal = [], []
    monitor = PhaseMonitor(plan,backend,lambda event,**values:journal.append(dict(event=event,**values)),
                           acknowledge=ack.append)
    request = dict(event='proxy_binding_requested',schema=1,launcher=launcher,interpreter=interpreter,
                   same_process=not split,ready_pid=interpreter['pid'])
    start = [dict(event='phase_start',phase='acquisition'),
             dict(event='proxy_launcher_started',schema=1,launcher=launcher)]
    terminal = dict(event='acquisition_terminal',ledger_path=str(ledger),ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
                    cumulative_bytes=7,prior_bytes=7,proxy_launcher_pid=launcher['pid'],
                    proxy_interpreter_pid=interpreter['pid'],proxy_identity_schema=1)
    return monitor,backend,ack,journal,start,request,terminal


def complete_proxy_binding(monitor,backend,request,terminal,omit=None):
    pair = dict(schema=1,launcher=request['launcher'],interpreter=request['interpreter'],
                listening_pid=request['interpreter']['pid'])
    monitor.accept([dict(event='proxy_listening',**pair),dict(event='proxy_closing',**pair)])
    for fact in backend.facts.values():fact['exit'] = 0
    exits = [dict(event='proxy_interpreter_exit',schema=1,identity=request['interpreter'],exit_code=0,identity_verified=True),
             dict(event='proxy_launcher_exit',schema=1,identity=request['launcher'],exit_code=0,identity_verified=True)]
    monitor.accept([row for row in exits if row['event'] != omit]+[terminal,dict(event='phase_complete',phase='acquisition')])


@pytest.mark.parametrize('split',[True,False])
def test_proxy_binding_distinct_roles_use_verified_interpreter_ledger_and_both_exits(tmp_path,split):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,split=split)
    monitor.accept(start+[request])
    assert ack==[b'PROXY_BOUND\n']
    assert monitor.proxy.pid==request['interpreter']['pid']
    complete_proxy_binding(monitor,backend,request,terminal)
    assert monitor.finish()==7
    cleanup=dict(verified=True,active_processes=0,owned_exits=[dict(pid=pid,creation_time_100ns=fact['birth'],exit_code=0)
        for pid,fact in backend.facts.items()])
    receipt=monitor.cleanup(cleanup)
    assert receipt['verified'] is True
    assert {row['role'] for row in receipt['identities']}=={'launcher','interpreter'}


@pytest.mark.parametrize('damage',['parent','membership','birth_change','handle_pid'])
def test_proxy_binding_native_identity_gaps_fail_before_private_ack(tmp_path,damage):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,damage=damage)
    with pytest.raises((ControllerFailure,RuntimeError)):
        monitor.accept(start+[request])
    assert ack==[]


def test_proxy_binding_wrong_readiness_pid_is_not_any_owned_pid(tmp_path):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path)
    request['ready_pid']=200
    with pytest.raises(ControllerFailure):monitor.accept(start+[request])
    assert ack==[]


@pytest.mark.parametrize('same_process',[True,False])
def test_proxy_binding_same_process_flag_requires_actual_retained_identity(tmp_path,same_process):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,split=same_process)
    request['same_process']=same_process
    with pytest.raises(ControllerFailure):monitor.accept(start+[request])
    assert ack==[]


def test_proxy_binding_ledger_launcher_pid_is_rejected(tmp_path):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,ledger_pid=200)
    monitor.accept(start+[request]);complete_proxy_binding(monitor,backend,request,terminal)
    with pytest.raises(ControllerFailure):monitor.finish()


@pytest.mark.parametrize('pid',[200,201])
def test_proxy_binding_premature_launcher_or_interpreter_exit_fails(tmp_path,pid):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path)
    monitor.accept(start+[request]);backend.facts[pid]['exit']=0
    with pytest.raises(ControllerFailure):monitor.poll_proxy()


@pytest.mark.parametrize('missing',['proxy_launcher_exit','proxy_interpreter_exit'])
def test_proxy_binding_terminal_requires_both_role_exit_records(tmp_path,missing):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path)
    monitor.accept(start+[request]);complete_proxy_binding(monitor,backend,request,terminal,omit=missing)
    with pytest.raises(ControllerFailure):monitor.finish()


def test_proxy_binding_unclassified_third_process_prevents_ack(tmp_path):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,extra=True)
    with pytest.raises(ControllerFailure):monitor.accept(start+[request])
    assert ack==[]


def test_proxy_binding_reuses_closed_console_policy_and_verifies_helper_cleanup(tmp_path):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,helper=True)
    monitor.accept(start+[request]);assert ack==[b'PROXY_BOUND\n']
    complete_proxy_binding(monitor,backend,request,terminal);assert monitor.finish()==7
    cleanup=dict(verified=True,active_processes=0,owned_exits=[dict(pid=pid,creation_time_100ns=fact['birth'],exit_code=0)
        for pid,fact in backend.facts.items()])
    receipt=monitor.cleanup(cleanup)
    assert receipt['verified'] is True
    assert 'query:202' in backend.api.closed


@pytest.mark.parametrize('schema',[True,1.0])
@pytest.mark.parametrize('stage',['launcher','request','listening','terminal'])
def test_proxy_binding_schema_must_be_exact_integer_version(tmp_path,schema,stage):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path)
    if stage=='launcher':
        start[-1]['schema']=schema
        with pytest.raises(ControllerFailure):monitor.accept(start)
        return
    if stage=='request':
        request['schema']=schema
        with pytest.raises(ControllerFailure):monitor.accept(start+[request])
        return
    monitor.accept(start+[request])
    if stage=='listening':
        row=dict(event='proxy_listening',schema=schema,launcher=request['launcher'],
                 interpreter=request['interpreter'],listening_pid=201)
        with pytest.raises(ControllerFailure):monitor.accept([row])
        return
    terminal['proxy_identity_schema']=schema
    complete_proxy_binding(monitor,backend,request,terminal)
    with pytest.raises(ControllerFailure):monitor.finish()


def test_proxy_binding_missing_accepted_helper_handle_cannot_verify_cleanup(tmp_path):
    monitor,backend,ack,journal,start,request,terminal=proxy_binding_monitor(tmp_path,helper=True)
    monitor.accept(start+[request]);complete_proxy_binding(monitor,backend,request,terminal)
    monitor.proxy_queries[202]['handle']=None
    cleanup=dict(verified=True,active_processes=0,owned_exits=[dict(pid=pid,creation_time_100ns=fact['birth'],exit_code=0)
        for pid,fact in backend.facts.items()])
    assert monitor.cleanup(cleanup)['verified'] is False


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
        self.handle, self.damage = 'private-job', None
        self.facts = {200:dict(birth=20000,parent=100,member=True,exit=None)}
        self.api = BindingApi(self)
        self.acks = []
    def launch(self, *args, **kwargs):
        if self.failure == 'interrupt':
            raise KeyboardInterrupt()
        self.current = Process(100 + len(self.launched), 10000 + len(self.launched))
        self.launched.append(self.current)
        self.polls = 0
        return self.current
    def validate_pid(self, pid, creation_time_100ns=None):
        if pid == 200:
            from types import SimpleNamespace
            if creation_time_100ns != 20000:
                raise ControllerFailure('synthetic proxy birth differs')
            if not hasattr(self,'proxy_process'):
                self.proxy_process=SimpleNamespace(pid=200,creation_time_100ns=20000,handle='process:200')
            return self.proxy_process
        return Process(pid, creation_time_100ns or 10000)
    def process_exit(self, proc):
        if proc.pid == 200:
            return 0 if self.failure == 'proxy_exit' else self.facts[200]['exit']
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
                    owned_exits=[dict(pid=200,creation_time_100ns=20000,exit_code=0)],
                    errors=[] if self.clean else ['synthetic descendants remain'])
    def write_stdin(self, worker, data):
        assert data == b'PROXY_BOUND\n'
        self.acks.append(data)
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


class BindingEvents:
    def __init__(self,batches,backend):
        self.batches,self.backend,self.reads=batches,backend,0
    def read(self,terminal=False):
        if self.reads==1:
            assert self.backend.acks==[b'PROXY_BOUND\n']
            self.backend.facts[200]['exit']=0
        self.reads+=1
        return self.batches.pop(0) if self.batches else []


def plans(tmp_path, proxy_exit=False, ledger_bad=False, manifest_bad=False, backend=None):
    import hashlib
    backend=backend or Backend()
    manifest=tmp_path/"built-artifacts.json"
    manifest.write_text(json.dumps([dict(path=str(tmp_path/"bin/llama-server.exe"),bytes=1,sha256="0"*64)]))
    ledger = tmp_path/'proxy.jsonl'
    writer = BudgetLedger(ledger, CEILING, 7)
    writer.record('listening', address=['127.0.0.1',12345], pid=200)
    writer.record('end', status='closed_unqualified', sockets_closed=True)
    writer.close()
    if ledger_bad:
        ledger.write_text('{"event":')
    identity=proxy_identity(200,20000,100)
    pair=dict(schema=1,launcher=identity,interpreter=identity,listening_pid=200)
    rows = [dict(event='phase_start', phase='acquisition'),
            dict(event='proxy_launcher_started',schema=1,launcher=identity),
            dict(event='proxy_binding_requested',schema=1,launcher=identity,interpreter=identity,
                 same_process=True,ready_pid=200)]
    terminal_rows=[]
    if not proxy_exit:
        terminal_rows = [dict(event='proxy_listening',**pair),dict(event='proxy_closing',**pair),
                 dict(event='proxy_interpreter_exit',schema=1,identity=identity,exit_code=0,identity_verified=True),
                 dict(event='proxy_launcher_exit',schema=1,identity=identity,exit_code=0,identity_verified=True),
                 dict(event='acquisition_terminal',ledger_path=str(ledger),ledger_sha256=__import__('hashlib').sha256(ledger.read_bytes()).hexdigest(),cumulative_bytes=7,prior_bytes=7,proxy_launcher_pid=200,proxy_interpreter_pid=200,proxy_identity_schema=1),
                 dict(event='phase_complete',phase='acquisition')]
    return [dict(name='acquisition',argv=['synthetic-acquisition'],cwd=str(tmp_path),env={},
                 stdoutfile=tmp_path/'acq.out',stderrfile=tmp_path/'acq.err',events_reader=BindingEvents([rows,terminal_rows],backend),stdin_pipe=True,
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
    return run_session(backend,sampler,plans(tmp_path, backend=backend, **changes),clock=clock,
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


class LifecycleBackend(Backend):
    def __init__(self, schedule, damage=None):
        super().__init__()
        from types import SimpleNamespace
        self.schedule, self.damage = schedule, damage
        self.facts[201] = dict(birth=20001, parent=200, member=True, exit=None)
        if schedule == 'helper_lag':
            self.facts[202] = dict(birth=20002, parent=200, member=True, exit=None,
                                   image=r'R:\Windows\System32\conhost.exe')
        self.retained = {pid: SimpleNamespace(pid=pid, creation_time_100ns=fact['birth'],
                         handle='process:'+str(pid)) for pid, fact in self.facts.items()}
        self.proxy_exit_observed = self.worker_exited = self.waiting = False
        self.helper_snapshots = 0
        self.timeline = []
        self.direct_terminations = []
        self.api.terminate_process = self.direct_terminations.append
        self.post_ack_launcher_polls = 0
    def launch(self, *args, **kwargs):
        assert self.closed is False, 'private Job closed between phases'
        if self.launched:
            assert self.reader.terminal_delivered, 'build before acquisition terminal'
            assert all(fact['exit'] == 0 for fact in self.facts.values()), 'build before zero active'
        result = super().launch(*args, **kwargs)
        self.timeline.append('launch:'+str(result.pid))
        return result
    def validate_pid(self, pid, creation_time_100ns=None):
        if pid not in self.retained:
            return super().validate_pid(pid, creation_time_100ns)
        ref = self.retained[pid]
        if creation_time_100ns != ref.creation_time_100ns or self.facts[pid]['member'] is not True:
            raise ControllerFailure('synthetic lifecycle exact Job identity mismatch')
        return ref
    def process_exit(self, process):
        if process.pid in self.facts:
            if (process.pid == 200 and self.acks and not self.proxy_exit_observed
                    and self.schedule.startswith('delayed')):
                self.post_ack_launcher_polls += 1
                if self.schedule == 'delayed_after_native_precheck' and self.post_ack_launcher_polls == 1:
                    return None
                self.proxy_exit_observed = True
                self.timeline.append('close_became_durable_after_initial_read')
                self.facts[200]['exit'] = self.facts[201]['exit'] = 0
                if self.damage == 'premature_launcher': self.facts[201]['exit'] = None
                if self.damage == 'premature_interpreter': self.facts[200]['exit'] = None
                if self.damage == 'unsuccessful_proxy_exit': self.facts[201]['exit'] = 1
                if self.damage == 'reconcile_deadline': self.clock.now += 1801
                self.worker_exited = self.schedule == 'delayed_worker_exit'
            return self.facts[process.pid]['exit']
        if process.pid == 100:
            if self.schedule == 'helper_lag' and self.acks and not self.worker_exited:
                self.worker_exited = True
                self.facts[200]['exit'] = self.facts[201]['exit'] = 0
                self.timeline.append('base_processes_exited_helper_still_active')
            return 0 if self.worker_exited else None
        return super().process_exit(process)
    def snapshot(self):
        if self.worker_exited and 202 in self.facts and self.facts[202]['exit'] is None:
            self.waiting = True
            self.helper_snapshots += 1
            if self.damage == 'unknown_remaining':
                self.facts[203] = dict(birth=30000,parent=999,member=True,exit=None)
            if self.damage == 'helper_birth': self.facts[202]['birth'] = 90000
            if self.damage == 'helper_membership': self.facts[202]['member'] = False
            if self.helper_snapshots > 1 and self.damage != 'helper_timeout':
                self.facts[202]['exit'] = 0
                self.timeline.append('verified_helper_exited')
        active = [pid for pid, fact in self.facts.items() if fact['exit'] is None]
        return dict(active_processes=len(active), job_committed_bytes=1024,
                    owned=[dict(pid=pid,creation_time_100ns=fact['birth'],in_job=fact['member'],
                                exit_code=fact['exit']) for pid,fact in self.facts.items()])
    def cleanup(self, **kwargs):
        self.timeline.append('final_job_cleanup')
        rows = [dict(pid=pid,creation_time_100ns=fact['birth'],exit_code=0)
                for pid,fact in self.facts.items()
                if not (self.damage == 'missing_helper_exit' and pid == 202)]
        return dict(verified=True, active_processes=0,
                    owned_exits=rows, errors=[])


class LifecycleEvents:
    def __init__(self, backend, first, closing, terminal):
        self.backend, self.first, self.closing, self.terminal = backend, first, closing, terminal
        self.initial_delivered = self.close_delivered = self.terminal_delivered = False
        self.terminal_reads = 0
        self.close_reads = 0
    def read(self, terminal=False):
        if terminal:
            self.terminal_reads += 1
        if not self.initial_delivered:
            self.initial_delivered = True
            return self.first
        if self.backend.schedule == 'helper_lag':
            if not self.backend.worker_exited:
                return []
            self.terminal_delivered = True
            result, self.terminal = self.terminal, []
            return result
        if not self.backend.proxy_exit_observed:
            return []
        if not self.close_delivered:
            self.close_delivered = True
            self.close_reads += 1
            self.backend.timeline.append('durable_close_consumed')
            result, self.closing = self.closing, []
            if self.backend.worker_exited:
                self.terminal_delivered = True
                result += self.terminal
                self.terminal = []
            return result
        if not self.terminal_delivered:
            self.backend.worker_exited = self.terminal_delivered = True
            result, self.terminal = self.terminal, []
            return result
        return []


def lifecycle_session(tmp_path, schedule, damage=None):
    import hashlib
    backend = LifecycleBackend(schedule, damage)
    phase_plans = plans(tmp_path, backend=backend)
    ledger = tmp_path/'lifecycle-proxy.jsonl'
    writer = BudgetLedger(ledger, CEILING, 7)
    writer.record('listening', address=['127.0.0.1',12345], pid=201)
    writer.record('tunnel_start', 'source-1', 'github.com:443')
    writer.charge('source-1', 'github.com:443', b'ab')
    writer.record('tunnel_end', 'source-1', 'github.com:443')
    writer.record('end', status='closed_unqualified', sockets_closed=True)
    writer.close()
    launcher, interpreter = proxy_identity(200,20000,100), proxy_identity(201,20001,200)
    pair = dict(schema=1,launcher=launcher,interpreter=interpreter,listening_pid=201)
    first = [dict(event='phase_start',phase='acquisition'),
             dict(event='proxy_launcher_started',schema=1,launcher=launcher),
             dict(event='proxy_binding_requested',schema=1,launcher=launcher,interpreter=interpreter,
                  same_process=False,ready_pid=201), dict(event='proxy_listening',**pair)]
    close = dict(event='proxy_closing',**pair)
    exits = [dict(event='proxy_interpreter_exit',schema=1,identity=interpreter,exit_code=0,identity_verified=True),
             dict(event='proxy_launcher_exit',schema=1,identity=launcher,exit_code=0,identity_verified=True)]
    terminal = [dict(event='acquisition_terminal',ledger_path=str(ledger),ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
                     cumulative_bytes=9,prior_bytes=7,proxy_launcher_pid=200,proxy_interpreter_pid=201,proxy_identity_schema=1),
                dict(event='phase_complete',phase='acquisition')]
    if damage == 'wrong_prior': terminal[0]['prior_bytes'] = 8
    if damage == 'wrong_cumulative': terminal[0]['cumulative_bytes'] = 10
    if damage == 'wrong_ledger_pid':
        rows = [json.loads(line) for line in ledger.read_text().splitlines()]
        next(row for row in rows if row['event']=='listening')['pid'] = 200
        ledger.write_text(''.join(json.dumps(row)+'\n' for row in rows))
        terminal[0]['ledger_sha256'] = hashlib.sha256(ledger.read_bytes()).hexdigest()
    if damage == 'mismatched_close': close['listening_pid'] = 999
    if damage == 'malformed_close': close = dict(event='proxy_closing')
    if schedule == 'helper_lag':
        first.append(close)
        remaining, terminal = [], exits+terminal
    else:
        remaining = [close]+exits
        if damage in ('absent_close','premature_launcher','premature_interpreter'):
            remaining = []
        if damage == 'invalid_close_order': remaining = exits+[close]
    reader = LifecycleEvents(backend, first, remaining, terminal)
    backend.reader = reader
    phase_plans[0].update(events_reader=reader,ledgerpath=ledger)
    clock = Clock()
    backend.clock = clock
    class LifecycleSampler(Sampler):
        def latest(self):
            value = super().latest()
            if (damage == 'reconcile_resource' and backend.proxy_exit_observed
                    or damage == 'helper_resource' and backend.waiting):
                value['disk_free_bytes'] = 8589934591
            return value
    sampler = LifecycleSampler(clock)
    if damage == 'helper_query_close':
        def failed_close(handle):
            if handle == 'query:202': raise OSError('injected query close failure')
            backend.api.closed.append(handle)
        backend.api.close_handle = failed_close
    if damage == 'helper_query_exit':
        backend.api.query_exit_code = lambda handle: 259
    if damage == 'helper_query_race':
        def query_after_native_exit(handle):
            pid = int(handle.split(':')[1])
            if pid == 202 and backend.waiting and backend.facts[pid]['exit'] is None:
                backend.facts[pid]['exit'] = 0
                backend.timeline.append('helper_exited_between_native_queries')
            code = backend.facts[pid]['exit']
            return 259 if code is None else code
        backend.api.query_exit_code = query_after_native_exit
    if damage == 'helper_handle_pid':
        original_pid = backend.api.process_id
        backend.api.process_id = lambda handle: 999 if handle=='query:202' and backend.waiting else original_pid(handle)
    if damage == 'helper_path_query':
        original_image = backend.api.image_path
        def unavailable_image(handle):
            if handle == 'query:202' and backend.waiting:
                raise OSError('injected phase helper image query unavailable')
            return original_image(handle)
        backend.api.image_path = unavailable_image
    def sleep(amount):
        if backend.waiting and damage in ('helper_timeout','helper_deadline'):
            clock.now += 1801
        else:
            clock.sleep(amount)
    class LifecycleWatchdog(Watchdog):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper_wait_beats = 0
            self.closed = False
            backend.watchdog = self
        def beat(self, *args):
            if backend.waiting:
                assert self.closed is False
                self.helper_wait_beats += 1
        def close(self):
            self.closed = True
    result = run_session(backend,sampler,phase_plans,clock=clock,sleep=sleep,
                         watchdog_factory=LifecycleWatchdog)
    return result, backend


@pytest.mark.parametrize('schedule', ['delayed_worker_alive', 'delayed_worker_exit', 'delayed_after_native_precheck'])
def test_default_session_reconciles_durable_close_after_read_before_observed_proxy_exit(tmp_path, schedule):
    result, backend = lifecycle_session(tmp_path, schedule)
    assert result['status']=='controlled_phases_passed', result
    assert backend.timeline.index('close_became_durable_after_initial_read') < backend.timeline.index('durable_close_consumed')
    assert len(backend.launched)==2 and backend.terminated==0
    assert result['downloaded_upper_bound_bytes']==9
    assert result['proxy_identity_cleanup'][0]['verified'] is True


def test_default_session_waits_only_for_already_verified_helper_before_build(tmp_path):
    result, backend = lifecycle_session(tmp_path, 'helper_lag')
    assert result['status']=='controlled_phases_passed', result
    assert backend.helper_snapshots>=2
    assert backend.timeline.index('verified_helper_exited') < backend.timeline.index('launch:101')
    assert backend.timeline.index('launch:101') < backend.timeline.index('final_job_cleanup')
    assert backend.watchdog.helper_wait_beats>=1
    assert backend.terminated==0 and backend.api.closed==['query:202']
    assert backend.direct_terminations==[]
    assert result['proxy_identity_cleanup'][0]['verified'] is True


@pytest.mark.parametrize('damage', ['absent_close','mismatched_close','malformed_close',
                                  'invalid_close_order','premature_launcher','premature_interpreter',
                                  'unsuccessful_proxy_exit'])
def test_default_session_durable_exit_reconciliation_never_accepts_invalid_lifecycle(tmp_path, damage):
    result, backend = lifecycle_session(tmp_path,'delayed_worker_alive',damage)
    assert result['status']=='failure', result
    assert backend.terminated>=1 and len(backend.launched)==1
    assert backend.direct_terminations==[]
    assert backend.reader.close_reads==1


@pytest.mark.parametrize('damage', ['unknown_remaining','helper_birth','helper_membership',
                                  'helper_timeout','helper_query_exit','helper_handle_pid','helper_path_query'])
def test_default_session_wait_rejects_unknown_changed_or_unproven_helper(tmp_path, damage):
    result, backend = lifecycle_session(tmp_path,'helper_lag',damage)
    assert result['status']=='failure', result
    assert backend.terminated>=1 and len(backend.launched)==1
    assert backend.direct_terminations==[]


@pytest.mark.parametrize('damage', ['missing_helper_exit','helper_query_close'])
def test_default_session_final_cleanup_proof_remains_mandatory(tmp_path, damage):
    result, backend = lifecycle_session(tmp_path,'helper_lag',damage)
    assert result['status']=='failure', result
    assert result['proxy_identity_cleanup'][0]['verified'] is False


@pytest.mark.parametrize('schedule,damage', [('delayed_worker_alive','reconcile_deadline'),
                                           ('delayed_worker_alive','reconcile_resource'),
                                           ('helper_lag','helper_deadline'),
                                           ('helper_lag','helper_resource')])
def test_default_session_deadlines_and_resources_remain_active_during_exit_handling(tmp_path, schedule, damage):
    result, backend = lifecycle_session(tmp_path,schedule,damage)
    assert result['status']=='failure', result
    assert backend.terminated>=1 and len(backend.launched)==1
    assert ('deadline' in result['reason'] if 'deadline' in damage else 'disk_floor' in result['reason'])


@pytest.mark.parametrize('damage', ['wrong_prior','wrong_cumulative','wrong_ledger_pid'])
def test_default_session_reconciled_exit_still_requires_original_accounting_and_interpreter_ledger(tmp_path, damage):
    result, backend = lifecycle_session(tmp_path,'delayed_worker_alive',damage)
    assert result['status']=='failure', result
    assert backend.terminated>=1 and len(backend.launched)==1
    expected='proxy_identity_differs' if damage=='wrong_ledger_pid' else 'worker_proxy_total_differs'
    assert expected in result['reason']


def test_default_session_reconciles_verified_helper_exit_between_native_queries(tmp_path):
    result, backend = lifecycle_session(tmp_path,'helper_lag','helper_query_race')
    assert result['status']=='controlled_phases_passed', result
    assert backend.timeline.index('helper_exited_between_native_queries') < backend.timeline.index('launch:101')
    assert backend.terminated==0 and backend.direct_terminations==[]
    assert backend.api.closed==['query:202']
    assert result['proxy_identity_cleanup'][0]['verified'] is True
