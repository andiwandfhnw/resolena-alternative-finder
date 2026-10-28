import hashlib
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.uc001_granite_acquisition_proxy.proxy import BudgetLedger, CEILING
from scripts.uc001_granite_controller import worker
from tests.unit.test_granite_controller_worker import Events, ProxyApi, ProxyInput


PRIOR_SHA = '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a'


class SelftestRunner:
    def __init__(self, root, journal, *, split=True, damage=None):
        self.root, self.journal = root, journal
        self.api = ProxyApi(split)
        self.split, self.damage = split, damage
        self.starts = []
        self.closed = False

    def selftest_worker_identity(self):
        return dict(pid=42, creation_time_100ns=800, parent_pid=41, in_any_job=True)

    def run(self, *args, **kwargs):
        raise AssertionError('Self-test must not execute Git, toolchain or build commands')

    def start(self, argv, label, env=None, stdin=False):
        assert label == 'proxy' and stdin
        self.starts.append(argv)
        ledger = self.root / 'evidence/acquisition-proxy.jsonl'
        pid = 701 if self.split else 700
        self.ready_value = dict(pid=pid, proxy_url='http://127.0.0.1:12345', ledger=str(ledger),
                                prior_bytes=0, remaining_bytes=CEILING)
        if self.damage == 'wrong_ready_pid':
            self.ready_value['pid'] = 999
        if self.damage == 'wrong_parent':
            self.api.rows['interpreter']['parent'] = 999
        if self.damage == 'wrong_member':
            self.api.rows['interpreter']['member'] = False
        if self.damage == 'changed_birth':
            self.api.rows['launcher']['birth'] = 999
        writer = BudgetLedger(ledger, CEILING, 0, prior_receipt_sha256=PRIOR_SHA)
        writer.record('acquisition_clock', acquisition_started_utc='2026-10-27T12:00:00+00:00',
                      remaining_seconds=1799)
        writer.record('listening', address=['127.0.0.1', 12345],
                      pid=700 if self.damage == 'wrong_listening_pid' else pid)
        if self.damage in ('CONNECT', 'tunnel_start', 'tunnel_end', 'debit', 'outbound'):
            writer.record(self.damage, tunnel_id='unapproved', destination='github.com:443')
        writer.record('end', status='closed_unqualified', sockets_closed=True)
        writer.close()
        identity = dict(pid=700, creation_time_100ns=900, parent_pid=42, in_any_job=True)
        process = SimpleNamespace(pid=700, _handle='launcher', stdin=ProxyInput(),
            poll=lambda: self.api.rows['launcher']['exit'],
            wait=lambda: self.api.rows['launcher']['exit'])
        out_path = self.root / 'evidence/proxy.stdout.log'
        err_path = self.root / 'evidence/proxy.stderr.log'
        self.proxy = worker.Child(process, label, out_path, err_path,
                                  out_path.open('xb'), err_path.open('xb'), identity)
        self.native = worker.NativeRunner(self.root, self.journal, {}, api=self.api,
            control=BytesIO(b'' if self.damage == 'missing_ack' else b'PROXY_BOUND\n'))
        self.journal.emit('proxy_launcher_started', schema=1, launcher=identity)
        return self.proxy

    def ready(self, proxy):
        return self.ready_value

    def bind_proxy(self, proxy, ready):
        result = self.native.bind_proxy(proxy, ready)
        if self.damage in ('premature_launcher', 'premature_interpreter'):
            role = self.damage.removeprefix('premature_')
            self.api.rows[role]['exit'] = 0
        return result

    def mark_proxy_closing(self, proxy):
        self.native.mark_proxy_closing(proxy)

    def wait(self, proxy):
        assert proxy.process.stdin.value == b'CLOSE\n'
        ledger = self.root / 'evidence/acquisition-proxy.jsonl'
        closed = dict(status='meter_closed_unqualified', cleanup_verified=True,
                      cumulative_bytes=0, ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest())
        proxy.stdout_file.write((json.dumps(self.ready_value) + '\n' + json.dumps(closed) + '\n').encode())
        proxy.stdout_file.flush()
        for row in self.api.rows.values():
            row['exit'] = 0
        return self.native.wait(proxy)

    def finish_proxy_selftest_handles(self, proxy):
        self.native.close_proxy_handles(proxy)
        return dict(interpreter_query=True, launcher_handle=True, stdout=True, stderr=True)

    def close_proxy_handles(self, proxy):
        self.native.close_proxy_handles(proxy)
        self.closed = True


def fixture(tmp_path, monkeypatch, **options):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline worker test cannot open processes or sockets')
    monkeypatch.setattr(worker.subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'socket', forbidden)
    root = tmp_path / 'selftest'
    (root / 'evidence').mkdir(parents=True)
    guard = tmp_path / 'guard.py'
    guard.write_text('synthetic guard fixture, never executed\n')
    config = dict(root=str(root), selftest_only=True,
        original_start_utc='2026-10-27T12:00:00+00:00',
        proxy_helper=str(Path('scripts/uc001_granite_acquisition_proxy/proxy.py').resolve()),
        proxy_sha256=worker.PROXY_SHA256,
        prior_receipt=str(Path('build/uc001-granite-prior-accounting-final-v1/prior-budget.json').resolve()),
        prior_sha256=PRIOR_SHA, guard_entry=str(guard), guard_sha256=worker.digest(guard))
    journal = Events()
    runner = SelftestRunner(root, journal, **options)
    return config, journal, runner


@pytest.mark.parametrize('split', [True, False])
def test_selftest_worker_reuses_real_binding_and_closes_without_git(tmp_path, monkeypatch, split):
    config, journal, runner = fixture(tmp_path, monkeypatch, split=split)
    worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert len(runner.starts) == 1
    argv = runner.starts[0]
    assert argv[:3] == [worker.sys.executable, '-I', '-B']
    assert argv[3] == config['guard_entry']
    assert argv[argv.index('--proxy-helper') + 1] == config['proxy_helper']
    assert '--guard-log' in argv and '--prior-sha256' in argv
    assert runner.closed
    assert runner.api.closed == (['interpreter'] if split else [])
    terminal = next(row for row in journal.events if row['event'] == 'acquisition_terminal')
    assert terminal['cumulative_bytes'] == terminal['prior_bytes'] == 0
    assert terminal['proxy_launcher_pid'] == 700
    assert terminal['proxy_interpreter_pid'] == (701 if split else 700)
    assert terminal['proxy_binding_selftest'] is True
    assert terminal['zero_acquisition_events'] is True
    assert all(terminal['worker_handles_closed'].values())
    assert not any((Path(config['root']) / name).exists() for name in ('src', 'build', 'source-repository'))


@pytest.mark.parametrize('damage', ['wrong_ready_pid', 'wrong_parent', 'wrong_member', 'changed_birth',
                                   'missing_ack', 'premature_launcher', 'premature_interpreter',
                                   'wrong_listening_pid', 'CONNECT', 'tunnel_start', 'tunnel_end',
                                   'debit', 'outbound'])
def test_selftest_worker_fails_closed_and_closes_retained_queries(tmp_path, monkeypatch, damage):
    config, journal, runner = fixture(tmp_path, monkeypatch, damage=damage)
    with pytest.raises((worker.WorkerFailure, RuntimeError)):
        worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert runner.closed
    assert not any(row['event'] == 'phase_complete' for row in journal.events)


@pytest.mark.parametrize('damage', ['prior_hash', 'prior_bytes', 'guard_hash', 'not_selftest', 'real_root'])
def test_selftest_worker_rejects_changed_pins_before_start(tmp_path, monkeypatch, damage):
    config, journal, runner = fixture(tmp_path, monkeypatch)
    if damage == 'prior_hash':
        config['prior_sha256'] = '0' * 64
    elif damage == 'prior_bytes':
        changed = tmp_path / 'changed-prior.json'
        changed.write_bytes(Path(config['prior_receipt']).read_bytes() + b'\n')
        config['prior_receipt'] = str(changed)
    elif damage == 'guard_hash':
        config['guard_sha256'] = '0' * 64
    elif damage == 'not_selftest':
        config['selftest_only'] = False
    else:
        config['root'] = worker.ROOT
    with pytest.raises((worker.WorkerFailure, RuntimeError)):
        worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert runner.starts == []


@pytest.mark.parametrize('split', [True, False])
def test_actual_native_runner_selftest_closes_query_and_retained_launcher_handle(tmp_path, split):
    from tests.unit.test_granite_controller_worker import proxy_binding_fixture
    runner, proxy, api, journal, ready = proxy_binding_fixture(tmp_path, split=split)

    class Handle(str):
        closed = False
        def Close(self):
            self.closed = True

    proxy.process._handle = Handle('launcher')
    try:
        runner.bind_proxy(proxy, ready)
        runner.mark_proxy_closing(proxy)
        for row in api.rows.values():
            row['exit'] = 0
        handles = runner.finish_proxy_selftest_handles(proxy)
        assert handles == dict(interpreter_query=True, launcher_handle=True, stdout=True, stderr=True)
        assert proxy.process._handle.closed is True
        assert api.closed == (['interpreter'] if split else [])
    finally:
        runner.close_proxy_handles(proxy)


def test_actual_native_runner_selftest_never_reports_unclosed_launcher_handle(tmp_path):
    from tests.unit.test_granite_controller_worker import proxy_binding_fixture
    runner, proxy, api, journal, ready = proxy_binding_fixture(tmp_path)

    class Handle(str):
        closed = False
        def Close(self):
            pass

    proxy.process._handle = Handle('launcher')
    try:
        runner.bind_proxy(proxy, ready)
        runner.mark_proxy_closing(proxy)
        for row in api.rows.values():
            row['exit'] = 0
        with pytest.raises(worker.WorkerFailure, match='launcher_handle_not_closed'):
            runner.finish_proxy_selftest_handles(proxy)
    finally:
        runner.close_proxy_handles(proxy)


@pytest.mark.parametrize('valid', [True, False])
def test_actual_selftest_worker_identity_query_is_closed_even_on_invalid_identity(tmp_path, valid):
    api = ProxyApi(split=False)
    api.rows['launcher']['pid'] = worker.os.getpid()
    if not valid:
        api.rows['launcher']['birth'] = 0
    runner = worker.NativeRunner(tmp_path, Events(), {}, api=api)
    if valid:
        identity = runner.selftest_worker_identity()
        assert identity['pid'] == worker.os.getpid()
        assert identity['creation_time_100ns'] == 900
    else:
        with pytest.raises(worker.WorkerFailure, match='retained_identity_invalid'):
            runner.selftest_worker_identity()
    assert api.closed == ['launcher']


def test_selftest_never_retries_an_unknown_query_handle_close(tmp_path, monkeypatch):
    config, journal, runner = fixture(tmp_path, monkeypatch)
    original_start = runner.start

    def start(*args, **kwargs):
        proxy = original_start(*args, **kwargs)
        def close_failed(handle):
            runner.api.closed.append(handle)
            raise RuntimeError('synthetic query close failed')
        runner.api.close_handle = close_failed
        return proxy

    runner.start = start
    runner.finish_proxy_selftest_handles = lambda proxy: runner.native.finish_proxy_selftest_handles(proxy)
    with pytest.raises(RuntimeError, match='query close failed'):
        worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert runner.api.closed == ['interpreter']
    assert runner.proxy.stdout_file.closed and runner.proxy.stderr_file.closed
    assert not any(row['event'] == 'phase_complete' for row in journal.events)


def test_actual_bind_identity_failure_closes_uncertain_query_handle_only_once(tmp_path, monkeypatch):
    config, journal, runner = fixture(tmp_path, monkeypatch, damage='wrong_parent')
    original_start = runner.start

    def start(*args, **kwargs):
        proxy = original_start(*args, **kwargs)
        def close_failed(handle):
            runner.api.closed.append(handle)
            raise RuntimeError('synthetic bind-failure query close failed')
        runner.api.close_handle = close_failed
        return proxy

    runner.start = start
    with pytest.raises(RuntimeError, match='bind-failure query close failed'):
        worker.run_proxy_binding_selftest(config, journal, runner=runner)
    assert runner.proxy.interpreter_opened is True
    assert runner.proxy.binding is None
    assert runner.api.opened == [701]
    assert runner.api.closed == ['interpreter']
    assert runner.proxy.stdout_file.closed and runner.proxy.stderr_file.closed
    assert not any(row['event'] == 'phase_complete' for row in journal.events)
