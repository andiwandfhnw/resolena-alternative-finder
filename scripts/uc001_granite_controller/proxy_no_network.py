"""Diagnostic-only launcher: exact accepted proxy, one listener, no outbound calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone


PROXY_SHA256 = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
BLOCKED = {'socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyname_ex',
           'socket.gethostbyaddr', 'socket.getnameinfo', 'socket.connect',
           'socket.connect_ex', 'socket.sendto', 'socket.sendmsg', 'subprocess.Popen',
           'os.system', 'os.exec', 'os.posix_spawn', 'ctypes.dlopen', 'ctypes.dlsym'}


class GuardFailure(RuntimeError):
    pass


class NetworkGuard:
    def __init__(self, path):
        self.fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.failed = False
        self.attempts = self.binds = 0
        try:
            self.record('guard_started')
        except BaseException:
            self.close()
            raise

    def record(self, event, **extra):
        if self.failed or self.fd is None:
            raise GuardFailure('guard_ledger_unknown_or_closed')
        row = dict(event=event, timestamp_utc=datetime.now(timezone.utc).isoformat(),
                   monotonic_ns=time.monotonic_ns(), pid=os.getpid(),
                   forbidden_attempts=self.attempts, loopback_binds=self.binds, **extra)
        data = (json.dumps(row, sort_keys=True) + '\n').encode('utf-8')
        try:
            while data:
                written = os.write(self.fd, data)
                if written <= 0:
                    raise OSError('short guard write')
                data = data[written:]
            os.fsync(self.fd)
        except BaseException as error:
            self.failed = True
            raise GuardFailure('guard_ledger_write_failed') from error

    def deny(self, event):
        self.attempts += 1
        self.record('forbidden_attempt', audit_event=event)
        raise GuardFailure('diagnostic_operation_forbidden:' + event)

    def __call__(self, event, args):
        if event in BLOCKED:
            self.deny(event)
        if event == 'socket.bind':
            if (self.binds or len(args) != 2 or args[1] != ('127.0.0.1', 0)
                    or getattr(args[0], 'family', None) != 2
                    or getattr(args[0], 'type', None) != 1):
                self.deny(event)
            self.binds += 1
            self.record('listener_bound')

    def complete(self):
        if self.failed or self.attempts or self.binds != 1:
            raise GuardFailure('guard_observations_incomplete_or_failed')
        self.record('guard_completed')

    def close(self):
        if self.fd is not None:
            fd, self.fd = self.fd, None
            os.close(fd)


def validate_guard_log(path, expected_pid):
    try:
        data = Path(path).read_bytes()
        if (not data.endswith(b'\n') or len(data) > 32768
                or type(expected_pid) is not int or not 0 < expected_pid <= 0xFFFFFFFF):
            raise ValueError('invalid_guard_size_or_pid')
        rows = [json.loads(line) for line in data.splitlines()]
        if [row['event'] for row in rows] != ['guard_started', 'listener_bound', 'guard_completed']:
            raise ValueError('guard_sequence_or_forbidden_attempt')
        last = -1
        for row, binds in zip(rows, (0, 1, 1)):
            stamp = row['monotonic_ns']
            if (type(stamp) is not int or stamp < last
                    or type(row['pid']) is not int or row['pid'] != expected_pid
                    or type(row['forbidden_attempts']) is not int or row['forbidden_attempts'] != 0
                    or type(row['loopback_binds']) is not int or row['loopback_binds'] != binds
                    or datetime.fromisoformat(row['timestamp_utc']).tzinfo is None):
                raise ValueError('guard_identity_or_observation_differs')
            last = stamp
        return dict(verified=True, interpreter_pid=expected_pid, outbound_attempts=0,
                    loopback_listener_binds=1, sha256=hashlib.sha256(data).hexdigest())
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise GuardFailure('guard_evidence_invalid:' + str(error)) from error


def run_guarded(proxy_path, log_path, argv, install=sys.addaudithook, execute=exec):
    proxy_path = Path(proxy_path).resolve()
    data = proxy_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PROXY_SHA256:
        raise GuardFailure('accepted_proxy_hash_differs')
    code = compile(data, str(proxy_path), 'exec')
    value = NetworkGuard(log_path)
    original_argv = sys.argv
    try:
        install(value)
        sys.argv = [str(proxy_path), *argv]
        execute(code, dict(__name__='__main__', __file__=str(proxy_path)))
        value.complete()
    finally:
        sys.argv = original_argv
        value.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proxy-helper', type=Path, required=True)
    parser.add_argument('--guard-log', type=Path, required=True)
    args, proxy_args = parser.parse_known_args()
    run_guarded(args.proxy_helper, args.guard_log, proxy_args)


if __name__ == '__main__':
    main()
