import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

EXP = Path(__file__).resolve().parent
REPO = EXP.parents[2]
RUN = REPO / 'build/lingua-b-20261015'
CAP = 1024 ** 3


def write(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def append(path, value):
    with path.open('a') as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def check_limits(now, deadline, rss, scratch):
    if now >= deadline:
        raise RuntimeError('deadline expired')
    if rss > CAP:
        raise RuntimeError('owned RSS cap exceeded')
    if scratch > CAP:
        raise RuntimeError('additional scratch cap exceeded')


def owned_identity(pid, ticks, observed):
    return bool(observed and observed['pid'] == pid and
                observed['start_ticks'] == ticks and observed['pgrp'] == pid)


def required_clear_correct(case, top):
    return top == case['required_clear_top1'] if 'required_clear_top1' in case else None


def process(pid):
    try:
        tail = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
        status = Path(f'/proc/{pid}/status').read_text().splitlines()
        mem = {line.split(':')[0]: int(line.split()[1]) * 1024
               for line in status if line.startswith(('VmRSS:', 'VmHWM:'))}
        threads = next((int(line.split()[1]) for line in status if line.startswith('Threads:')), 0)
        return {'pid': pid, 'ppid': int(tail[1]), 'pgrp': int(tail[2]), 'os_threads': threads,
                'start_ticks': int(tail[19]), 'rss': mem.get('VmRSS', 0),
                'hwm': mem.get('VmHWM', 0)}
    except (FileNotFoundError, ProcessLookupError):
        return None


def scratch():
    logical = allocated = 0
    for root in [RUN, EXP]:
        for p in root.rglob('*'):
            try:
                st = p.lstat()
                if not p.is_dir():
                    logical += st.st_size
                allocated += st.st_blocks * 512
            except FileNotFoundError:
                pass
    return {'logical_bytes': logical, 'allocated_bytes': allocated}


def preflight():
    mem = {line.split(':')[0]: int(line.split()[1]) * 1024
           for line in Path('/proc/meminfo').read_text().splitlines()
           if line.startswith(('MemAvailable:', 'MemTotal:'))}
    cg = {}
    for name in ['memory.max', 'memory.current', 'memory.events', 'memory.pressure']:
        p = Path('/sys/fs/cgroup') / name
        if p.exists():
            cg[name] = p.read_text().strip()
    headroom = mem['MemAvailable']
    if cg.get('memory.max', 'max') != 'max':
        headroom = min(headroom, int(cg['memory.max']) - int(cg['memory.current']))
    disk = os.statvfs(RUN)
    free = disk.f_bavail * disk.f_frsize
    sample = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'memory': mem, 'visible_cgroup': cg, 'effective_headroom_bytes': headroom,
              'free_disk_bytes': free, 'minimum_headroom_bytes': CAP + CAP // 2,
              'cpu_affinity': sorted(os.sched_getaffinity(0))}
    write(RUN / 'acquisition-preflight.json', sample)
    if headroom < CAP + CAP // 2 or free < CAP + CAP // 2:
        raise RuntimeError('preflight headroom below recorded threshold')


def main():
    attempt = json.loads((RUN / 'attempt.json').read_text())
    deadline = attempt['deadline_monotonic']
    marker = RUN / 'execution-started.json'
    if marker.exists():
        raise RuntimeError('existing execution marker; no retry permitted')
    freeze_path = EXP / 'freeze.json'
    freeze = json.loads(freeze_path.read_text())
    for name, digest in freeze['files'].items():
        if hashlib.sha256((EXP / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError('freeze mismatch: ' + name)
    freeze_sha = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    write(marker, {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'freeze_sha256': freeze_sha, 'pid': os.getpid(),
                   'deadline_monotonic': deadline})
    preflight()
    env = dict(os.environ)
    env.update({k: '2' for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                               'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'RAYON_NUM_THREADS']})
    env.update({'PYTHONDONTWRITEBYTECODE': '1', 'PIP_CONFIG_FILE': '/dev/null',
                'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'TMPDIR': str(RUN / 'tmp'),
                'LINGUA_FREEZE_SHA256': freeze_sha})
    (RUN / 'tmp').mkdir(exist_ok=False)
    cpus = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, cpus)
    venv = RUN / 'venv'
    phases = [
        ('acquire', [sys.executable, '-B', str(EXP / 'acquire.py')]),
        ('venv', [sys.executable, '-B', '-m', 'venv', '--without-pip', '--symlinks', str(venv)]),
        ('install', [sys.executable, '-B', '-m', 'pip', '--isolated', '--python', str(venv),
                     'install', '--no-index', '--find-links', str(RUN), '--no-deps',
                     '--no-cache-dir', '--no-compile', '--require-hashes', '-r', str(EXP / 'requirements.lock')]),
        ('detector', [str(venv / 'bin/python'), '-B', str(EXP / 'worker.py')]),
    ]
    peak_rss = peak_hwm_sum = peak_scratch = 0
    child = None
    started = time.monotonic()
    failure = None
    exits = []
    try:
        for name, command in phases:
            check_limits(time.monotonic(), deadline, peak_rss, peak_scratch)
            out = (RUN / (name + '.stdout.log')).open('xb')
            err = (RUN / (name + '.stderr.log')).open('xb')
            child = subprocess.Popen(command, cwd=REPO, env=env, stdout=out,
                                     stderr=err, start_new_session=True)
            identity = process(child.pid)
            ticks = identity['start_ticks'] if identity else None
            append(RUN / 'processes.jsonl', {'phase': name, 'command': command,
                                           'identity': identity, 'start_monotonic': time.monotonic()})
            last_scratch = 0
            disk = scratch()
            while True:
                now = time.monotonic()
                all_ps = [process(int(p.name)) for p in Path('/proc').iterdir() if p.name.isdigit()]
                owned = [p for p in all_ps if p and (p['pid'] == os.getpid() or p['pgrp'] == child.pid)]
                rss = sum(p['rss'] for p in owned)
                hwm_sum = sum(p['hwm'] for p in owned)
                peak_rss = max(peak_rss, rss)
                peak_hwm_sum = max(peak_hwm_sum, hwm_sum)
                if now - last_scratch >= .25:
                    disk = scratch()
                    last_scratch = now
                size = max(disk.values())
                peak_scratch = max(peak_scratch, size)
                append(RUN / 'resources.jsonl', {'monotonic': now, 'phase': name,
                        'owned': owned, 'rss_bytes': rss, 'hwm_sum_bytes': hwm_sum, 'scratch': disk})
                check_limits(now, deadline, max(rss, hwm_sum), size)
                if child.poll() is not None:
                    break
                time.sleep(.05)
            exits.append({'phase': name, 'exit_code': child.returncode,
                          'end_monotonic': time.monotonic()})
            write(RUN / 'phase-exits.json', exits)
            out.close()
            err.close()
            if child.returncode != 0:
                raise RuntimeError(name + ' operational failure; no retry')
            child = None
    except BaseException as exc:
        failure = str(exc)
        if child and child.poll() is None:
            observed = process(child.pid)
            if owned_identity(child.pid, ticks, observed):
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    if owned_identity(child.pid, ticks, process(child.pid)):
                        os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=2)
            else:
                failure += '; live ownership check failed, no signal sent'
        append(RUN / 'failures.jsonl', {'failure': failure, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    summary = {'status': 'operational_failure' if failure else 'completed_fixed_sample',
               'failure': failure, 'freeze_sha256': freeze_sha,
               'deadline_utc': attempt['deadline_utc'], 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'elapsed_from_authorization_window_seconds': time.monotonic() - attempt['started_monotonic'],
               'supervised_seconds': time.monotonic() - started, 'peak_owned_rss_bytes': peak_rss,
               'peak_owned_hwm_sum_bytes': peak_hwm_sum, 'peak_scratch_bytes': peak_scratch,
               'final_scratch': scratch(), 'phase_exits': exits, 'cpu_affinity': cpus,
               'thread_limits': {k: env[k] for k in env if k.endswith('_NUM_THREADS')},
               'sampling': 'RSS every 50ms; scratch every 250ms; HWM sum is conservative, transient aggregate peaks may be missed.',
               'owned_child_alive': bool(child and child.poll() is None)}
    write(RUN / 'closeout.json', summary)
    print(json.dumps(summary, indent=2))
    return 1 if failure else 0


if __name__ == '__main__':
    sys.exit(main())
