import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.uc001_granite_acquisition_proxy.proxy import BudgetLedger, CEILING
from scripts.uc001_granite_controller import proxy_binding_selftest as selftest
from scripts.uc001_granite_controller.controller import ControllerFailure
from tests.unit.test_granite_controller_run import BindingBackend, proxy_identity


def ledger(path, pid=201):
    writer = BudgetLedger(path, CEILING, 0, prior_receipt_sha256=selftest.PRIOR_SHA256)
    writer.record('listening', address=['127.0.0.1', 12345], pid=pid)
    writer.record('end', status='closed_unqualified', sockets_closed=True)
    writer.close()


def test_zero_acquisition_ledger_accepts_only_unchanged_prior_and_listener(tmp_path):
    path = tmp_path/'proxy.jsonl'; ledger(path)
    observation = selftest.validate_zero_acquisition_ledger(path, 0, 201, terminal=True)
    assert observation['complete'] is True
    assert observation['total'] == 0
    assert observation['event_counts'] == {'start': 1, 'listening': 1, 'end': 1}


@pytest.mark.parametrize('event', ['CONNECT', 'connect', 'tunnel_start', 'tunnel_end', 'debit',
                                  'upstream', 'outbound', 'unknown'])
def test_every_tunnel_or_outbound_event_is_rejected_even_at_zero_bytes(tmp_path, event):
    path = tmp_path/'proxy.jsonl'; ledger(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows.insert(-1, dict(rows[1], event=event, tunnel_id='x', destination='github.com:443'))
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    with pytest.raises(ControllerFailure):
        selftest.validate_zero_acquisition_ledger(path, 0, 201, terminal=True)


@pytest.mark.parametrize('damage', ['prior_hash', 'counter', 'pid', 'partial', 'missing_end'])
def test_zero_guard_fails_unknown_or_wrong_receipt_listener_or_terminal(tmp_path, damage):
    path = tmp_path/'proxy.jsonl'; ledger(path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if damage == 'prior_hash': rows[0]['prior_receipt_sha256'] = '0'*64
    if damage == 'counter': rows[1]['cumulative_bytes'] = 1
    if damage == 'pid': rows[1]['pid'] = 200
    if damage == 'missing_end': rows.pop()
    text = ''.join(json.dumps(row)+'\n' for row in rows)
    path.write_text(text+'{' if damage == 'partial' else text)
    with pytest.raises(ControllerFailure):
        selftest.validate_zero_acquisition_ledger(path, 0, 201, terminal=True)


def test_live_guard_tolerates_only_an_unfinished_tail_and_then_rechecks_it(tmp_path):
    path = tmp_path/'proxy.jsonl'; ledger(path)
    path.write_bytes(path.read_bytes()+b'{')
    assert selftest.validate_zero_acquisition_ledger(path, 0, 201)['complete'] is True
    with pytest.raises(ControllerFailure):
        selftest.validate_zero_acquisition_ledger(path, 0, 201, terminal=True)


class Clock:
    def __init__(self): self.value = 1.0
    def __call__(self): return self.value
    def sleep(self, amount): self.value += amount


class Guard:
    def __init__(self, backend, deadline, clock):
        self.failure = None; self.closed = False; backend.guard = self
    def start(self): pass
    def close(self): self.closed = True


class Backend(BindingBackend):
    def __init__(self, split=True, helper=False, damage=None, worker_helper=False):
        super().__init__(split=split, helper=helper, damage=damage)
        self.facts[90] = dict(birth=10000, parent=1, member=True, exit=None)
        self.facts[100] = dict(birth=10001, parent=90, member=True, exit=None)
        if worker_helper:
            self.facts[91] = dict(birth=10002, parent=90, member=True, exit=None,
                                  image=r'R:\Windows\System32\conhost.exe')
        self.retained.update({pid: SimpleNamespace(pid=pid, creation_time_100ns=row['birth'],
            handle='process:'+str(pid)) for pid,row in self.facts.items()})
        self.terminated = self.closed = False; self.acks = []; self.damage = damage
        self.launch_args = None; self.observations = []
    def launch(self, argv, cwd, env, stdoutfile, stderrfile, stdin_pipe=False):
        assert stdin_pipe
        self.launch_args = argv
        return self.retained[90]
    def drain_events(self):
        if self.observations: return []
        self.observations = [dict(event=kind,pid=90,creation_time_100ns=10000)
                             for kind in ('worker_created_suspended','worker_assigned','worker_resumed')]
        return self.observations
    def write_stdin(self, process, token):
        assert process.pid == 90 and token == b'PROXY_BOUND\n'
        self.acks.append(token)
        if self.damage == 'fast_close':
            for row in self.facts.values(): row['exit'] = 0
    def snapshot(self):
        return dict(active_processes=sum(row['exit'] is None for row in self.facts.values()),
                    total_processes=len(self.facts), owned=[dict(pid=pid,
                        creation_time_100ns=row['birth']) for pid,row in self.facts.items()])
    def terminate(self):
        self.terminated = True
        for row in self.facts.values(): row['exit'] = 57345
    def cleanup(self, timeout_seconds=5):
        self.guard_active_during_cleanup = not self.guard.closed
        if self.damage == 'helper_lag': self.facts[202]['exit'] = 0
        rows=[dict(pid=pid,creation_time_100ns=fact['birth'],exit_code=fact['exit'])
              for pid,fact in self.facts.items()]
        if self.damage == 'missing_cleanup_exit': rows = [row for row in rows if row['pid']!=201]
        return dict(verified=True, active_processes=0, total_processes=len(self.facts),
                    owned_exits=rows, errors=[])
    def close(self): self.closed = True


def fixture(tmp_path, *, split=True, helper=False, worker_helper=False, damage=None):
    backend=Backend(split,helper,damage,worker_helper)
    path=tmp_path/'proxy.jsonl'; ledger(path,201 if split else 200)
    launcher=proxy_identity(200,20000,100)
    interpreter=proxy_identity(201,20001,200) if split else dict(launcher)
    pair=dict(schema=1,launcher=launcher,interpreter=interpreter,listening_pid=interpreter['pid'])
    request=dict(event='proxy_binding_requested',schema=1,launcher=launcher,interpreter=interpreter,
                 same_process=not split,ready_pid=interpreter['pid'])
    if damage=='ready_pid': request['ready_pid']=999
    if damage=='listening_pid': pair['listening_pid']=200
    phases=[
        [dict(event='phase_start',phase='acquisition',proxy_binding_selftest=True,
              worker_interpreter_identity=proxy_identity(100,10001,90),worker_identity_query_closed=True)],
        [dict(event='proxy_launcher_started',schema=1,launcher=launcher)], [request],
        [dict(event='proxy_listening',**pair)], [dict(event='proxy_closing',**pair)],
        [dict(event='proxy_interpreter_exit',schema=1,identity=interpreter,exit_code=0,identity_verified=True),
         dict(event='proxy_launcher_exit',schema=1,identity=launcher,exit_code=0,identity_verified=True),
         dict(event='acquisition_terminal',ledger_path=str(path),ledger_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              cumulative_bytes=0,prior_bytes=0,proxy_launcher_pid=200,
              proxy_interpreter_pid=interpreter['pid'],proxy_identity_schema=1,
              proxy_binding_selftest=True,zero_acquisition_events=True,
              worker_handles_closed=dict(interpreter_query=True,launcher_handle=True,stdout=True,stderr=True)),
         dict(event='phase_complete',phase='acquisition')]]
    if damage=='worker_parent': phases[0][0]['worker_interpreter_identity']['parent_pid']=999
    if damage=='worker_handle_unclosed': phases[0][0]['worker_identity_query_closed']=False
    if damage=='missing_ack': phases[3]=[dict(event='worker_failure',reason='proxy_controller_binding_ack_missing')]
    if damage=='missing_role_exit': phases[-1].pop(0)
    if damage=='unclosed_worker_handle': phases[-1][-2]['worker_handles_closed']['launcher_handle']=False
    if damage=='nonboolean_worker_handle': phases[-1][-2]['worker_handles_closed']['launcher_handle']=1
    if damage=='extra_job_process':
        backend.facts[999]=dict(birth=99999,parent=42,member=True,exit=None)
        backend.retained[999]=SimpleNamespace(pid=999,creation_time_100ns=99999,handle='process:999')
    if damage=='helper_path': backend.facts[202]['image']=r'D:\Fake\conhost.exe'
    if damage=='helper_membership': backend.facts[202]['member']=False
    if damage=='helper_path_query':
        backend.api.image_path=lambda handle: (_ for _ in ()).throw(RuntimeError('path unavailable'))
    if damage=='helper_identity':
        original=backend.api.creation_time;reads={}
        def unstable(handle):
            reads[handle]=reads.get(handle,0)+1
            return original(handle)+(1 if handle=='query:202' and reads[handle]>1 else 0)
        backend.api.creation_time=unstable
    if damage=='helper_extra':
        backend.facts[203]=dict(birth=20003,parent=200,member=True,exit=None,image=r'D:\Unknown\extra.exe')
        backend.retained[203]=SimpleNamespace(pid=203,creation_time_100ns=20003,handle='process:203')
    if damage=='helper_close':
        close=backend.api.close_handle
        def fail(handle):
            if handle=='query:202': raise RuntimeError('query handle close failed')
            return close(handle)
        backend.api.close_handle=fail
    class Reader:
        def read(self, terminal=False):
            if not phases:return []
            if damage == 'fast_close' and backend.acks:
                rows = [row for batch in phases for row in batch]
                phases.clear()
                return rows
            rows=phases.pop(0)
            if damage in ('premature_launcher','premature_interpreter') and rows[0].get('event')=='proxy_listening':
                backend.facts[200 if damage=='premature_launcher' else 201]['exit']=0
                phases[:] = [[dict(event='worker_failure',reason='native_role_exited_before_planned_close')]]
            if rows[-1].get('event')=='phase_complete':
                for fact in backend.facts.values(): fact['exit']=0
                if damage=='helper_lag': backend.facts[202]['exit']=None
            return rows
    plan=dict(name='acquisition',argv=['prepared-worker','--phase','proxy-binding-selftest'],cwd=tmp_path,
              env={},stdoutfile=tmp_path/'stdout',stderrfile=tmp_path/'stderr',
              events=tmp_path/'events.jsonl',events_reader=Reader(),ledgerpath=path,
              expected_prior_bytes=0,guard_log=tmp_path/'guard.jsonl',expected_controller_pid=1)
    clock=Clock()
    return backend,plan,clock


@pytest.mark.parametrize('split,helper,worker_helper',[(True,False,False),(True,True,True),(False,False,False)])
def test_session_uses_real_monitor_ack_roles_helpers_and_all_cleanup(tmp_path,split,helper,worker_helper):
    backend,plan,clock=fixture(tmp_path,split=split,helper=helper,worker_helper=worker_helper)
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is True,result
    assert backend.acks==[b'PROXY_BOUND\n']
    assert result['suspended_assignment_order_verified'] is True
    assert result['zero_acquisition_events_verified'] is True
    assert result['proxy_identity_cleanup']['verified'] is True
    assert result['worker_identity_cleanup']['verified'] is True
    assert result['resource_fit_established'] is False
    assert result['native_binding_verified'] is False
    assert result['windows_execution'] is False
    assert backend.closed and not backend.terminated
    assert 'query:202' in backend.api.closed if helper else True
    assert 'query:91' in backend.api.closed if worker_helper else True


@pytest.mark.parametrize('damage', ['parent','membership','handle_pid','birth_change','ready_pid',
    'listening_pid','worker_parent','worker_handle_unclosed','missing_ack','missing_role_exit',
    'unclosed_worker_handle','nonboolean_worker_handle','premature_launcher','premature_interpreter','extra_job_process',
    'missing_cleanup_exit','helper_path','helper_close','helper_membership','helper_path_query',
    'helper_identity','helper_extra'])
def test_session_preserves_fail_closed_binding_and_cleanup(tmp_path,damage):
    helper=damage.startswith('helper_')
    backend,plan,clock=fixture(tmp_path,helper=helper,damage=damage)
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is False,result
    assert result['failure_reason']
    assert backend.closed


def test_native_main_rejects_without_explicit_owner_authorization_before_native_api(tmp_path):
    with pytest.raises(ControllerFailure,match='not_authorized'):
        selftest.native_selftest(tmp_path/'config.json',tmp_path/'result',owner_authorized=False)


def test_acceptance_prior_hash_is_fixed_and_not_replaceable_with_another_zero_receipt(tmp_path):
    with pytest.raises(ControllerFailure,match='prior_receipt'):
        selftest.validate_preparation(dict(selftest_only=True,prior_sha256='0'*64),tmp_path)


def test_fast_planned_close_drains_durable_events_before_premature_exit_checks(tmp_path):
    backend,plan,clock=fixture(tmp_path,damage='fast_close')
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is True,result
    assert len(backend.acks)==1


def test_zero_guard_cannot_mark_missing_bootstrap_guard_as_success(tmp_path):
    backend,plan,clock=fixture(tmp_path)
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=False))
    assert result['proxy_binding_selftest_passed'] is False
    assert result['network_guard_verified'] is False


def test_deadline_remains_twenty_seconds_and_failure_terminates_only_backend(tmp_path):
    backend,plan,clock=fixture(tmp_path)
    def slow(amount): clock.value += 21
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=slow,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is False
    assert result['timeout_seconds']==20
    assert backend.terminated and backend.closed


def test_independent_deadline_stays_active_through_native_cleanup_and_handle_close(tmp_path):
    backend,plan,clock=fixture(tmp_path)
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is True,result
    assert backend.guard_active_during_cleanup is True
    assert backend.guard.closed is True


def test_worker_launcher_parent_must_be_the_expected_controller(tmp_path):
    backend,plan,clock=fixture(tmp_path)
    plan['expected_controller_pid']=999
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is False


def test_failure_after_evidence_directory_creation_retains_structured_failure(tmp_path):
    journal=SimpleNamespace(emit=lambda *args,**kwargs:None)
    result=selftest.preserve_native_failure(tmp_path,journal,RuntimeError('native job creation failed'),
                                          windows_execution=False)
    saved=json.loads((tmp_path/'result.json').read_text())
    assert saved==result
    assert result['proxy_binding_selftest_passed'] is False
    assert result['failure_reason']=='native job creation failed'
    assert result['cleanup']['verified'] is False
    assert result['cleanup']['owned_exits']==[]
    assert result['windows_execution'] is False
    assert result['native_binding_verified'] is False


def test_already_verified_helper_may_exit_during_bounded_cleanup_without_direct_termination(tmp_path):
    backend,plan,clock=fixture(tmp_path,helper=True,damage='helper_lag')
    result=selftest.run_binding_session(backend,plan,clock=clock,sleep=clock.sleep,
        watchdog_factory=Guard,guard_validator=lambda path,pid:dict(verified=True))
    assert result['proxy_binding_selftest_passed'] is True,result
    assert result['cleanup']['active_processes']==0
    assert result['proxy_identity_cleanup']['verified'] is True
    assert backend.terminated is False
