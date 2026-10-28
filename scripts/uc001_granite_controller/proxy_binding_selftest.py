"""Opt-in, network-free Windows proxy identity diagnostic; never acquire or build."""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace


PRIOR_SHA256 = '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a'
PROXY_SHA256 = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
SELFTEST_SECONDS = 20
HELPERS = {'controller.py', 'worker.py', 'standins.py', 'windows_job.py',
           'proxy_binding_selftest.py', 'proxy_no_network.py', 'proxy.py'}


def local(name):
    key = '_granite_proxy_binding_selftest_' + name
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, Path(__file__).with_name(name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


try:
    from . import controller
except ImportError:
    controller = local('controller')
ControllerFailure = controller.ControllerFailure


def validate_zero_acquisition_ledger(path, expected_prior=0, expected_pid=None, terminal=False):
    if type(expected_prior) is not int or expected_prior != 0:
        raise ControllerFailure('selftest_prior_must_be_owner_attested_zero')
    path = Path(path)
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        if terminal:
            raise ControllerFailure('selftest_ledger_missing') from None
        return dict(records=0, complete=False, total=expected_prior, listening_pid=None, event_counts={})
    if len(data) > 65536:
        raise ControllerFailure('selftest_ledger_size_invalid')
    complete_size = data.rfind(b'\n') + 1
    if terminal and complete_size != len(data) or len(data) - complete_size > 8192:
        raise ControllerFailure('selftest_ledger_partial')
    counts = {}
    ended = False
    listening_pid = None
    for raw in data[:complete_size].splitlines():
        try:
            row = controller.strict_json(raw)
            event = row['event']
            if event not in {'start', 'acquisition_clock', 'listening', 'end'} or ended:
                raise ValueError('outbound_or_tunnel_event')
            if (row.get('tunnel_id') is not None or row.get('destination') is not None
                    or type(row.get('tunnel_bytes')) is not int or row['tunnel_bytes'] != 0
                    or type(row.get('cumulative_bytes')) is not int or row['cumulative_bytes'] != expected_prior
                    or 'bytes_read' in row or 'bytes_forwarded' in row):
                raise ValueError('outbound_or_debit_fields')
            counts[event] = counts.get(event, 0) + 1
            if counts[event] != 1 or not counts.get('start'):
                raise ValueError('selftest_ledger_sequence')
            if event == 'start' and (len(counts) != 1
                    or row.get('prior_receipt_sha256') != PRIOR_SHA256
                    or type(row.get('prior_bytes')) is not int or row['prior_bytes'] != expected_prior
                    or row.get('allowance_bytes') != controller.DOWNLOAD_CEILING):
                raise ValueError('selftest_receipt_binding_differs')
            if event == 'listening':
                listening_pid = row.get('pid')
                if (type(listening_pid) is not int or not 0 < listening_pid <= 0xFFFFFFFF
                        or expected_pid is not None and listening_pid != expected_pid):
                    raise ValueError('selftest_listening_identity_differs')
                address = row.get('address')
                if (not isinstance(address, list) or len(address) != 2 or address[0] != '127.0.0.1'
                        or type(address[1]) is not int or not 0 < address[1] <= 65535):
                    raise ValueError('selftest_listener_not_loopback')
            ended = event == 'end'
        except (ValueError, TypeError, KeyError) as error:
            raise ControllerFailure('selftest_zero_acquisition_guard:' + str(error)) from error
    if terminal:
        if not ended:
            raise ControllerFailure('selftest_ledger_terminal_missing')
        controller.validate_proxy_terminal(path, expected_prior, expected_pid)
    return dict(records=sum(counts.values()), complete=ended, total=expected_prior,
                listening_pid=listening_pid, event_counts=counts)


def validate_preparation(config, helper_dir):
    helper_dir = Path(helper_dir).resolve()
    if config.get('prior_sha256') != PRIOR_SHA256:
        raise ControllerFailure('selftest_accepted_prior_receipt_hash_required')
    if config.get('selftest_only') is not True or config.get('proxy_sha256') != PROXY_SHA256:
        raise ControllerFailure('selftest_configuration_not_bounded')
    if set(config.get('selftest_hashes', {})) != HELPERS:
        raise ControllerFailure('selftest_helper_manifest_incomplete')
    for name, expected in config['selftest_hashes'].items():
        if controller.file_hash(helper_dir / name) != expected:
            raise ControllerFailure('selftest_helper_hash_differs:' + name)
    resolved = dict(config)
    for key in ('proxy_helper', 'prior_receipt', 'guard_entry'):
        path = Path(config[key])
        path = (helper_dir / path).resolve() if not path.is_absolute() else path.resolve()
        if path.parent != helper_dir or not path.is_file():
            raise ControllerFailure('selftest_packaged_path_required:' + key)
        resolved[key] = str(path)
    if controller.file_hash(resolved['guard_entry']) != config.get('guard_sha256'):
        raise ControllerFailure('selftest_guard_hash_differs')
    proxy = local('worker').load_proxy(resolved)
    if proxy.load_prior(resolved['prior_receipt'], PRIOR_SHA256) != 0:
        raise ControllerFailure('selftest_prior_must_be_owner_attested_zero')
    return dict(resolved, prior_bytes=0)


class DeadlineGuard:
    def __init__(self, backend, deadline, clock):
        self.backend, self.deadline, self.clock = backend, deadline, clock
        self.stop = threading.Event()
        self.failure = None
        self.thread = None
    def start(self):
        self.thread = threading.Thread(target=self.run, name='proxy-binding-selftest-deadline', daemon=True)
        self.thread.start()
    def run(self):
        while not self.stop.wait(0.025):
            if self.clock() >= self.deadline:
                self.failure = 'proxy_binding_selftest_deadline'
                try:
                    self.backend.terminate()
                except BaseException as error:
                    self.failure += ';termination_failed:' + str(error)
                return
    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(0.25)
            if self.thread.is_alive():
                raise ControllerFailure('selftest_deadline_guard_exit_unverified')


class WorkerBranch:
    def __init__(self, worker, plan, backend, emit, clock, check, remaining):
        self.worker, self.backend, self.emit = worker, backend, emit
        self.expected_controller_pid = plan.get('expected_controller_pid')
        self.clock, self.check, self.remaining = clock, check, remaining
        self.monitor = controller.PhaseMonitor(plan, backend, emit)
        self.bound = False
    def bind(self, row):
        if self.bound or row.get('proxy_binding_selftest') is not True or row.get('worker_identity_query_closed') is not True:
            raise ControllerFailure('selftest_worker_identity_missing_or_query_unclosed')
        m = self.monitor
        interpreter = m.identity(row.get('worker_interpreter_identity'))
        api = self.backend.api
        launcher = m.identity(dict(pid=self.worker.pid, creation_time_100ns=self.worker.creation_time_100ns,
            parent_pid=api.parent_pid(self.worker.handle), in_any_job=True))
        if launcher['parent_pid'] != self.expected_controller_pid:
            raise ControllerFailure('selftest_worker_launcher_parent_not_controller')
        m.verify_retained(launcher, self.worker, alive=True, metadata=True)
        same = interpreter['pid'] == launcher['pid']
        if same:
            if interpreter != launcher:
                raise ControllerFailure('selftest_worker_single_process_identity_differs')
            process = self.worker
        else:
            if interpreter['parent_pid'] != launcher['pid'] or interpreter['creation_time_100ns'] < launcher['creation_time_100ns']:
                raise ControllerFailure('selftest_worker_interpreter_parent_differs')
            process = self.backend.validate_pid(interpreter['pid'], interpreter['creation_time_100ns'])
        m.verify_retained(interpreter, process, alive=True, metadata=True)
        m.proxy_launcher, m.proxy, m.same_process = self.worker, process, same
        m.proxy_identities = dict(launcher=launcher, interpreter=interpreter)
        m.proxy_bound = self.bound = True
        self.emit('selftest_worker_binding_verified', launcher=launcher, interpreter=interpreter, same_process=same)
    def check_branch(self, proxy_monitor):
        if not self.bound or not proxy_monitor.proxy_bound:
            return
        self.check()
        m = self.monitor
        for role, process in (('launcher', m.proxy_launcher), ('interpreter', m.proxy)):
            m.verify_retained(m.proxy_identities[role], process, metadata=not proxy_monitor.proxy_closing)
            if not proxy_monitor.proxy_closing and self.backend.process_exit(process) is not None:
                raise ControllerFailure('selftest_worker_premature_exit')
        proxy_launcher = proxy_monitor.proxy_identities['launcher']
        if proxy_launcher['parent_pid'] != m.proxy.pid:
            raise ControllerFailure('selftest_proxy_not_child_of_verified_worker')
        refs = [dict(identity, role='worker', kind=role,
                    handle=(m.proxy_launcher if role == 'launcher' else m.proxy).handle, verified=True)
                for role, identity in m.proxy_identities.items()]
        base = {(proxy_launcher['pid'], m.proxy.pid)}
        if not m.same_process:
            base.add((m.proxy.pid, m.proxy_launcher.pid))
        parents = {ref['pid'] for ref in refs}
        timeout = min(1.0, self.remaining())
        if proxy_monitor.proxy_closing or m.same_process:
            edges = self.backend.api.children_of(parents, timeout_seconds=timeout)
            allowed = base | {(ref['pid'], ref['parent_pid']) for ref in m.proxy_helpers.values()}
            if (type(edges) is not set or any(type(edge) is not tuple or len(edge) != 2
                    or any(type(pid) is not int or not 0 < pid <= 0xFFFFFFFF for pid in edge)
                    or edge[1] not in parents for edge in edges) or not edges <= allowed):
                raise ControllerFailure('selftest_unknown_worker_branch_process')
        else:
            module = controller.local_module('standins')
            journal = SimpleNamespace(record=lambda event, **values: self.emit('selftest_worker_branch',
                branch_event=event, **values))
            module._check_console_shape(self.backend.api, self.backend.handle, refs, base, True,
                m.proxy_helpers, m.proxy_queries, journal, self.clock, self.check,
                'unexpected selftest worker branch process', timeout)
            for ref in m.proxy_helpers.values():
                self.backend.validate_pid(ref['pid'], ref['creation_time_100ns'])
    def expected(self):
        m = self.monitor
        return {(row['pid'], row['creation_time_100ns']) for row in
                list(m.proxy_identities.values()) + list(m.proxy_helpers.values())}
    def cleanup(self, cleanup):
        return self.monitor.cleanup(cleanup)


def run_binding_session(backend, plan, *, clock=time.monotonic, sleep=time.sleep, journal=None,
                        watchdog_factory=DeadlineGuard, guard_validator=None):
    started = clock()
    deadline = started + SELFTEST_SECONDS
    emit = journal.emit if journal else lambda *args, **values: None
    result = dict(proxy_binding_selftest_passed=False, windows_execution=False, synthetic_injected=True,
        native_binding_verified=False, resource_fit_established=False, acquisition_or_build=False,
        ownership_selftest_run=False, gpu_model_inference=False, zero_acquisition_events_verified=False,
        network_guard_verified=False, suspended_assignment_order_verified=False,
        cleanup=None, proxy_identity_cleanup=None, worker_identity_cleanup=None,
        controller_pid=plan.get('expected_controller_pid'), controller_outside_private_job=False,
        failure_reason=None, started_utc=controller.utc(), timeout_seconds=SELFTEST_SECONDS)
    guard = watchdog_factory(backend, deadline, clock)
    monitor = branch = worker = None
    ownership = []
    expected = set()
    reason = None
    def check():
        if clock() >= deadline or guard.failure:
            raise ControllerFailure(guard.failure or 'proxy_binding_selftest_deadline')
    remaining = lambda: max(0, deadline-clock())
    def exact_job():
        nonlocal expected
        branch.check_branch(monitor)
        expected = branch.expected() | {(row['pid'],row['creation_time_100ns']) for row in
            list(monitor.proxy_identities.values()) + list(monitor.proxy_helpers.values())}
        observation = backend.snapshot()
        actual = {(row['pid'],row['creation_time_100ns']) for row in observation['owned']}
        if actual != expected or observation['total_processes'] != len(expected):
            raise ControllerFailure('selftest_unclassified_job_identity_or_lifetime')
        return observation
    def acknowledge(token):
        if not branch.bound:
            raise ControllerFailure('selftest_worker_binding_missing_before_ack')
        exact_job()
        backend.write_stdin(worker, token)
        emit('selftest_private_ack_sent', bytes=len(token), interpreter_pid=monitor.proxy.pid)
    def consume(rows):
        for row in rows:
            if row.get('event') == 'phase_start': branch.bind(row)
        monitor.accept(rows)
    def drain_after_observed_exit(reader):
        code = backend.process_exit(worker)
        refs = [process for process in (monitor.proxy_launcher, monitor.proxy) if process is not None]
        if code is not None or any(backend.process_exit(process) is not None for process in refs):
            consume(reader.read(terminal=code is not None))
    try:
        if plan.get('name') != 'acquisition' or plan.get('expected_prior_bytes') != 0 or not callable(guard_validator):
            raise ControllerFailure('bounded_selftest_plan_required')
        guard.start()
        worker = backend.launch(plan['argv'], plan['cwd'], plan['env'], plan['stdoutfile'], plan['stderrfile'], stdin_pipe=True)
        backend.validate_pid(worker.pid, worker.creation_time_100ns)
        monitor = controller.PhaseMonitor(plan, backend, emit, acknowledge=acknowledge,
            clock=clock, check_deadline=check, remaining_seconds=remaining)
        branch = WorkerBranch(worker, plan, backend, emit, clock, check, remaining)
        reader = plan.get('events_reader') or controller.FileEvents(plan['events'])
        ledger_seen = False
        while True:
            check()
            for event in backend.drain_events():
                ownership.append(event); emit('ownership', record=event)
            consume(reader.read())
            drain_after_observed_exit(reader)
            try:
                monitor.poll_proxy()
            except ControllerFailure as error:
                if str(error) not in {'proxy_launcher_premature_exit','proxy_interpreter_premature_exit',
                                     'proxy_identity_exited_before_binding'}:
                    raise
                drain_after_observed_exit(reader)
                monitor.poll_proxy()
            if monitor.proxy_bound:
                drain_after_observed_exit(reader)
                try:
                    exact_job()
                except ControllerFailure as error:
                    if str(error) != 'selftest_worker_premature_exit':
                        raise
                    drain_after_observed_exit(reader)
                    exact_job()
            exists = Path(plan['ledgerpath']).exists()
            if ledger_seen and not exists:
                raise ControllerFailure('selftest_ledger_disappeared')
            ledger_seen |= exists
            validate_zero_acquisition_ledger(plan['ledgerpath'], 0,
                monitor.proxy.pid if monitor.proxy_bound else None)
            code = backend.process_exit(worker)
            if code is not None:
                consume(reader.read(terminal=True))
                if code != 0:
                    raise ControllerFailure('selftest_worker_exit:' + str(code))
                if monitor.finish() != 0:
                    raise ControllerFailure('selftest_download_counter_not_zero')
                terminal = monitor.terminal
                handles = terminal.get('worker_handles_closed')
                if (terminal.get('proxy_binding_selftest') is not True or terminal.get('zero_acquisition_events') is not True
                        or not isinstance(handles, dict)
                        or set(handles) != {'interpreter_query','launcher_handle','stdout','stderr'}
                        or any(value is not True for value in handles.values())):
                    raise ControllerFailure('selftest_worker_terminal_or_handle_proof_missing')
                observation = exact_job()
                if any(backend.process_exit(process) != 0 for process in
                       (branch.monitor.proxy_launcher, branch.monitor.proxy)):
                    raise ControllerFailure('selftest_worker_base_exit_not_native_confirmed')
                result['verified_helpers_pending_cleanup'] = observation['active_processes']
                result['zero_acquisition_events_verified'] = validate_zero_acquisition_ledger(
                    plan['ledgerpath'], 0, monitor.proxy.pid, terminal=True)['complete']
                proof = guard_validator(plan['guard_log'], monitor.proxy.pid)
                if proof.get('verified') is not True:
                    raise ControllerFailure('selftest_network_guard_not_verified')
                result['network_guard_verified'] = True
                kinds = [event['event'] for event in ownership if event.get('pid') == worker.pid]
                required = ['worker_created_suspended','worker_assigned','worker_resumed']
                if any(kinds.count(kind) != 1 for kind in required) or [kind for kind in kinds if kind in required] != required:
                    raise ControllerFailure('selftest_suspended_assignment_order_unverified')
                result['suspended_assignment_order_verified'] = True
                result['worker_terminal'] = dict(terminal)
                break
            sleep(0.005)
    except BaseException as error:
        reason = 'selftest_interrupted' if isinstance(error, KeyboardInterrupt) else str(error)
        try:
            backend.terminate()
        except BaseException as stop_error:
            reason += ';termination_failed:' + str(stop_error)
    finally:
        try:
            result['cleanup'] = backend.cleanup(timeout_seconds=min(5, remaining()))
            if not result['cleanup'].get('verified'):
                raise ControllerFailure('private_job_cleanup_unverified')
            if reason is None:
                exits = {(row['pid'],row['creation_time_100ns']) for row in result['cleanup']['owned_exits']
                         if type(row.get('exit_code')) is int}
                if (exits != expected or result['cleanup'].get('total_processes') != len(expected)
                        or result['cleanup'].get('active_processes') != 0):
                    raise ControllerFailure('selftest_complete_identity_cleanup_missing')
        except BaseException as error:
            reason = (reason or '') + ';job_cleanup:' + str(error)
        for name, value in (('proxy_identity_cleanup', monitor), ('worker_identity_cleanup', branch)):
            if value:
                try:
                    result[name] = value.cleanup(result['cleanup'] or {})
                    if not result[name]['verified']:
                        raise ControllerFailure('identity_or_query_handle_cleanup_unverified')
                except BaseException as error:
                    reason = (reason or '') + ';' + name + ':' + str(error)
        try:
            backend.close()
            result['private_job_handle_closed'] = True
        except BaseException as error:
            result['private_job_handle_closed'] = False
            reason = (reason or '') + ';job_close:' + str(error)
        try:
            guard.close()
        except BaseException as error:
            reason = (reason or '') + ';deadline_guard_cleanup:' + str(error)
        if guard.failure:
            reason = reason or guard.failure
        if clock() > deadline:
            reason = reason or 'proxy_binding_selftest_deadline'
        result.update(proxy_binding_selftest_passed=reason is None, failure_reason=reason,
            ended_utc=controller.utc(), elapsed_seconds=clock()-started,
            owned_expected_identities=[dict(pid=pid,creation_time_100ns=birth) for pid,birth in sorted(expected)])
        try: emit('proxy_binding_selftest_end', result=result)
        except BaseException as error:
            result.update(proxy_binding_selftest_passed=False, failure_reason='selftest_terminal_log_failed:' + str(error))
    return result


def preserve_native_failure(output, journal, error, backend=None, *, windows_execution=True):
    result = dict(proxy_binding_selftest_passed=False, failure_reason=str(error),
        windows_execution=windows_execution, synthetic_injected=not windows_execution,
        native_binding_verified=False, resource_fit_established=False, acquisition_or_build=False,
        ownership_selftest_run=False, gpu_model_inference=False,
        accepted_prior_sha256=PRIOR_SHA256, accepted_proxy_sha256=PROXY_SHA256,
        cleanup=dict(verified=False, active_processes=None, total_processes=None,
                     owned_exits=[], errors=['private job cleanup not established']))
    if backend is not None and backend.handle is not None:
        try:
            backend.terminate()
            result['cleanup'] = backend.cleanup(timeout_seconds=5)
        except BaseException as cleanup_error:
            result['cleanup']['errors'].append(str(cleanup_error))
        try:
            backend.close()
            result['private_job_handle_closed'] = True
        except BaseException as close_error:
            result['private_job_handle_closed'] = False
            result['cleanup']['errors'].append(str(close_error))
    try:
        journal.emit('proxy_binding_selftest_entry_failure', result=result)
    except BaseException as journal_error:
        result['journal_failure'] = str(journal_error)
    with (Path(output)/'result.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
        stream.flush()
        os.fsync(stream.fileno())
    return result


def native_selftest(config_path, output, *, owner_authorized=False):
    if owner_authorized is not True:
        raise ControllerFailure('proxy_binding_selftest_not_authorized')
    if os.name != 'nt' or sys.version_info[:3] != (3, 12, 11) or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise ControllerFailure('approved_windows_x64_python_3_12_11_required')
    helper_dir = Path(__file__).resolve().parent
    config = validate_preparation(controller.strict_json(Path(config_path).read_text()), helper_dir)
    output = Path(output).resolve()
    forbidden_root = Path(controller.FIXED_ROOT).resolve()
    if output.is_relative_to(forbidden_root) or forbidden_root.is_relative_to(output):
        raise ControllerFailure('selftest_evidence_must_not_use_native_build_root')
    output.mkdir(parents=True, exist_ok=False)
    (output/'evidence').mkdir()
    journal = controller.Journal(output/'controller.jsonl')
    backend = None
    try:
        worker = local('worker')
        config = dict(config, root=str(output), original_start_utc=controller.utc())
        config_path = output/'selftest-worker-config.json'
        worker.write_json(config_path, config)
        backend = local('windows_job').WindowsJob(memory_limit_bytes=controller.MEMORY_CAP)
        outside = backend.api.controller_in_job(backend.handle) is False
        if not outside:
            raise ControllerFailure('selftest_controller_inside_private_job_or_unknown')
        plan = dict(name='acquisition', expected_prior_bytes=0, ledgerpath=output/'evidence/acquisition-proxy.jsonl',
            guard_log=output/'evidence/proxy-no-network.jsonl', events=output/'worker.events.jsonl',
            argv=[sys.executable,'-I','-B',str(helper_dir/'worker.py'),'--phase','proxy-binding-selftest',
                  '--config',str(config_path),'--events',str(output/'worker.events.jsonl')],
            cwd=str(output), env=dict(os.environ), stdoutfile=output/'worker.stdout.log',
            stderrfile=output/'worker.stderr.log', expected_controller_pid=os.getpid())
        result = run_binding_session(backend, plan, journal=journal,
            guard_validator=lambda path,pid:local('proxy_no_network').validate_guard_log(path,pid))
        result.update(windows_execution=True, synthetic_injected=False,
            native_binding_verified=result['proxy_binding_selftest_passed'],
            controller_pid=os.getpid(), controller_outside_private_job=outside,
            scope='harmless_network_free_proxy_binding_only',
            accepted_prior_sha256=PRIOR_SHA256, accepted_proxy_sha256=PROXY_SHA256)
        worker.write_json(output/'result.json', result)
        return result
    except BaseException as error:
        return preserve_native_failure(output,journal,error,backend)
    finally:
        if backend and backend.handle is not None: backend.close()
        journal.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--owner-authorized', action='store_true')
    args = parser.parse_args()
    result = native_selftest(args.config,args.output,owner_authorized=args.owner_authorized)
    print(json.dumps(result,indent=2))
    return 0 if result['proxy_binding_selftest_passed'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ControllerFailure, OSError, ValueError) as error:
        print(json.dumps(dict(proxy_binding_selftest_passed=False,failure_reason=str(error))),file=sys.stderr)
        raise SystemExit(1)
