"""Harmless opt-in Windows ownership self-test; no acquisition or build actions."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone


class StandinFailure(RuntimeError):
    pass


def _job_module():
    name = "granite_controller_standin_windows_job"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("windows_job.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _native_guard():
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8 or sys.version_info[:3] != (3, 12, 11):
        raise StandinFailure("Windows x64 / Python 3.12.11 required; no native operation performed")


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _write_new(path, value):
    with Path(path).open("xb") as stream:
        stream.write((json.dumps(value, sort_keys=True) + "\n").encode("utf-8"))
        stream.flush()
        os.fsync(stream.fileno())


class Journal:
    def __init__(self, path, clock):
        self.stream = Path(path).open("xb")
        self.clock = clock
        self.lock = threading.Lock()

    def record(self, event, **values):
        row = dict(event=event, timestamp_utc=_utc(), monotonic=self.clock(), **values)
        data = (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
        with self.lock:
            self.stream.write(data)
            self.stream.flush()
            os.fsync(self.stream.fileno())

    def close(self):
        self.stream.close()


def _identity(path, role):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if (value.get("role") != role or type(value.get("pid")) is not int or value["pid"] <= 0
            or type(value.get("creation_time_100ns")) is not int or value["creation_time_100ns"] <= 0
            or type(value.get("parent_pid")) is not int or value["parent_pid"] <= 0):
        raise StandinFailure("stand-in creation identity malformed")
    return value


def _public_identity(ref):
    return {key: ref[key] for key in ('role', 'kind', 'pid', 'creation_time_100ns', 'parent_pid')}


def _stable(api, ref):
    if (api.process_id(ref['handle']) != ref['pid']
            or api.creation_time(ref['handle']) != ref['creation_time_100ns']):
        raise StandinFailure('retained identity changed:' + ref['role'] + ':' + ref['kind'])


def _verify(api, job, ref, inside, journal):
    observed = dict(pid=api.process_id(ref['handle']),
                    creation_time_100ns=api.creation_time(ref['handle']),
                    parent_pid=api.parent_pid(ref['handle']),
                    in_private_job=api.in_job(ref['handle'], job.handle),
                    exit_code=api.exit_code(ref['handle']))
    journal.record('identity_observation', expected=_public_identity(ref), observed=observed)
    if (any(observed[key] != ref[key] for key in ('pid', 'creation_time_100ns', 'parent_pid'))
            or observed['in_private_job'] is not inside or observed['exit_code'] is not None):
        raise StandinFailure('native identity/parent/membership mismatch:' + ref['role'] + ':' + ref['kind'])
    _stable(api, ref)
    ref['verified'] = True


def _observe_scoped_edges(api, outside, timeout_seconds, journal, clock):
    parents = {ref['pid']: ref['kind'] for ref in outside}
    observation = dict(scoped_parents=[dict(parent_pid=ref['pid'], parent_kind=ref['kind'])
                                      for ref in outside],
                       observation_started_utc=_utc(), observation_started_monotonic=clock())
    try:
        edges = api.children_of(set(parents), timeout_seconds=timeout_seconds)
    except BaseException as error:
        journal.record('scoped_child_edges', **observation, observation_utc=_utc(),
                       observation_monotonic=clock(), status='failed', observed_edges=None,
                       error_type=type(error).__name__)
        raise
    observation.update(observation_utc=_utc(), observation_monotonic=clock())
    valid = type(edges) is set and all(
        type(edge) is tuple and len(edge) == 2
        and all(type(pid) is int and 0 < pid <= 0xFFFFFFFF for pid in edge)
        and edge[1] in parents for edge in edges)
    rows = None
    if valid:
        known = {ref['pid']: ref for ref in outside if ref.get('verified')}
        rows = []
        for child, parent in sorted(edges, key=lambda edge: (edge[1], edge[0])):
            ref = known.get(child)
            rows.append(dict(parent_pid=parent, child_pid=child, parent_kind=parents[parent],
                observation_utc=observation['observation_utc'],
                observation_monotonic=observation['observation_monotonic'],
                child_creation_time_100ns=ref['creation_time_100ns'] if ref else None,
                child_creation_source=('previously_verified_retained_identity' if ref
                                       else 'no_retained_verified_handle')))
    journal.record('scoped_child_edges', **observation,
                   status='observed' if valid else 'malformed', observed_edges=rows)
    if not valid:
        raise StandinFailure('unknown additional unrelated process')
    return edges


def run_ownership_selftest(output, python_exe=sys.executable, *, job_factory=None,
                           popen_factory=subprocess.Popen, clock=time.monotonic,
                           sleep=time.sleep, timeout_seconds=20):
    native = job_factory is None
    if native:
        _native_guard()
        if not Path(python_exe).is_absolute() or not Path(python_exe).is_file():
            raise StandinFailure('explicit existing Python executable required')
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 20:
        raise StandinFailure('ownership self-test deadline must be at most 20 seconds')
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started, started_utc = clock(), _utc()
    deadline = started + timeout_seconds
    journal = Journal(output / 'controller.jsonl', clock)
    job, unrelated, worker = None, None, None
    outside = []
    owned = []
    outside_shape_verified = False
    expired, watchdog_stop, terminated = threading.Event(), threading.Event(), threading.Event()
    terminate_lock = threading.Lock()
    watchdog = None
    result = dict(ownership_self_test_passed=False, windows_execution=native,
                  synthetic_injected=not native, started_utc=started_utc,
                  started_monotonic=started, timeout_seconds=timeout_seconds,
                  controller_pid=os.getpid(), controller_outside_private_job=False,
                  suspended_assignment_order_verified=False, owned_identities=[],
                  unrelated_identities=[], unrelated_exits=[], unrelated_survived=False,
                  unrelated_cleanup_verified=False,
                  cleanup=dict(verified=False, active_processes=None, owned_exits=[]),
                  failure_reason=None, cleanup_errors=[], resource_fit_established=False,
                  model_started=False, gpu_probe=False, acquisition_or_build=False,
                  helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

    def failure(reason):
        if result['failure_reason'] is None:
            result['failure_reason'] = str(reason)

    def record(event, **values):
        try:
            journal.record(event, **values)
        except BaseException as error:
            failure('journal failure:' + str(error))
            result['cleanup_errors'].append('journal:' + str(error))

    def stop_job():
        with terminate_lock:
            if job is not None and not terminated.is_set():
                terminated.set()
                job.terminate()

    def stop_outside():
        for ref in list(outside):
            if not ref.get('kill_allowed'):
                continue
            try:
                _stable(job.api, ref)
                if job.api.exit_code(ref['handle']) is None:
                    job.api.terminate_process(ref['handle'])
            except BaseException as error:
                failure(str(error))
                result['cleanup_errors'].append('outside termination:' + str(error))

    def check_deadline():
        if expired.is_set() or clock() >= deadline:
            raise StandinFailure('ownership self-test deadline')

    def outside_shape():
        nonlocal outside_shape_verified
        outside_shape_verified = False
        check_deadline()
        launcher, interpreter = outside
        edges = _observe_scoped_edges(job.api, outside, min(1.0, deadline-clock()), journal, clock)
        if edges != {(interpreter['pid'], launcher['pid'])}:
            raise StandinFailure('unknown additional unrelated process')
        for ref in outside:
            _stable(job.api, ref)
        outside_shape_verified = True

    def watchdog_main():
        if not watchdog_stop.wait(max(0, deadline-clock())):
            expired.set()
            try:
                stop_job()
            except BaseException as error:
                result['cleanup_errors'].append('deadline job termination:' + str(error))
            stop_outside()

    try:
        journal.record('selftest_start', native_windows=native, timeout_seconds=timeout_seconds)
        job = job_factory() if job_factory else _job_module().WindowsJob()
        result['controller_outside_private_job'] = not job.api.controller_in_job(job.handle)
        if not result['controller_outside_private_job']:
            raise StandinFailure('controller is inside its private job')
        watchdog = threading.Thread(target=watchdog_main, name='ownership-selftest-deadline', daemon=True)
        watchdog.start()
        check_deadline()
        argv = [str(python_exe), '-I', '-B', str(Path(__file__).resolve()),
                '--child-role', 'unrelated', '--events', str(output), '--safety-seconds', '30']
        with (output/'unrelated.stdout.log').open('xb') as stdout, (output/'unrelated.stderr.log').open('xb') as stderr:
            unrelated = popen_factory(argv, cwd=str(output), env=dict(os.environ), stdin=subprocess.DEVNULL,
                                      stdout=stdout, stderr=stderr, close_fds=True,
                                      creationflags=0x08000000 if native else 0)
        handle = job.api.open_process(unrelated.pid, can_terminate=True)
        launcher = dict(role='unrelated', kind='launcher', pid=unrelated.pid,
                        creation_time_100ns=job.api.creation_time(handle), parent_pid=os.getpid(),
                        handle=handle, verified=False, kill_allowed=True)
        outside.append(launcher)
        _verify(job.api, job, launcher, False, journal)
        while not (output/'unrelated.identity.json').is_file():
            check_deadline()
            _stable(job.api, launcher)
            if job.api.exit_code(handle) is not None:
                raise StandinFailure('unrelated launcher exited before interpreter evidence')
            sleep(0.01)
        manifest = _identity(output/'unrelated.identity.json', 'unrelated')
        journal.record('interpreter_manifest_observed', manifest=manifest)
        if manifest['pid'] == launcher['pid'] or manifest['parent_pid'] != launcher['pid']:
            raise StandinFailure('unrelated interpreter/launcher parent mismatch')
        handle = job.api.open_process(manifest['pid'], can_terminate=True)
        interpreter = dict(manifest, kind='interpreter', handle=handle, verified=False, kill_allowed=False)
        outside.append(interpreter)
        _verify(job.api, job, interpreter, False, journal)
        interpreter['kill_allowed'] = True
        _verify(job.api, job, launcher, False, journal)
        outside_shape()
        outside_shape_verified = True
        result['unrelated_identities'] = [_public_identity(ref) for ref in outside]
        journal.record('unrelated_pair_verified', identities=result['unrelated_identities'])

        argv[argv.index('--child-role')+1] = 'root'
        worker = job.launch(argv, str(output), dict(os.environ), output/'root.stdout.log', output/'root.stderr.log')
        events = job.drain_events()
        names = [row['event'] for row in events if row.get('pid') == worker.pid]
        required = ['worker_created_suspended', 'worker_assigned', 'worker_resumed']
        if [name for name in names if name in required] != required or not worker.assigned or not worker.resumed:
            raise StandinFailure('suspended assignment/resume order not verified')
        result['suspended_assignment_order_verified'] = True
        for row in events:
            journal.record('backend_event', value=row)
        roles = ('root', 'child', 'grandchild')
        files = [output/f'{role}.identity.json' for role in roles]
        files += [output/f'{role}.launcher.identity.json' for role in ('child', 'grandchild')]
        observed_members = set()
        while True:
            check_deadline()
            if job.process_exit(worker) is not None:
                raise StandinFailure('owned launcher exited prematurely')
            snapshot = job.snapshot()
            journal.record('owned_observation', snapshot=snapshot)
            members = {(row['pid'],row['creation_time_100ns']) for row in snapshot['owned']}
            observed_members |= members
            if snapshot.get('total_processes', 0) > 6 or len(observed_members) > 6:
                raise StandinFailure('unknown additional owned process')
            if all(path.is_file() for path in files):
                parent = os.getpid()
                for role in roles:
                    if role == 'root':
                        launch_manifest = dict(role=role, kind='launcher', pid=worker.pid,
                            creation_time_100ns=worker.creation_time_100ns, parent_pid=parent)
                    else:
                        launch_manifest = _identity(output/f'{role}.launcher.identity.json', role)
                    if launch_manifest['parent_pid'] != parent:
                        raise StandinFailure('owned launcher parent mismatch:' + role)
                    native_launcher = job.validate_pid(launch_manifest['pid'], launch_manifest['creation_time_100ns'])
                    ref = dict(launch_manifest, kind='launcher', handle=native_launcher.handle, verified=False)
                    _verify(job.api, job, ref, True, journal)
                    owned.append(ref)
                    interp_manifest = _identity(output/f'{role}.identity.json', role)
                    journal.record('interpreter_manifest_observed', manifest=interp_manifest)
                    if interp_manifest['pid'] == ref['pid'] or interp_manifest['parent_pid'] != ref['pid']:
                        raise StandinFailure('owned interpreter/launcher parent mismatch:' + role)
                    native_interp = job.validate_pid(interp_manifest['pid'], interp_manifest['creation_time_100ns'])
                    ref = dict(interp_manifest, kind='interpreter', handle=native_interp.handle, verified=False)
                    _verify(job.api, job, ref, True, journal)
                    owned.append(ref)
                    parent = ref['pid']
                expected = {(ref['pid'],ref['creation_time_100ns']) for ref in owned}
                snapshot = job.snapshot()
                journal.record('owned_observation_after_identity_verification', snapshot=snapshot)
                observed_members |= {(row['pid'],row['creation_time_100ns']) for row in snapshot['owned']}
                live = {(row['pid'],row['creation_time_100ns']) for row in snapshot['owned']
                        if row['in_job'] and row['exit_code'] is None}
                if (len(expected) != 6 or live != expected or observed_members != expected
                        or snapshot.get('active_processes') != 6 or snapshot.get('total_processes') != 6):
                    raise StandinFailure('owned launcher/interpreter tree is incomplete or additional')
                outside_shape()
                result['owned_identities'] = [_public_identity(ref) for ref in owned]
                journal.record('six_owned_identities_verified', identities=result['owned_identities'])
                break
            sleep(0.01)
    except BaseException as error:
        failure('controller_interruption' if isinstance(error, KeyboardInterrupt)
                else type(error).__name__ + ': ' + str(error))
    finally:
        try:
            stop_job()
            record('private_job_termination_requested')
        except BaseException as error:
            failure('private job termination failed')
            result['cleanup_errors'].append(str(error))
        if job is not None:
            try:
                result['cleanup'] = job.cleanup(timeout_seconds=max(0,min(5,deadline-clock())))
                expected_total = 6 if worker is not None else 0
                if result['cleanup'].get('total_processes') != expected_total:
                    result['cleanup']['verified'] = False
                    result['cleanup'].setdefault('errors', []).append('unexpected or unknown lifetime process count')
                    failure('unknown additional owned process at cleanup')
                expected = {(ref['pid'],ref['creation_time_100ns']) for ref in owned}
                exits = {(row['pid'],row['creation_time_100ns']) for row in result['cleanup'].get('owned_exits',[])
                         if type(row.get('exit_code')) is int}
                if (result['cleanup'].get('verified') is not True or result['cleanup'].get('active_processes') != 0
                        or not expected <= exits):
                    failure('owned job cleanup/identity exits unverified')
                record('private_job_cleanup', cleanup=result['cleanup'])
            except BaseException as error:
                failure('private job cleanup failed')
                result['cleanup_errors'].append(str(error))
            try:
                alive = len(outside)==2 and all(ref.get('verified') for ref in outside)
                if alive:
                    outside_shape()
                for ref in outside:
                    _stable(job.api,ref)
                    alive &= job.api.exit_code(ref['handle']) is None
                result['unrelated_survived'] = bool(alive)
                record('unrelated_pair_after_job_termination', survived=bool(alive),
                       identities=[_public_identity(ref) for ref in outside])
                if not alive:
                    failure('both unrelated identities did not survive private-job termination')
            except BaseException as error:
                failure(str(error))
            stop_outside()
            waiting = True
            while job is not None and waiting:
                waiting = False
                result['unrelated_exits'] = []
                for ref in outside:
                    code = None
                    try:
                        _stable(job.api,ref)
                        code = job.api.exit_code(ref['handle'])
                        waiting |= code is None
                    except BaseException as error:
                        failure(str(error))
                    result['unrelated_exits'].append(dict(_public_identity(ref),exit_code=code,
                                                          identity_verified=ref.get('verified',False)))
                if not waiting or clock() >= deadline:
                    break
                sleep(min(0.01,max(0,deadline-clock())))
            result['unrelated_cleanup_verified'] = (outside_shape_verified and len(outside)==2
                and all(row['identity_verified'] and type(row['exit_code']) is int for row in result['unrelated_exits']))
            if not result['unrelated_cleanup_verified']:
                failure('both unrelated identity-bound exits unverified')
            record('unrelated_cleanup', exits=result['unrelated_exits'],
                   verified=result['unrelated_cleanup_verified'])
        watchdog_stop.set()
        if watchdog is not None:
            watchdog.join(max(0,min(0.25,deadline-clock())))
            if watchdog.is_alive():
                failure('ownership watchdog exit unverified')
        if watchdog is None or not watchdog.is_alive():
            for ref in outside:
                try:
                    job.api.close_handle(ref['handle'])
                except BaseException as error:
                    failure('outside retained handle close failed')
                    result['cleanup_errors'].append(str(error))
            if job is not None:
                try:
                    job.close()
                except BaseException as error:
                    failure('private job handle cleanup failed')
                    result['cleanup_errors'].append(str(error))
        result['deadline_exceeded'] = expired.is_set() or clock() >= deadline
        result['termination_reason'] = ('ownership self-test deadline' if result['deadline_exceeded']
                                        else result['failure_reason'] or 'completed ownership observations')
        if result['deadline_exceeded']:
            failure('ownership self-test deadline')
        result['ownership_self_test_passed'] = (result['failure_reason'] is None
            and result['controller_outside_private_job'] and result['suspended_assignment_order_verified']
            and len(result['owned_identities'])==6 and result['unrelated_survived']
            and result['unrelated_cleanup_verified'] and result['cleanup'].get('verified') is True)
        result['ended_utc'],result['ended_monotonic'] = _utc(),clock()
        result['elapsed_seconds'] = result['ended_monotonic']-started
        record('selftest_end', passed=result['ownership_self_test_passed'],
               failure_reason=result['failure_reason'],elapsed_seconds=result['elapsed_seconds'])
        if result['failure_reason'] is not None:
            result['ownership_self_test_passed'] = False
        journal.close()
        _write_new(output/'result.json',result)
    return result


def _child(role, events, safety_seconds, python_exe):
    _native_guard()
    if role not in {"root", "child", "grandchild", "unrelated"} or not 0 < safety_seconds <= 30:
        raise StandinFailure("unapproved harmless stand-in role or safety deadline")
    events = Path(events).resolve(strict=True)
    if not events.is_dir():
        raise StandinFailure("existing self-test event directory required")
    module = _job_module()
    api = module.NativeApi()
    identity = dict(role=role, kind='interpreter', pid=os.getpid(), parent_pid=os.getppid(),
                    creation_time_100ns=api.creation_time(api.k.GetCurrentProcess()),
                    timestamp_utc=_utc(), monotonic_ns=time.monotonic_ns())
    pending = events / f"{role}.identity.pending"
    final = events / f"{role}.identity.json"
    _write_new(pending, identity)
    if final.exists():
        raise StandinFailure("stand-in identity already exists")
    os.replace(pending, final)
    child = None
    deadline = time.monotonic() + safety_seconds
    try:
        if role in {"root", "child"}:
            next_role = "child" if role == "root" else "grandchild"
            with (events / f"{next_role}.stdout.log").open("xb") as stdout, (events / f"{next_role}.stderr.log").open("xb") as stderr:
                child = subprocess.Popen([str(python_exe), "-I", "-B", str(Path(__file__).resolve()),
                                          "--child-role", next_role, "--events", str(events),
                                          "--safety-seconds", str(safety_seconds)],
                                         stdin=subprocess.DEVNULL, stdout=stdout,
                                         stderr=stderr, close_fds=True, creationflags=0x08000000)
            child_handle = int(child._handle)
            launcher = dict(role=next_role, kind='launcher', pid=api.process_id(child_handle),
                            creation_time_100ns=api.creation_time(child_handle),
                            parent_pid=api.parent_pid(child_handle), timestamp_utc=_utc(),
                            monotonic_ns=time.monotonic_ns())
            if launcher['pid'] != child.pid or launcher['parent_pid'] != os.getpid():
                raise StandinFailure('created child launcher identity mismatch')
            pending = events/f'{next_role}.launcher.identity.pending'
            final = events/f'{next_role}.launcher.identity.json'
            _write_new(pending,launcher)
            if final.exists():
                raise StandinFailure('child launcher evidence already exists')
            os.replace(pending,final)
        while time.monotonic() < deadline:
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child-role", choices=("root", "child", "grandchild", "unrelated"), required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--safety-seconds", type=float, default=30)
    args = parser.parse_args()
    _child(args.child_role, args.events, args.safety_seconds, sys.executable)


if __name__ == "__main__":
    try:
        main()
    except (StandinFailure, OSError, ValueError) as error:
        print(json.dumps(dict(status="failure", reason=str(error))), file=sys.stderr)
        raise SystemExit(1)
