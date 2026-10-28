"""Harness checks only; shared interpretation/domain validation remains unchanged."""

import ctypes
from ctypes import wintypes
import math
import ntpath
import os
import re

from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter


class HarnessStop(ValueError):
    def __init__(self, stage, reason):
        self.stage, self.reason = stage, reason
        super().__init__(stage + '/' + reason)


def stop_record(error):
    return {'stage': error.stage if isinstance(error, HarnessStop) else 'unknown',
        'reason': error.reason if isinstance(error, HarnessStop) else 'unexpected_failure',
        'type': type(error).__name__}


def read_windows_process(pid):
    class Basic(ctypes.Structure):
        _fields_ = [('reserved', ctypes.c_void_p), ('peb', ctypes.c_void_p),
            ('reserved2', ctypes.c_void_p * 2), ('pid', ctypes.c_size_t), ('parent', ctypes.c_size_t)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    native = ctypes.WinDLL('ntdll')
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    native.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.c_void_p]
    native.NtQueryInformationProcess.restype = wintypes.LONG
    handle = kernel.OpenProcess(0x1400, False, pid)
    if not handle: raise HarnessStop('ownership', 'process_query_failed')
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        basic = Basic(); image = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(image))
        if (not kernel.GetProcessTimes(handle, *[ctypes.byref(t) for t in times])
                or native.NtQueryInformationProcess(handle, 0, ctypes.byref(basic), ctypes.sizeof(basic), None) != 0
                or not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size))
                or basic.pid != pid):
            raise HarnessStop('ownership', 'process_query_failed')
        return {'pid': pid, 'created': times[0].dwHighDateTime << 32 | times[0].dwLowDateTime,
            'parent_pid': basic.parent, 'image': image.value}
    finally:
        kernel.CloseHandle(handle)


def windows_system_directory():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetSystemDirectoryW.argtypes = [wintypes.LPWSTR, wintypes.UINT]
    kernel.GetSystemDirectoryW.restype = wintypes.UINT
    path = ctypes.create_unicode_buffer(32768)
    size = kernel.GetSystemDirectoryW(path, len(path))
    if not 0 < size < len(path): raise HarnessStop('ownership', 'system_directory_unavailable')
    return path.value


def verify_python_ownership(proof, *, reader=read_windows_process, self_pid=None, self_parent=None,
        system_directory=windows_system_directory):
    try:
        core = [proof[name] for name in ('supervisor', 'redirector', 'interpreter')]
        helpers = proof.get('console_helpers', [])
        if not isinstance(helpers, list) or len(helpers) > 1: raise ValueError()
        identities = core + helpers
        for identity in identities:
            if (type(identity['pid']) is not int or not 0 < identity['pid'] <= 0xffffffff
                    or type(identity['created']) is not int or not 0 < identity['created'] < 2**63
                    or type(identity['parent_pid']) is not int or not 0 <= identity['parent_pid'] <= 0xffffffff
                    or not isinstance(identity['image'], str)
                    or reader(identity['pid']) != identity):
                raise ValueError()
        supervisor, redirector, interpreter = core
        expected = {redirector['pid'], interpreter['pid'], *(h['pid'] for h in helpers)}
        server = proof.get('server_pid', 0)
        if type(server) is not int or not 0 <= server <= 0xffffffff or server in {p['pid'] for p in identities}: raise ValueError()
        if server: expected.add(server)
        if (len({p['pid'] for p in identities}) != len(identities) or proof['job_membership_verified'] is not True
                or any(type(pid) is not int for pid in proof['job_verified_pids'])
                or set(proof['job_verified_pids']) != expected or len(proof['job_verified_pids']) != len(expected)
                or redirector['parent_pid'] != supervisor['pid'] or interpreter['parent_pid'] != redirector['pid']
                or not supervisor['created'] <= redirector['created'] <= interpreter['created']
                or ntpath.normcase(redirector['image']) != ntpath.normcase(r'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe')
                or ntpath.normcase(interpreter['image']) != ntpath.normcase(r'C:\ResolenaExperiments\tools\python-3.12.10\python.exe')
                or interpreter['pid'] != (os.getpid() if self_pid is None else self_pid)
                or redirector['pid'] != (os.getppid() if self_parent is None else self_parent)):
            raise ValueError()
        if helpers:
            directory = system_directory()
            if not ntpath.isabs(directory) or not ntpath.splitdrive(directory)[0]: raise ValueError()
            parents = {p['pid']: p for p in (redirector, interpreter)}
            for helper in helpers:
                parent = parents.get(helper['parent_pid'])
                if (parent is None or helper['created'] < parent['created']
                        or helper['image'].casefold() != ntpath.join(directory, 'conhost.exe').casefold()):
                    raise ValueError()
    except Exception as error:
        raise HarnessStop('ownership', 'identity_mismatch') from error


def verify_reported_settings(props, log):
    try:
        generation = props['default_generation_settings']; params = generation['params']
        if (props['total_slots'] != 1 or generation['n_ctx'] != 8192
                or not re.fullmatch(r'b11429-d81235049[0-9a-f]*', props['build_info'])
                or props['model_path'] != r'C:\ResolenaExperiments\qwen3-8b-v1\Qwen3-8B-Q8_0.gguf'):
            raise HarnessStop('settings', 'runtime_context_mismatch')
        if type(params['n_predict']) is not int or params['n_predict'] != -1:
            raise HarnessStop('settings', 'reported_task_default_mismatch')
        for field, expected in LlamaCppInterpreter.SAMPLING.items():
            value = params[field]
            if type(value) not in (int, float) or not math.isfinite(value) or not math.isclose(value, expected, abs_tol=1e-6):
                raise HarnessStop('settings', 'sampling_mismatch')
        patterns = [r'build 11429 \(d81235049\)', r'using device Vulkan0 \(AMD Radeon RX 6800 XT\)',
            r'offloaded 37/37 layers to GPU', r'n_threads = 2 \(n_threads_batch = 2\)',
            r'n_ctx_seq\s*=\s*8192\b', r'n_batch\s*=\s*64\b', r'n_ubatch\s*=\s*64\b', r'K \(f16\):.*V \(f16\):']
        if any(not re.search(pattern, log) for pattern in patterns):
            raise HarnessStop('settings', 'offload_settings_unverified')
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, HarnessStop): raise
        raise HarnessStop('settings', 'report_unavailable') from error


def verify_request_limit(body):
    if (not isinstance(body, dict) or type(body.get('max_tokens')) is not int or body['max_tokens'] != 3072
            or any(name in body for name in ('n_predict', 'max_completion_tokens'))):
        raise HarnessStop('output_limit', 'request_limit_mismatch')


def verify_effective(props, log, launch_args, body):
    verify_reported_settings(props, log)
    if (not isinstance(launch_args, list) or launch_args.count('--predict') != 1
            or any(a in ('-n', '--n-predict') or a.startswith(('--predict=', '--n-predict=')) for a in launch_args)):
        raise HarnessStop('output_limit', 'cli_limit_unverified')
    index = launch_args.index('--predict')
    if index + 1 >= len(launch_args) or launch_args[index + 1] != '3072':
        raise HarnessStop('output_limit', 'cli_limit_mismatch')
    verify_request_limit(body)
    return {'reported_task_default': -1, 'cli_limit': 3072, 'request_limit': 3072}


def adapter_limit_body():
    adapter = object.__new__(LlamaCppInterpreter)
    adapter.prompt = 'Explicit model-free request-construction check; never sent.'
    return adapter.request_body('Explicit synthetic input; never sent.')


def check_saved_receipt(receipt):
    verify_reported_settings(receipt['props'], receipt['startup_log'])
    body = adapter_limit_body(); verify_request_limit(body)
    cli_verified = False
    if 'launch_args' in receipt:
        verify_effective(receipt['props'], receipt['startup_log'], receipt['launch_args'], body)
        cli_verified = True
    return {'saved_report_compatible': True, 'reported_task_default': -1, 'request_limit_code': 3072,
        'cli_execution_verified': cli_verified, 'cli_evidence': 'recorded_argv' if cli_verified else 'unavailable_in_saved_receipt',
        'generation_evidence': 'unavailable', 'model_readiness_verified': False}
