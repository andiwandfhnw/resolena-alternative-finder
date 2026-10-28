"""Opt-in, conservative CONNECT meter. No Git execution or TLS interception."""
import argparse
import configparser
import errno
import hashlib
import json
import os
from pathlib import Path
import selectors
import socket
import stat
import sys
import threading
import time
from datetime import datetime, timezone

CEILING = 10 * 1024**3
SOURCE = "https://github.com/ggml-org/llama.cpp.git"
COMMIT = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
BUNDLE = "9a4acb903c834737809b2648c358da9f2d91b116471966fb7b691847a069f4b4"


def utc():
    return datetime.now(timezone.utc).isoformat()


class ProxyFailure(RuntimeError):
    pass


class BudgetLedger:
    def __init__(self, path, allowance, prior_bytes=0, prior_receipt_sha256=None):
        if (type(allowance) is not int or type(prior_bytes) is not int
                or not 0 <= prior_bytes < allowance <= CEILING):
            raise ProxyFailure("invalid_or_exhausted_budget")
        self.path = Path(path)
        self.allowance = allowance
        self.total_bytes = prior_bytes
        self.prior_bytes = prior_bytes
        self.failed = False
        self.totals = {}
        self.lock = threading.RLock()
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                          | getattr(os, "O_BINARY", 0), 0o600)
        try:
            self.record("start", prior_bytes=prior_bytes,
                        prior_receipt_sha256=prior_receipt_sha256,
                        allowance_bytes=allowance)
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise

    def record(self, event, tunnel_id=None, destination=None, **extra):
        with self.lock:
            if self.failed or self.fd is None:
                raise ProxyFailure("ledger_unknown_or_closed")
            value = dict(event=event, timestamp_utc=utc(),
                         monotonic_ns=time.monotonic_ns(), tunnel_id=tunnel_id,
                         destination=destination,
                         tunnel_bytes=self.totals.get(tunnel_id, 0),
                         cumulative_bytes=self.total_bytes, **extra)
            data = (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")
            try:
                while data:
                    written = os.write(self.fd, data)
                    if written <= 0:
                        raise OSError("short ledger write")
                    data = data[written:]
                os.fsync(self.fd)
            except BaseException as error:
                self.failed = True
                raise ProxyFailure("ledger_write_failed_accounting_unknown") from error

    def charge(self, tunnel_id, destination, chunk):
        with self.lock:
            if self.failed or self.fd is None:
                raise ProxyFailure("ledger_unknown_or_closed")
            if len(chunk) > self.allowance - self.total_bytes:
                raise ProxyFailure("allowance_exceeded")
            self.total_bytes += len(chunk)
            self.totals[tunnel_id] = self.totals.get(tunnel_id, 0) + len(chunk)
            self.record("debit", tunnel_id, destination, bytes_read=len(chunk))

    def close(self):
        with self.lock:
            if self.fd is not None:
                os.close(self.fd)
                self.fd = None


class LocalProxy:
    def __init__(self, ledger, allow_destinations=None, upstream_factory=None,
                 read_size=65536, deadline_seconds=1800):
        self.ledger = ledger
        self.allowed = allow_destinations or {("github.com", 443)}
        self.factory = upstream_factory
        self.read_size = read_size
        if not 1 <= read_size <= 65536 or not 0 < deadline_seconds <= 1800:
            raise ProxyFailure("invalid_proxy_bounds")
        self.deadline = time.monotonic() + deadline_seconds
        self.failure = None
        self.cleanup_verified = False
        self.selector = selectors.SelectSelector()
        self.tunnels = {}
        self.stop = threading.Event()
        self.thread = None
        self.address = None
        self.listener = None
        self.sequence = 0
        self.owned_sockets = []

    @property
    def active_tunnels(self):
        return len(self.tunnels)

    def __enter__(self):
        try:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.owned_sockets.append(self.listener)
            if os.name == "nt":
                self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            self.listener.bind(("127.0.0.1", 0))
            self.listener.listen(8)
            self.listener.setblocking(False)
            self.address = self.listener.getsockname()
            self.selector.register(self.listener, selectors.EVENT_READ, (None, "listener"))
            self.ledger.record("listening", address=list(self.address), pid=os.getpid())
            self.thread = threading.Thread(target=self._run, name="owned-connect-meter")
            self.thread.start()
            return self
        except BaseException:
            self._cleanup()
            raise

    def __exit__(self, *_):
        self.close()

    def _fail(self, reason):
        if self.failure is None:
            self.failure = str(reason)
        self.stop.set()

    def _watch(self, sock, tunnel, side, reading=True):
        events = selectors.EVENT_READ if reading else 0
        if tunnel["out"][side]:
            events |= selectors.EVENT_WRITE
        try:
            self.selector.unregister(sock)
        except KeyError:
            pass
        if events:
            self.selector.register(sock, events, (tunnel, side))

    def _upstream(self, host, port, tunnel):
        if self.factory:
            upstream = self.factory(host, port)
            tunnel["upstream"] = upstream
            self.owned_sockets.append(upstream)
            upstream.setblocking(False)
            tunnel["connecting"] = False
            return
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        if not addresses:
            raise ProxyFailure("destination_resolution_failed")
        family, kind, protocol, _, endpoint = addresses[0]
        upstream = socket.socket(family, kind, protocol)
        tunnel["upstream"] = upstream
        self.owned_sockets.append(upstream)
        upstream.setblocking(False)
        result = upstream.connect_ex(endpoint)
        pending = {0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY,
                   getattr(errno, "WSAEWOULDBLOCK", 10035)}
        if result not in pending:
            raise ProxyFailure("upstream_connect_failed")
        tunnel["connecting"] = result != 0

    def _accept(self):
        client, _ = self.listener.accept()
        self.owned_sockets.append(client)
        client.setblocking(False)
        if len(self.tunnels) >= 8:
            client.close()
            raise ProxyFailure("tunnel_capacity_exceeded")
        self.sequence += 1
        key = str(self.sequence)
        tunnel = dict(id=key, client=client, upstream=None, header=bytearray(),
                      destination=None, connected=False, connecting=False,
                      out={"client": bytearray(), "upstream": bytearray()},
                      upstream_eof=False, created=time.monotonic())
        self.tunnels[key] = tunnel
        self._watch(client, tunnel, "client")

    def _handshake(self, tunnel):
        chunk = tunnel["client"].recv(4096 - len(tunnel["header"]))
        if not chunk:
            self._end(tunnel, "client_eof_before_connect")
            return
        tunnel["header"].extend(chunk)
        if b"\r\n\r\n" not in tunnel["header"]:
            if len(tunnel["header"]) >= 4096:
                raise ProxyFailure("connect_header_too_large")
            return
        header, tail = bytes(tunnel["header"]).split(b"\r\n\r\n", 1)
        lines = header.decode("ascii").split("\r\n")
        parts = lines[0].split(" ")
        if len(parts) != 3 or parts[0] != "CONNECT" or parts[2] != "HTTP/1.1" or tail:
            raise ProxyFailure("invalid_connect_request")
        destination = parts[1].lower()
        if destination.count(":") != 1:
            raise ProxyFailure("unapproved_connect_destination")
        host, port = destination.split(":")
        if not port.isascii() or not port.isdecimal() or (host, int(port)) not in self.allowed:
            raise ProxyFailure("unapproved_connect_destination")
        for line in lines[1:]:
            name, separator, value = line.partition(":")
            if not separator or name.lower() not in {"host", "user-agent", "proxy-connection"}:
                raise ProxyFailure("unexpected_connect_header")
            if name.lower() == "host" and value.strip().lower() != destination:
                raise ProxyFailure("connect_host_mismatch")
        tunnel["destination"] = destination
        self.ledger.record("tunnel_start", tunnel["id"], destination)
        self._upstream(host, int(port), tunnel)
        tunnel["connected"] = True
        if tunnel["connecting"]:
            self.selector.register(tunnel["upstream"], selectors.EVENT_WRITE, (tunnel, "upstream"))
        else:
            self._connected(tunnel)

    def _connected(self, tunnel):
        tunnel["out"]["client"].extend(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self._watch(tunnel["client"], tunnel, "client")
        self._watch(tunnel["upstream"], tunnel, "upstream")

    def _end(self, tunnel, reason):
        errors = []
        for side in ("client", "upstream"):
            sock = tunnel[side]
            if sock is not None:
                try:
                    self.selector.unregister(sock)
                except KeyError:
                    pass
                except BaseException as error:
                    errors.append(str(error))
                try:
                    sock.close()
                except BaseException as error:
                    errors.append(str(error))
        closed = all(tunnel[side] is None or tunnel[side].fileno() == -1
                     for side in ("client", "upstream"))
        if closed:
            self.tunnels.pop(tunnel["id"], None)
        if errors or not closed:
            raise ProxyFailure("tunnel_cleanup_not_verified:" + ";".join(errors))
        self.ledger.record("tunnel_end", tunnel["id"], tunnel["destination"], reason=reason)

    def _service(self, tunnel, side, mask):
        sock = tunnel[side]
        if side == "upstream" and tunnel["connecting"]:
            if sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR):
                raise ProxyFailure("upstream_connect_failed")
            tunnel["connecting"] = False
            self._connected(tunnel)
            return
        if not tunnel["connected"]:
            self._handshake(tunnel)
            return
        if mask & selectors.EVENT_WRITE:
            pending = tunnel["out"][side]
            if pending:
                sent = sock.send(pending)
                if sent <= 0:
                    raise ProxyFailure("socket_write_failed")
                del pending[:sent]
            if tunnel["upstream_eof"] and not tunnel["out"]["client"]:
                self._end(tunnel, "upstream_eof")
                return
        if mask & selectors.EVENT_READ:
            other = "client" if side == "upstream" else "upstream"
            if not tunnel["out"][other]:
                size = self.read_size
                if side == "upstream":
                    size = min(size, self.ledger.allowance - self.ledger.total_bytes)
                    if size <= 0:
                        raise ProxyFailure("allowance_exhausted")
                chunk = sock.recv(size)
                if not chunk:
                    if side == "client":
                        self._end(tunnel, "client_eof")
                        return
                    tunnel["upstream_eof"] = True
                    if not tunnel["out"]["client"]:
                        self._end(tunnel, "upstream_eof")
                        return
                else:
                    if side == "upstream":
                        self.ledger.charge(tunnel["id"], tunnel["destination"], chunk)
                        if self.ledger.total_bytes == self.ledger.allowance:
                            raise ProxyFailure("allowance_exhausted")
                    tunnel["out"][other].extend(chunk)
        self._watch(tunnel["client"], tunnel, "client", not tunnel["out"]["upstream"])
        self._watch(tunnel["upstream"], tunnel, "upstream",
                    not tunnel["upstream_eof"] and not tunnel["out"]["client"])

    def _run(self):
        try:
            while not self.stop.is_set():
                if time.monotonic() >= self.deadline:
                    raise ProxyFailure("acquisition_deadline")
                for key, mask in self.selector.select(0.05):
                    if self.stop.is_set():
                        break
                    tunnel, side = key.data
                    try:
                        if side == "listener":
                            self._accept()
                        elif tunnel["id"] in self.tunnels:
                            self._service(tunnel, side, mask)
                    except BlockingIOError:
                        continue
                if any((not t["connected"] or t["connecting"])
                       and time.monotonic() - t["created"] > 10 for t in self.tunnels.values()):
                    raise ProxyFailure("connect_handshake_timeout")
        except BaseException as error:
            self._fail(str(error))
        finally:
            self._cleanup()

    def _cleanup(self):
        for tunnel in list(self.tunnels.values()):
            try:
                self._end(tunnel, self.failure or "owner_close")
            except BaseException as error:
                self._fail(str(error))
        if self.listener is not None:
            try:
                self.selector.unregister(self.listener)
            except KeyError:
                pass
            self.listener.close()
        self.selector.close()
        self.cleanup_verified = not self.tunnels and all(s.fileno() == -1 for s in self.owned_sockets)
        if not self.cleanup_verified:
            self._fail("socket_cleanup_not_verified")
        try:
            self.ledger.record("end", reason=self.failure or "owner_close",
                               status="failure" if self.failure else "closed_unqualified",
                               sockets_closed=self.cleanup_verified)
        except BaseException as error:
            self._fail(str(error))

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(5)
            if self.thread.is_alive():
                self._fail("cleanup_not_verified")
                raise ProxyFailure("cleanup_not_verified")


def git_fetch_spec(git, repo, proxy_address, empty_config, empty_hooks, environ):
    """Return a child-only command/environment; never execute it."""
    repo, empty_config, empty_hooks = map(Path, (repo, empty_config, empty_hooks))
    if not empty_config.is_file() or empty_config.read_bytes() or not empty_hooks.is_dir() or any(empty_hooks.iterdir()):
        raise ProxyFailure("private_empty_config_and_hooks_required")
    config = configparser.RawConfigParser(strict=True, interpolation=None)
    try:
        git_dir = repo / ".git"
        config_path = git_dir / "config"
        for path in (git_dir, config_path):
            attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
            if path.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                raise ValueError("redirected Git configuration")
        if not git_dir.is_dir() or (git_dir / "commondir").exists():
            raise ValueError("common or nonordinary Git directory")
        config.read_string(config_path.read_text(encoding="utf-8"))
        if set(config.sections()) != {"core", 'remote "origin"'}:
            raise ValueError("unexpected sections")
        core = dict(config["core"])
        allowed = {"repositoryformatversion": {"0"}, "filemode": {"true", "false"},
                   "bare": {"false"}, "logallrefupdates": {"true"},
                   "symlinks": {"false", "true"}, "ignorecase": {"false", "true"}}
        if any(k not in allowed or v not in allowed[k] for k, v in core.items()):
            raise ValueError("unexpected core configuration")
        remote = dict(config['remote "origin"'])
        if remote != {"url": SOURCE, "fetch": "+refs/heads/*:refs/remotes/origin/*"}:
            raise ValueError("origin differs")
        if (repo / ".git" / "config.worktree").exists():
            raise ValueError("worktree configuration")
    except (OSError, ValueError, configparser.Error) as error:
        raise ProxyFailure("unreviewed_repository_configuration") from error
    host, port = proxy_address
    if host != "127.0.0.1" or type(port) is not int or not 1 <= port <= 65535:
        raise ProxyFailure("invalid_loopback_proxy")
    env = {k: v for k, v in environ.items() if not k.upper().startswith("GIT_")
           and not k.lower().endswith("_proxy") and k.upper() not in {"SSH_ASKPASS", "CURL_HOME"}}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(empty_config),
               GIT_CONFIG_SYSTEM=str(empty_config), GIT_TERMINAL_PROMPT="0",
               GIT_LFS_SKIP_SMUDGE="1")
    proxy = f"http://127.0.0.1:{port}"
    options = [f"http.proxy={proxy}", f"remote.origin.proxy={proxy}",
               "http.followRedirects=false", "protocol.allow=never", "protocol.https.allow=always",
               "credential.helper=", f"core.hooksPath={empty_hooks}", "http.sslVerify=true"]
    argv = [str(git), "-C", str(repo)]
    for option in options:
        argv += ["-c", option]
    argv += ["fetch", "--depth=1", "--no-tags", "--recurse-submodules=no", "origin", COMMIT]
    return argv, env


def load_prior(path, expected_sha256):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ProxyFailure("prior_receipt_hash_differs")
    receipt = json.loads(data)
    prior = receipt.get("previously_charged_bytes")
    if (receipt.get("bundle_id") != BUNDLE or not receipt.get("owner")
            or receipt.get("accounting_complete") is not True or type(prior) is not int
            or not 0 <= prior < CEILING):
        raise ProxyFailure("prior_accounting_unknown")
    return prior


def wait_for_controller(proxy, control):
    requested = threading.Event()

    def receive():
        try:
            if control.readline(16) == "CLOSE\n":
                requested.set()
            else:
                proxy._fail("controller_lost_or_invalid_command")
        except BaseException:
            proxy._fail("controller_channel_failed")

    threading.Thread(target=receive, name="private-controller-channel", daemon=True).start()
    while proxy.thread.is_alive() and not requested.wait(0.05):
        pass
    proxy.close()
    if proxy.failure or not proxy.cleanup_verified:
        raise ProxyFailure(proxy.failure or "cleanup_not_verified")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "fetch-spec":
        parser = argparse.ArgumentParser(description="Print the future isolated Git invocation only")
        parser.add_argument("--git", required=True)
        parser.add_argument("--repo", required=True)
        parser.add_argument("--proxy-port", type=int, required=True)
        parser.add_argument("--empty-config", required=True)
        parser.add_argument("--empty-hooks", required=True)
        args = parser.parse_args(sys.argv[2:])
        argv, env = git_fetch_spec(args.git, args.repo, ("127.0.0.1", args.proxy_port),
                                   args.empty_config, args.empty_hooks, os.environ)
        print(json.dumps(dict(argv=argv,
                              environment_remove=[k for k in os.environ if k not in env],
                              environment_set={k: v for k, v in env.items() if k.startswith("GIT_")})))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--prior-receipt", type=Path, required=True)
    parser.add_argument("--prior-sha256", required=True)
    parser.add_argument("--acquisition-started-utc", required=True)
    args = parser.parse_args()
    started = datetime.fromisoformat(args.acquisition_started_utc)
    if started.tzinfo is None:
        raise ProxyFailure("timezone_required")
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    if not 0 <= elapsed < 1800:
        raise ProxyFailure("invalid_or_expired_acquisition_clock")
    prior = load_prior(args.prior_receipt, args.prior_sha256)
    ledger = BudgetLedger(args.ledger, CEILING, prior, args.prior_sha256)
    try:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        if not 0 <= elapsed < 1800:
            raise ProxyFailure("acquisition_deadline")
        ledger.record("acquisition_clock", acquisition_started_utc=started.isoformat(),
                      remaining_seconds=1800-elapsed)
        with LocalProxy(ledger, deadline_seconds=1800-elapsed) as proxy:
            print(json.dumps(dict(proxy_url=f"http://127.0.0.1:{proxy.address[1]}",
                                  pid=os.getpid(), ledger=str(args.ledger),
                                  prior_bytes=prior, remaining_bytes=CEILING-prior)), flush=True)
            wait_for_controller(proxy, sys.stdin)
    except KeyboardInterrupt:
        raise ProxyFailure("owner_stop_not_acquisition_success") from None
    finally:
        ledger.close()
    print(json.dumps(dict(status="meter_closed_unqualified", cumulative_bytes=ledger.total_bytes,
                          cleanup_verified=proxy.cleanup_verified,
                          ledger_sha256=hashlib.sha256(args.ledger.read_bytes()).hexdigest())), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ProxyFailure, OSError, ValueError) as failure:
        print(json.dumps(dict(status="failure", reason=str(failure))), file=sys.stderr)
        raise SystemExit(1)
