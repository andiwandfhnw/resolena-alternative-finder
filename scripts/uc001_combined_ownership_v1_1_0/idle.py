"""Model-free worker; validates the real combined ownership proof, then waits for job closure."""

import json
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from scripts.uc001_combined_ownership_v1_1_0.harness_checks import (
    verify_python_ownership, windows_system_directory, stop_record,
)


def write_atomic(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    os.replace(temporary, path)


def run(ready, result):
    write_atomic(ready, {'pid': os.getpid(), 'parent_pid': os.getppid()})
    try:
        proof = json.loads(sys.stdin.readline(32769))
        # The expected server executable comes from native Windows, never from the proof.
        import ntpath
        verify_python_ownership(proof, server_executable=ntpath.join(
            windows_system_directory(), r'WindowsPowerShell\v1.0\powershell.exe'))
        status = {'outcome': 'python_combined_ownership_verified', 'validator': 'verify_python_ownership',
            'pid': os.getpid(), 'parent_pid': os.getppid(), 'proof': proof}
    except Exception as error:
        status = {'outcome': 'failed', 'failure': stop_record(error)}
    write_atomic(result, status)
    sys.stdin.readline()  # Stay alive for a fresh native proof and held-handle cleanup.


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
