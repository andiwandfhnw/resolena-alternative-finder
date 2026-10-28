from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.uc001_granite_controller import worker
from scripts.uc001_granite_controller.controller import ControllerFailure, PhaseMonitor
from tests.unit.test_granite_controller_worker import ProxyApi
from tests.unit.test_granite_proxy_binding_worker import SelftestRunner, fixture


class FlowApi(ProxyApi):
    def __init__(self, split=True, helper=False, extra=False):
        super().__init__(split)
        if helper or extra:
            self.rows['helper'] = dict(pid=702, birth=902, parent=700, member=True, exit=None,
                image=r'R:\Windows\System32\conhost.exe' if helper else r'D:\Fake\conhost.exe')

    def row(self, handle):
        if ':' in handle and handle in self.closed:
            raise RuntimeError('attempted to query a closed injected handle')
        return self.rows[handle.rsplit(':', 1)[-1]]

    def process_id(self, handle): return self.row(handle)['pid']
    def creation_time(self, handle): return self.row(handle)['birth']
    def parent_pid(self, handle): return self.row(handle)['parent']
    def exit_code(self, handle): return self.row(handle)['exit']

    def any_job(self, handle, job, pointer):
        assert job is None
        pointer._obj.value = int(self.row(handle)['member'])
        return 1

    def in_job(self, handle, job):
        assert job == 'flow-private-job'
        return self.row(handle)['member']

    def children_of(self, parents, timeout_seconds=1):
        return {(row['pid'], row['parent']) for row in self.rows.values()
                if row['parent'] in parents and row['exit'] is None}

    def name_for(self, pid):
        for name, row in self.rows.items():
            if row['pid'] == pid:
                return name
        raise worker.WorkerFailure('unknown flow identity')

    def open_process(self, pid, can_terminate=False):
        assert can_terminate is False
        self.opened.append(pid)
        return 'worker-query:' + self.name_for(pid)

    def open_query_process(self, pid):
        return 'helper-query:' + self.name_for(pid)

    def image_path(self, handle): return self.row(handle)['image']
    def query_exit_code(self, handle):
        code = self.exit_code(handle)
        return 259 if code is None else code
    def system_console_path(self): return r'R:\Windows\System32\conhost.exe'


class FlowBackend:
    handle = 'flow-private-job'

    def __init__(self, api):
        self.api = api
        self.retained = {row['pid']: SimpleNamespace(pid=row['pid'],
            creation_time_100ns=row['birth'], handle='controller-retained:' + name)
            for name, row in api.rows.items()}

    def validate_pid(self, pid, creation_time_100ns=None):
        process = self.retained[pid]
        if (self.api.creation_time(process.handle) != creation_time_100ns
                or self.api.in_job(process.handle, self.handle) is not True):
            raise ControllerFailure('flow exact retained identity differs')
        return process

    def process_exit(self, process): return self.api.exit_code(process.handle)


class FlowJournal:
    def __init__(self):
        self.events = []

    def emit(self, event, **values):
        row = dict(event=event, **values)
        self.events.append(row)
        self.monitor.accept([row])


class FlowRunner(SelftestRunner):
    def __init__(self, root, journal, *, split=True, helper=False, extra=False, damage=None):
        super().__init__(root, journal, split=split, damage=damage)
        self.api = FlowApi(split, helper, extra)
        self.control = BytesIO()
        self.acks = []

    def acknowledge(self, token):
        assert self.monitor.proxy_bound
        assert token == b'PROXY_BOUND\n' and self.acks == []
        if self.damage != 'missing_ack':
            self.acks.append(token)
            self.control.write(token)
            self.control.seek(0)

    def start(self, *args, **kwargs):
        proxy = super().start(*args, **kwargs)
        self.native.control = self.control
        return proxy

    def mark_proxy_closing(self, proxy):
        assert self.acks == [b'PROXY_BOUND\n']
        assert self.monitor.proxy_bound and self.monitor.proxy_listening
        super().mark_proxy_closing(proxy)


def flow(tmp_path, monkeypatch, **options):
    config, _, _ = fixture(tmp_path, monkeypatch)
    journal = FlowJournal()
    runner = FlowRunner(Path(config['root']), journal, **options)
    backend = FlowBackend(runner.api)
    observations = []
    monitor = PhaseMonitor(dict(name='acquisition', expected_prior_bytes=0,
        ledgerpath=Path(config['root']) / 'evidence/acquisition-proxy.jsonl'), backend,
        lambda event, **values: observations.append(dict(event=event, **values)),
        acknowledge=runner.acknowledge)
    journal.monitor = runner.monitor = monitor
    return config, runner, journal, monitor, observations


@pytest.mark.parametrize('split,helper', [(True, False), (True, True), (False, False)])
def test_actual_selftest_worker_events_bind_real_monitor_ack_and_zero_terminal(tmp_path, monkeypatch, split, helper):
    config, runner, journal, monitor, observations = flow(tmp_path, monkeypatch,
                                                        split=split, helper=helper)
    worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert monitor.finish() == 0
    assert runner.acks == [b'PROXY_BOUND\n']
    assert monitor.proxy.pid == (701 if split else 700)
    assert set(monitor.proxy_role_exits) == {'launcher', 'interpreter'}
    assert monitor.terminal['zero_acquisition_events'] is True
    assert all(monitor.terminal['worker_handles_closed'].values())
    assert any(row['event'] == 'proxy_binding_verified' for row in observations)
    assert monitor.proxy_helpers.keys() == ({700} if helper else set())
    receipt = monitor.cleanup(dict(verified=True, active_processes=0,
        owned_exits=[dict(pid=row['pid'], creation_time_100ns=row['birth'], exit_code=row['exit'])
                     for row in runner.api.rows.values()]))
    assert receipt['verified'] is True and receipt['query_handles_closed'] is True
    assert all(row['exit_verified'] for row in receipt['identities'])
    assert 'helper-query:helper' in runner.api.closed if helper else True
    assert 'worker-query:interpreter' in runner.api.closed if split else True
    assert all(not row['termination_requested'] for row in receipt['helper_queries'])


@pytest.mark.parametrize('damage', ['wrong_ready_pid', 'wrong_listening_pid', 'missing_ack', 'CONNECT'])
def test_actual_worker_flow_rejects_identity_ack_or_zero_network_gaps(tmp_path, monkeypatch, damage):
    config, runner, journal, monitor, _ = flow(tmp_path, monkeypatch, damage=damage)
    with pytest.raises((worker.WorkerFailure, ControllerFailure, RuntimeError)):
        worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert monitor.complete is False
    assert not any(row['event'] == 'phase_complete' for row in journal.events)
    if damage == 'wrong_ready_pid':
        assert runner.acks == []
    if damage == 'missing_ack':
        assert runner.acks == []
        assert not monitor.proxy_listening


def test_actual_worker_flow_rejects_unclassified_branch_before_private_ack(tmp_path, monkeypatch):
    config, runner, journal, monitor, _ = flow(tmp_path, monkeypatch, extra=True)
    try:
        with pytest.raises((ControllerFailure, RuntimeError)):
            worker.run_proxy_binding_selftest(config, journal, runner=runner)
        assert runner.acks == [] and monitor.proxy_bound is False
        assert not any(row['event'] == 'proxy_closing' for row in journal.events)
    finally:
        for row in runner.api.rows.values():
            row['exit'] = 57345
        monitor.cleanup(dict(verified=True, active_processes=0, owned_exits=[
            dict(pid=row['pid'], creation_time_100ns=row['birth'], exit_code=row['exit'])
            for row in runner.api.rows.values()]))
