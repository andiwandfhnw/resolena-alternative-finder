import json
import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import pytest

from scripts.uc001_granite_acquisition_proxy.proxy import (
    BudgetLedger,
    LocalProxy,
    ProxyFailure,
)


DESTINATION = "github.com:443"


def wait_until(predicate):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    assert predicate(), "Synthetic proxy operation did not settle"


def recv_exact(connection, count):
    result = bytearray()
    while len(result) < count:
        chunk = connection.recv(count - len(result))
        assert chunk, "Tunnel closed before the expected synthetic bytes"
        result.extend(chunk)
    return bytes(result)


def connect_tunnel(proxy, destination=DESTINATION):
    connection = socket.create_connection(proxy.address, timeout=3)
    connection.settimeout(3)
    connection.sendall(
        f"CONNECT {destination} HTTP/1.1\r\nHost: {destination}\r\n\r\n".encode("ascii")
    )
    response = bytearray()
    while not response.endswith(b"\r\n\r\n"):
        chunk = connection.recv(1)
        if not chunk:
            break
        response.extend(chunk)
    return connection, bytes(response)


@contextmanager
def synthetic_proxy(tmp_path, allowance=100, read_size=3):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = BudgetLedger(ledger_path, allowance=allowance, prior_bytes=0)
    peers = []
    created = []
    lock = threading.Lock()

    def upstream_factory(host, port):
        assert (host, port) == ("github.com", 443)
        upstream, peer = socket.socketpair()
        peer.settimeout(3)
        with lock:
            created.append(upstream)
            peers.append(peer)
        return upstream

    proxy = LocalProxy(
        ledger,
        allow_destinations={("github.com", 443)},
        upstream_factory=upstream_factory,
        read_size=read_size,
    )
    clients = []
    try:
        with proxy:
            yield proxy, ledger, ledger_path, peers, created, clients
    finally:
        for connection in clients + peers:
            connection.close()
        proxy.close()


def test_exact_boundary_is_durably_counted(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = BudgetLedger(path, allowance=5, prior_bytes=0)
    ledger.charge("one", DESTINATION, b"ab")
    ledger.charge("one", DESTINATION, b"cde")
    assert ledger.total_bytes == 5
    records = [json.loads(line) for line in path.read_text().splitlines()]
    assert records[-1]["cumulative_bytes"] == 5
    assert all(record.get("cumulative_bytes", 0) <= 5 for record in records)


def test_one_byte_over_is_rejected_without_increasing_ledger(tmp_path):
    ledger = BudgetLedger(tmp_path / "ledger.jsonl", allowance=5, prior_bytes=0)
    ledger.charge("one", DESTINATION, b"abcde")
    with pytest.raises(ProxyFailure):
        ledger.charge("two", DESTINATION, b"f")
    assert ledger.total_bytes == 5


def test_prior_credit_cannot_reset_the_remaining_allowance(tmp_path):
    ledger = BudgetLedger(tmp_path / "ledger.jsonl", allowance=5, prior_bytes=4)
    ledger.charge("one", DESTINATION, b"x")
    assert ledger.total_bytes == 5
    with pytest.raises(ProxyFailure):
        ledger.charge("two", DESTINATION, b"y")


def test_failed_fsync_is_an_accounting_failure(tmp_path, monkeypatch):
    ledger = BudgetLedger(tmp_path / "ledger.jsonl", allowance=5, prior_bytes=0)

    def failed_fsync(_):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(os, "fsync", failed_fsync)
    with pytest.raises(ProxyFailure):
        ledger.charge("one", DESTINATION, b"x")


def test_concurrent_charges_share_one_budget(tmp_path):
    ledger = BudgetLedger(tmp_path / "ledger.jsonl", allowance=50, prior_bytes=0)

    def charge(index):
        try:
            ledger.charge(str(index), DESTINATION, b"x")
            return True
        except ProxyFailure:
            return False

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(charge, range(80)))
    assert sum(outcomes) == 50
    assert ledger.total_bytes == 50


def test_listener_is_loopback_only(tmp_path):
    with synthetic_proxy(tmp_path) as (proxy, *_):
        assert proxy.address[0] == "127.0.0.1"


def test_simultaneous_and_sequential_tunnels_share_cumulative_count(tmp_path):
    with synthetic_proxy(tmp_path) as (proxy, ledger, path, peers, _, clients):
        first, response = connect_tunnel(proxy)
        clients.append(first)
        assert response.startswith(b"HTTP/1.1 200 ")
        second, response = connect_tunnel(proxy)
        clients.append(second)
        assert response.startswith(b"HTTP/1.1 200 ")
        peers[0].sendall(b"abc")
        peers[1].sendall(b"defg")
        assert recv_exact(first, 3) == b"abc"
        assert recv_exact(second, 4) == b"defg"
        assert ledger.total_bytes == 7
        first.close()
        second.close()
        wait_until(lambda: proxy.active_tunnels == 0)
        third, response = connect_tunnel(proxy)
        clients.append(third)
        assert response.startswith(b"HTTP/1.1 200 ")
        peers[2].sendall(b"hij")
        assert recv_exact(third, 3) == b"hij"
        assert ledger.total_bytes == 10
        records = [json.loads(line) for line in path.read_text().splitlines()]
        charged = [record for record in records if record.get("tunnel_bytes", 0)]
        totals = {}
        for record in charged:
            assert record["destination"] == DESTINATION
            assert record["tunnel_id"]
            totals[record["tunnel_id"]] = record["tunnel_bytes"]
        assert sorted(totals.values()) == [3, 3, 4]


def test_multiple_socket_read_chunks_are_all_counted(tmp_path):
    with synthetic_proxy(tmp_path, read_size=2) as (proxy, ledger, path, peers, _, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        peers[0].sendall(b"abcdefghijk")
        assert recv_exact(client, 11) == b"abcdefghijk"
        assert ledger.total_bytes == 11
        charged = [json.loads(line) for line in path.read_text().splitlines()]
        assert charged[-1]["cumulative_bytes"] == 11


def test_upstream_byte_over_boundary_never_reaches_client(tmp_path):
    with synthetic_proxy(tmp_path, allowance=5, read_size=5) as (proxy, ledger, _, peers, _, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        peers[0].sendall(b"abcdef")
        wait_until(lambda: proxy.failure is not None)
        received = bytearray()
        while chunk := client.recv(10):
            received.extend(chunk)
        assert b"abcde".startswith(received)
        assert len(received) <= 5
        assert ledger.total_bytes == 5
        wait_until(lambda: proxy.active_tunnels == 0)


def test_exact_boundary_closes_fail_closed_without_resetting_counter(tmp_path):
    with synthetic_proxy(tmp_path, allowance=5, read_size=5) as (proxy, ledger, _, peers, _, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        peers[0].sendall(b"abcde")
        wait_until(lambda: proxy.failure is not None)
        assert ledger.total_bytes == 5
        wait_until(lambda: proxy.active_tunnels == 0)


def test_upstream_disconnect_closes_owned_tunnel_with_count_retained(tmp_path):
    with synthetic_proxy(tmp_path) as (proxy, ledger, _, peers, created, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        peers[0].sendall(b"abc")
        assert recv_exact(client, 3) == b"abc"
        peers[0].close()
        assert client.recv(1) == b""
        wait_until(lambda: proxy.active_tunnels == 0)
        assert created[0].fileno() == -1
        assert ledger.total_bytes == 3


def test_client_disconnect_closes_owned_upstream(tmp_path):
    with synthetic_proxy(tmp_path) as (proxy, ledger, _, peers, created, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        client.close()
        wait_until(lambda: proxy.active_tunnels == 0)
        assert peers[0].recv(1) == b""
        assert created[0].fileno() == -1
        assert ledger.total_bytes == 0


def test_ledger_write_failure_forwards_no_unrecorded_upstream_bytes(tmp_path, monkeypatch):
    with synthetic_proxy(tmp_path) as (proxy, ledger, _, peers, _, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")

        def failed_charge(*_):
            raise OSError("synthetic durable ledger failure")

        monkeypatch.setattr(ledger, "charge", failed_charge)
        peers[0].sendall(b"must not forward")
        wait_until(lambda: proxy.failure is not None)
        assert client.recv(1) == b""
        wait_until(lambda: proxy.active_tunnels == 0)


def test_unapproved_connect_destination_never_creates_upstream(tmp_path):
    with synthetic_proxy(tmp_path) as (proxy, ledger, _, _, created, clients):
        client, response = connect_tunnel(proxy, "example.invalid:443")
        clients.append(client)
        assert not response.startswith(b"HTTP/1.1 200 ")
        assert not created
        assert ledger.total_bytes == 0
        wait_until(lambda: proxy.failure is not None)


def test_active_tunnel_cleanup_is_idempotent_and_closes_both_ends(tmp_path):
    with synthetic_proxy(tmp_path) as (proxy, _, _, peers, created, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        proxy.close()
        proxy.close()
        assert proxy.active_tunnels == 0
        assert created[0].fileno() == -1
        assert client.recv(1) == b""
        assert peers[0].recv(1) == b""


def test_exhaustion_closes_all_active_tunnels(tmp_path):
    with synthetic_proxy(tmp_path, allowance=5) as (proxy, ledger, _, peers, created, clients):
        for _ in range(2):
            client, response = connect_tunnel(proxy)
            clients.append(client)
            assert response.startswith(b"HTTP/1.1 200 ")
        peers[0].sendall(b"abcdeEXTRA")
        wait_until(lambda: proxy.failure is not None and proxy.active_tunnels == 0)
        assert ledger.total_bytes == 5
        assert all(sock.fileno() == -1 for sock in created)
        assert clients[1].recv(1) == b""


def test_fsync_precedes_forwarding_and_failure_closes_all(tmp_path, monkeypatch):
    with synthetic_proxy(tmp_path) as (proxy, ledger, _, peers, created, clients):
        for _ in range(2):
            client, response = connect_tunnel(proxy)
            clients.append(client)
            assert response.startswith(b"HTTP/1.1 200 ")
        monkeypatch.setattr(os, "fsync", lambda *_: (_ for _ in ()).throw(OSError("disk failure")))
        peers[0].sendall(b"not forwarded")
        wait_until(lambda: proxy.failure is not None and proxy.active_tunnels == 0)
        assert ledger.failed is True
        assert all(sock.fileno() == -1 for sock in created)
        assert all(client.recv(1) == b"" for client in clients)


def test_existing_ledger_is_never_overwritten(tmp_path):
    path = tmp_path / "existing.jsonl"
    path.write_bytes(b"old partial evidence")
    with pytest.raises((ProxyFailure, FileExistsError)):
        BudgetLedger(path, allowance=10)
    assert path.read_bytes() == b"old partial evidence"


def test_deadline_closes_active_tunnels(tmp_path):
    ledger = BudgetLedger(tmp_path / "ledger.jsonl", 100)
    peers = []
    def upstream(host, port):
        a, b = socket.socketpair()
        peers.append(b)
        return a
    try:
        with LocalProxy(ledger, upstream_factory=upstream, deadline_seconds=0.15) as proxy:
            client, response = connect_tunnel(proxy)
            try:
                assert response.startswith(b"HTTP/1.1 200 ")
                wait_until(lambda: proxy.failure is not None)
                assert proxy.failure == "acquisition_deadline"
                wait_until(lambda: proxy.active_tunnels == 0)
                assert client.recv(1) == b""
            finally:
                client.close()
    finally:
        for peer in peers:
            peer.close()
        ledger.close()


def git_route_fixture(tmp_path, source):
    repo = tmp_path / "source-repository"
    (repo / ".git").mkdir(parents=True)
    (repo / ".git/config").write_text(
        '[core]\nrepositoryformatversion = 0\nfilemode = true\nbare = false\nlogallrefupdates = true\n'
        f'[remote "origin"]\nurl = {source}\nfetch = +refs/heads/*:refs/remotes/origin/*\n'
    )
    config = tmp_path / "empty.config"
    config.touch()
    hooks = tmp_path / "empty-hooks"
    hooks.mkdir()
    return repo, config, hooks


def test_git_spec_scrubs_bypasses_and_preserves_url_commit(tmp_path):
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    repo, config, hooks = git_route_fixture(tmp_path, module.SOURCE)
    hostile = dict(os.environ, NO_PROXY="*", no_proxy="*", HTTPS_PROXY="http://bypass.invalid",
                   GIT_CONFIG_COUNT="1", GIT_EXEC_PATH="untrusted", GIT_SSL_NO_VERIFY="1")
    argv, env = module.git_fetch_spec("git", repo, ("127.0.0.1", 12345), config, hooks, hostile)
    assert argv[-1] == "620d2225cc436ab0b001e3200e590e3b286ef9ab"
    assert "fetch" in argv and "origin" in argv
    assert "http.proxy=http://127.0.0.1:12345" in argv
    assert "remote.origin.proxy=http://127.0.0.1:12345" in argv
    assert "http.followRedirects=false" in argv
    assert "http.sslVerify=true" in argv
    assert not any(k.lower().endswith("_proxy") for k in env)
    assert "GIT_CONFIG_COUNT" not in env and "GIT_EXEC_PATH" not in env
    assert "GIT_SSL_NO_VERIFY" not in env
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_CONFIG_GLOBAL"] == str(config)
    assert module.SOURCE == "https://github.com/ggml-org/llama.cpp.git"


@pytest.mark.parametrize("extra", [
    '[http "https://github.com/"]\nproxy =\n',
    '[url "https://bypass.invalid/"]\ninsteadOf = https://github.com/\n',
    '[include]\npath = unreviewed.config\n',
    '[remote "origin"]\nproxy =\n',
])
def test_git_spec_rejects_config_bypasses(tmp_path, extra):
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    repo, config, hooks = git_route_fixture(tmp_path, module.SOURCE)
    with (repo / ".git/config").open("a") as out:
        out.write(extra)
    with pytest.raises(ProxyFailure):
        module.git_fetch_spec("git", repo, ("127.0.0.1", 12345), config, hooks, os.environ)


def test_real_git_fails_with_unavailable_proxy_without_direct_loopback_connection(tmp_path, monkeypatch):
    import subprocess
    import shutil
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    git = shutil.which("git")
    assert git, "Existing Git is required for this offline route check"
    direct = socket.socket()
    dead_proxy = socket.socket()
    try:
        direct.bind(("127.0.0.1", 0))
        direct.listen(1)
        direct.settimeout(0.15)
        dead_proxy.bind(("127.0.0.1", 0))  # bound, deliberately not listening
        fixture_url = f"https://127.0.0.1:{direct.getsockname()[1]}/fixture.git"
        monkeypatch.setattr(module, "SOURCE", fixture_url)
        repo, config, hooks = git_route_fixture(tmp_path, fixture_url)
        # Convert the synthetic config-only directory into a real, empty auxiliary repo.
        subprocess.run([git, "init", "--template=", str(repo)], check=True,
                       capture_output=True, timeout=5)
        argv, env = module.git_fetch_spec(git, repo, dead_proxy.getsockname(), config, hooks,
                                          dict(os.environ, NO_PROXY="*", no_proxy="*"))
        result = subprocess.run(argv, env=env, capture_output=True, timeout=5)
        assert result.returncode != 0
        assert str(dead_proxy.getsockname()[1]).encode() in result.stderr
        with pytest.raises(socket.timeout):
            direct.accept()
    finally:
        direct.close()
        dead_proxy.close()


def test_prior_unknown_cannot_be_loaded_as_zero(tmp_path):
    import hashlib
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    path = tmp_path / "prior.json"
    data = json.dumps(dict(bundle_id=module.BUNDLE, owner="owner", accounting_complete=False,
                           previously_charged_bytes=0)).encode()
    path.write_bytes(data)
    with pytest.raises(ProxyFailure):
        module.load_prior(path, hashlib.sha256(data).hexdigest())


def test_cli_does_not_reset_acquisition_clock_during_prior_validation(tmp_path, monkeypatch):
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    from datetime import datetime, timezone
    import sys
    started = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(sys, "argv", ["proxy.py", "--ledger", str(tmp_path / "ledger.jsonl"),
        "--prior-receipt", str(tmp_path / "prior.json"), "--prior-sha256", "unused",
        "--acquisition-started-utc", started])
    def delayed_prior(*_):
        time.sleep(0.08)
        return 0
    observed = {}
    class FakeProxy:
        def __init__(self, ledger, **kwargs):
            observed.update(kwargs)
            raise ProxyFailure("synthetic stop before socket creation")
    monkeypatch.setattr(module, "load_prior", delayed_prior)
    monkeypatch.setattr(module, "LocalProxy", FakeProxy)
    with pytest.raises(ProxyFailure):
        module.main()
    assert observed["deadline_seconds"] < 1799.95


@pytest.mark.parametrize('control,failed', [('CLOSE\n', False), ('', True), ('PASS\n', True)])
def test_controller_close_is_explicit_and_eof_is_failure(tmp_path, control, failed):
    import io
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    with synthetic_proxy(tmp_path) as (proxy, _, _, _, _, _):
        if failed:
            with pytest.raises(ProxyFailure):
                module.wait_for_controller(proxy, io.StringIO(control))
        else:
            module.wait_for_controller(proxy, io.StringIO(control))
            assert proxy.cleanup_verified
            assert proxy.failure is None


def test_fetch_spec_cli_emits_only_route_delta_no_environment_secrets(tmp_path, capsys, monkeypatch):
    import sys
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    repo, config, hooks = git_route_fixture(tmp_path, module.SOURCE)
    monkeypatch.setenv('SECRET_FIXTURE', 'must-not-be-output')
    monkeypatch.setattr(sys, 'argv', ['proxy.py', 'fetch-spec', '--git', 'git', '--repo', str(repo),
        '--proxy-port', '12345', '--empty-config', str(config), '--empty-hooks', str(hooks)])
    module.main()
    output = capsys.readouterr().out
    spec = json.loads(output)
    assert spec['argv'][-1] == module.COMMIT
    assert spec['environment_set']['GIT_CONFIG_GLOBAL'] == str(config)
    assert 'must-not-be-output' not in output


def test_tunnel_is_binary_transparent_in_both_directions(tmp_path):
    with synthetic_proxy(tmp_path, read_size=2) as (proxy, ledger, _, peers, _, clients):
        client, response = connect_tunnel(proxy)
        clients.append(client)
        assert response.startswith(b"HTTP/1.1 200 ")
        outbound = b"\x16\x03\x01\x00\xffsynthetic-tls-client"
        inbound = b"\x16\x03\x03\x00\xfesynthetic-tls-server"
        client.sendall(outbound)
        assert recv_exact(peers[0], len(outbound)) == outbound
        peers[0].sendall(inbound)
        assert recv_exact(client, len(inbound)) == inbound
        assert ledger.total_bytes == len(inbound)


def test_proxy_cli_records_controlled_close_without_claiming_acquisition_success(tmp_path):
    import hashlib
    import subprocess
    import sys
    from pathlib import Path
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    from datetime import datetime, timezone
    prior = tmp_path / "prior.json"
    prior.write_text(json.dumps(dict(bundle_id=module.BUNDLE, owner="synthetic",
                                    accounting_complete=True, previously_charged_bytes=7)))
    ledger = tmp_path / "ledger.jsonl"
    result = subprocess.run([
        sys.executable, str(Path(module.__file__)), "--ledger", str(ledger),
        "--prior-receipt", str(prior), "--prior-sha256", hashlib.sha256(prior.read_bytes()).hexdigest(),
        "--acquisition-started-utc", datetime.now(timezone.utc).isoformat(),
    ], input=b"CLOSE\n", capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr
    ready, closed = [json.loads(line) for line in result.stdout.splitlines()]
    assert ready['proxy_url'].startswith('http://127.0.0.1:')
    assert ready['prior_bytes'] == closed['cumulative_bytes'] == 7
    assert closed['status'] == 'meter_closed_unqualified'
    assert closed['cleanup_verified'] is True
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert records[-1]['event'] == 'end'
    assert records[-1]['status'] == 'closed_unqualified'


def test_real_git_connect_uses_proxy_and_received_tls_alert_is_metered(tmp_path, monkeypatch):
    import subprocess
    import shutil
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    direct = socket.socket()
    peers = []
    try:
        direct.bind(('127.0.0.1', 0))
        direct.listen(1)
        direct.settimeout(0.1)
        host, port = direct.getsockname()
        fixture_url = f'https://{host}:{port}/fixture.git'
        monkeypatch.setattr(module, 'SOURCE', fixture_url)
        repo, config, hooks = git_route_fixture(tmp_path, fixture_url)
        git = shutil.which('git')
        subprocess.run([git, 'init', '--template=', str(repo)], check=True, capture_output=True, timeout=5)
        def upstream(_host, _port):
            assert (_host, _port) == (host, port)
            a, b = socket.socketpair()
            peers.append(b)
            b.sendall(b'\x15\x03\x03\x00\x02\x02\x28')  # synthetic TLS fatal alert
            return a
        ledger = BudgetLedger(tmp_path / 'ledger.jsonl', 100)
        try:
            with LocalProxy(ledger, allow_destinations={(host, port)}, upstream_factory=upstream) as proxy:
                argv, env = module.git_fetch_spec(git, repo, proxy.address, config, hooks,
                                                  dict(os.environ, NO_PROXY='*', no_proxy='*'))
                result = subprocess.run(argv, env=env, capture_output=True, timeout=5)
                assert result.returncode != 0
                assert peers
                assert ledger.total_bytes == 7
                with pytest.raises(socket.timeout):
                    direct.accept()
        finally:
            ledger.close()
    finally:
        direct.close()
        for peer in peers:
            peer.close()


def test_git_common_directory_cannot_redirect_validated_config(tmp_path):
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    repo, config, hooks = git_route_fixture(tmp_path, module.SOURCE)
    (repo / '.git/commondir').write_text('../other-git-directory')
    with pytest.raises(ProxyFailure):
        module.git_fetch_spec('git', repo, ('127.0.0.1', 12345), config, hooks, os.environ)


def test_git_directory_symlink_is_not_followed(tmp_path):
    from scripts.uc001_granite_acquisition_proxy import proxy as module
    repo, config, hooks = git_route_fixture(tmp_path, module.SOURCE)
    target = tmp_path / 'redirected-git'
    (repo / '.git').rename(target)
    (repo / '.git').symlink_to(target, target_is_directory=True)
    with pytest.raises(ProxyFailure):
        module.git_fetch_spec('git', repo, ('127.0.0.1', 12345), config, hooks, os.environ)
