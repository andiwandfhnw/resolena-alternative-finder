import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ORIGINAL = HERE.parent / 'lingua_B_2026_10_15'
VERIFIER = HERE.parent / 'lingua_B_verifier_v1_0_1'
OLD_RUN = REPO / 'build/lingua-b-20261015'
LIMITS = json.loads((ORIGINAL / 'config.json').read_text())['limits']


def write(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    tmp.replace(path)


def append(path, value):
    with path.open('a') as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def validate_context(c, path):
    root = Path(c['run_dir']).resolve()
    if root != path.resolve().parent or not root.is_relative_to(REPO / 'build') or root == OLD_RUN or root.is_relative_to(OLD_RUN):
        raise RuntimeError('unsafe output path or closed attempt')
    if c['limits'] != LIMITS:
        raise RuntimeError('resource limits changed')
    if time.monotonic() >= c['deadline_monotonic'] or time.time() >= c['deadline_wall_unix']:
        raise RuntimeError('deadline expired')
    return c


def load_context():
    path = Path(sys.argv[sys.argv.index('--context')+1]).resolve()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != os.environ['LINGUA_CONTEXT_SHA256']:
        raise RuntimeError('context checksum mismatch')
    c = validate_context(json.loads(raw), path)
    if str(c['deadline_monotonic']) != os.environ['LINGUA_DEADLINE_MONOTONIC']:
        raise RuntimeError('deadline propagation mismatch')
    if json.loads(os.environ['LINGUA_LIMITS_JSON']) != c['limits']:
        raise RuntimeError('limits propagation mismatch')
    if c['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        raise RuntimeError('execution host changed')
    return c


def check_limits(now, deadline, rss, scratch):
    if now >= deadline: raise RuntimeError('deadline expired')
    if rss > LIMITS['owned_rss_bytes']: raise RuntimeError('owned RSS cap exceeded')
    if scratch > LIMITS['additional_scratch_bytes']: raise RuntimeError('scratch cap exceeded')


def deadline(c):
    check_limits(time.monotonic(), c['deadline_monotonic'], 0, 0)
    if time.time() >= c['deadline_wall_unix']: raise RuntimeError('wall deadline expired')


def worker_start(c, role):
    deadline(c)
    root = Path(c['run_dir'])
    marker = root / (role + '.started.json')
    with marker.open('x') as stream:
        json.dump({'role': role, 'pid': os.getpid(), 'ppid': os.getppid(),
            'deadline_monotonic': c['deadline_monotonic'], 'deadline_utc': c['deadline_utc'],
            'limits': c['limits'], 'freeze_sha256': c['freeze_sha256'],
            'context_sha256': os.environ['LINGUA_CONTEXT_SHA256'],
            'affinity': sorted(os.sched_getaffinity(0))}, stream, indent=2)


def required_clear_correct(case, top):
    return top == case['required_clear_top1'] if 'required_clear_top1' in case else None
