import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.uc001_granite_controller import proxy_no_network as guard


PROXY = Path('scripts/uc001_granite_acquisition_proxy/proxy.py').resolve()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.mark.parametrize('event', [
    'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr',
    'socket.connect', 'socket.connect_ex', 'socket.sendto', 'socket.sendmsg',
    'subprocess.Popen', 'os.system', 'ctypes.dlopen',
])
def test_outbound_dns_process_or_native_attempt_fails_before_operation(tmp_path, event):
    path = tmp_path / 'guard.jsonl'
    value = guard.NetworkGuard(path)
    try:
        with pytest.raises(guard.GuardFailure):
            value(event, ())
        assert rows(path)[-1]['event'] == 'forbidden_attempt'
        assert rows(path)[-1]['forbidden_attempts'] == 1
        with pytest.raises(guard.GuardFailure):
            value.complete()
    finally:
        value.close()


def test_only_one_ipv4_loopback_ephemeral_listener_is_allowed(tmp_path):
    value = guard.NetworkGuard(tmp_path / 'guard.jsonl')
    sock = SimpleNamespace(family=2, type=1)
    try:
        value('socket.bind', (sock, ('127.0.0.1', 0)))
        with pytest.raises(guard.GuardFailure):
            value('socket.bind', (sock, ('127.0.0.1', 0)))
    finally:
        value.close()


@pytest.mark.parametrize('address', [('0.0.0.0', 0), ('::1', 0), ('127.0.0.1', 443)])
def test_other_bind_is_failure(tmp_path, address):
    value = guard.NetworkGuard(tmp_path / 'guard.jsonl')
    try:
        with pytest.raises(guard.GuardFailure):
            value('socket.bind', (SimpleNamespace(family=2, type=1), address))
    finally:
        value.close()


def test_ledger_write_failure_is_not_recorded_as_zero_pass(tmp_path, monkeypatch):
    value = guard.NetworkGuard(tmp_path / 'guard.jsonl')
    monkeypatch.setattr(guard.os, 'write', lambda *_: (_ for _ in ()).throw(OSError('injected')))
    try:
        with pytest.raises(guard.GuardFailure, match='guard_ledger_write_failed'):
            value('socket.connect', ())
        assert value.failed
    finally:
        value.close()


def test_exact_accepted_proxy_buffer_executes_only_after_guard_install(tmp_path):
    installed = []
    path = tmp_path / 'guard.jsonl'

    def execute(code, namespace):
        assert installed and namespace['__name__'] == '__main__'
        assert namespace['__file__'] == str(PROXY)
        assert code.co_filename == str(PROXY)
        installed[0]('socket.bind', (SimpleNamespace(family=2, type=1), ('127.0.0.1', 0)))

    guard.run_guarded(PROXY, path, ['--ledger', str(tmp_path / 'meter.jsonl')],
                      install=installed.append, execute=execute)
    result = guard.validate_guard_log(path, expected_pid=guard.os.getpid())
    assert result['outbound_attempts'] == 0
    assert result['loopback_listener_binds'] == 1
    assert [row['event'] for row in rows(path)] == ['guard_started', 'listener_bound', 'guard_completed']


def test_changed_proxy_is_rejected_before_guard_or_execution(tmp_path):
    path = tmp_path / 'proxy.py'
    path.write_bytes(PROXY.read_bytes() + b'\n')
    invoked = []
    with pytest.raises(guard.GuardFailure, match='accepted_proxy_hash_differs'):
        guard.run_guarded(path, tmp_path / 'guard.jsonl', [],
                          install=invoked.append, execute=lambda *_: invoked.append('executed'))
    assert invoked == []
    assert hashlib.sha256(PROXY.read_bytes()).hexdigest() == guard.PROXY_SHA256


@pytest.mark.parametrize('kind', ['missing_terminal', 'attempt', 'wrong_pid', 'clock', 'extra_event'])
def test_guard_evidence_unknown_or_changed_is_failure(tmp_path, kind):
    path = tmp_path / 'guard.jsonl'
    value = guard.NetworkGuard(path)
    value('socket.bind', (SimpleNamespace(family=2, type=1), ('127.0.0.1', 0)))
    value.complete()
    value.close()
    data = rows(path)
    if kind == 'missing_terminal':
        data.pop()
    elif kind == 'attempt':
        data[1]['forbidden_attempts'] = 1
    elif kind == 'wrong_pid':
        data[1]['pid'] += 1
    elif kind == 'clock':
        data[1]['monotonic_ns'] = -1
    else:
        data.append(dict(data[-1], event='unknown'))
    path.write_text(''.join(json.dumps(row) + '\n' for row in data))
    with pytest.raises(guard.GuardFailure):
        guard.validate_guard_log(path, expected_pid=guard.os.getpid())
