"""Owned worker for the prepared source acquisition and model-free native build."""
import argparse
import ctypes
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import types
from dataclasses import dataclass
from datetime import datetime, timezone
from zipfile import ZipFile

COMMIT = '620d2225cc436ab0b001e3200e590e3b286ef9ab'
SOURCE = 'https://github.com/ggml-org/llama.cpp.git'
ROOT = r'C:\Resolena\gn1-20261025'
GIT = r'C:\Program Files\Git\cmd\git.exe'
VS = r'C:\Program Files\Microsoft Visual Studio\2022\Community'
CMAKE = VS + r'\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
NINJA = VS + r'\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
CL = VS + r'\VC\Tools\MSVC\14.43.34808\bin\Hostx64\x64\cl.exe'
SDK = r'C:\VulkanSDK\1.4.357.0'
PROXY_SHA256 = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
CEILING = 10737418240


class WorkerFailure(RuntimeError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


class Journal:
    def __init__(self, path):
        self.stream = Path(path).open('x', encoding='utf-8', newline='\n')
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.stream.close()
    def emit(self, event, **data):
        record = dict(event=event, timestamp_utc=utc(), monotonic_ns=time.monotonic_ns(), **data)
        self.stream.write(json.dumps(record, sort_keys=True) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())


def build_flags():
    return ['-DCMAKE_BUILD_TYPE=Release', '-DFETCHCONTENT_FULLY_DISCONNECTED=ON',
            '-DGGML_VULKAN=ON', '-DLLAMA_BUILD_SERVER=ON', '-DLLAMA_BUILD_TOOLS=ON',
            '-DLLAMA_BUILD_COMMON=ON', '-DLLAMA_BUILD_IS_DEV=OFF',
            '-DLLAMA_BUILD_COMMIT=' + COMMIT, '-DLLAMA_BUILD_NUMBER=0',
            '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF', '-DLLAMA_BUILD_APP=OFF',
            '-DLLAMA_BUILD_UI=OFF', '-DLLAMA_USE_PREBUILT_UI=OFF', '-DLLAMA_OPENSSL=OFF',
            '-DLLAMA_SUBPROCESS=OFF', '-DLLAMA_LLGUIDANCE=OFF']


def validate_environment(environ, exists=os.path.isfile, which=shutil.which):
    env = dict(environ)
    required = [GIT, CMAKE, NINJA, CL, SDK + r'\Bin\glslc.exe',
                SDK + r'\Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake']
    if not all(exists(path) for path in required):
        raise WorkerFailure('required_existing_tool_missing')
    if (env.get('VCToolsVersion', '').rstrip('\\') != '14.43.34808'
            or env.get('WindowsSDKVersion', '').rstrip('\\') != '10.0.22621.0'
            or env.get('VSCMD_ARG_HOST_ARCH') not in ('x64', 'amd64')
            or env.get('VSCMD_ARG_TGT_ARCH') not in ('x64', 'amd64')):
        raise WorkerFailure('frozen_x64_environment_not_active')
    for key in ('VULKAN_SDK', 'VK_SDK_PATH'):
        if ntpath.normcase(env.get(key, '').rstrip('\\')) != ntpath.normcase(SDK):
            raise WorkerFailure('pinned_vulkan_environment_differs')
    for name, expected in [('cl.exe', CL), ('glslc.exe', SDK + r'\Bin\glslc.exe')]:
        if ntpath.normcase(which(name) or '') != ntpath.normcase(expected):
            raise WorkerFailure('active_tool_differs:' + name)
    if any(env.get(key) for key in ('CC', 'CXX', 'CMAKE_TOOLCHAIN_FILE', 'CMAKE_PREFIX_PATH')):
        raise WorkerFailure('unreviewed_toolchain_override')
    env['PATH'] = ntpath.dirname(NINJA) + ';' + env.get('PATH', '')
    env['CMAKE_BUILD_PARALLEL_LEVEL'] = '2'
    env['GIT_LFS_SKIP_SMUDGE'] = '1'
    return env


def child_identity(process):
    if os.name != 'nt':
        raise WorkerFailure('native_child_identity_requires_windows')
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel.IsProcessInJob.restype = wintypes.BOOL
    created, exited, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
    member = wintypes.BOOL()
    handle = wintypes.HANDLE(int(process._handle))
    if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                  ctypes.byref(kernel_time), ctypes.byref(user_time)):
        raise WorkerFailure('child_creation_identity_unavailable')
    if not kernel.IsProcessInJob(handle, None, ctypes.byref(member)) or not member.value:
        raise WorkerFailure('child_job_membership_missing')
    return dict(pid=process.pid, creation_time_100ns=(created.dwHighDateTime << 32) | created.dwLowDateTime,
                in_any_job=True)


@dataclass
class Child:
    process: object
    label: str
    stdout_path: Path
    stderr_path: Path
    stdout_file: object
    stderr_file: object
    identity: dict


class NativeRunner:
    def __init__(self, root, journal, environment):
        self.root, self.journal, self.environment = Path(root), journal, environment
    def start(self, argv, label, env=None, stdin=False):
        evidence = self.root / 'evidence'
        out_path, err_path = evidence / (label + '.stdout.log'), evidence / (label + '.stderr.log')
        out, err = out_path.open('xb'), err_path.open('xb')
        try:
            process = subprocess.Popen(argv, cwd=self.root, env=env or self.environment,
                                       stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                       stdout=out, stderr=err, shell=False)
            identity = child_identity(process)
            self.journal.emit('child_started', label=label, argv=[str(a) for a in argv], **identity)
            return Child(process, label, out_path, err_path, out, err, identity)
        except BaseException:
            out.close(); err.close()
            raise
    def wait(self, child, proxy=None):
        while child.process.poll() is None:
            if proxy is not None and proxy.process.poll() is not None:
                raise WorkerFailure('proxy_premature_exit')
            time.sleep(0.025)
        code = child.process.wait()
        for stream in (child.stdout_file, child.stderr_file):
            stream.flush(); os.fsync(stream.fileno()); stream.close()
        self.journal.emit('child_exit', label=child.label, exit_code=code, **child.identity)
        if code != 0:
            raise WorkerFailure('command_failed:' + child.label)
        if child.label in ('source-revision', 'source-tree', 'proxy'):
            if child.stdout_path.stat().st_size > 1024 * 1024:
                raise WorkerFailure('unexpected_metadata_output_size')
            return child.stdout_path.read_text(encoding='utf-8')
        return ''
    def run(self, argv, label, env=None, proxy=None):
        return self.wait(self.start(argv, label, env), proxy)
    def ready(self, proxy):
        started = time.monotonic()
        while time.monotonic() - started < 10:
            if proxy.process.poll() is not None:
                raise WorkerFailure('proxy_startup_exit')
            data = proxy.stdout_path.read_bytes()
            if len(data) > 65536:
                raise WorkerFailure('proxy_readiness_too_large')
            if b'\n' in data:
                return json.loads(data.split(b'\n', 1)[0])
            time.sleep(0.025)
        raise WorkerFailure('proxy_readiness_timeout')


def load_proxy(config):
    path = Path(config['proxy_helper'])
    data = path.read_bytes()
    if config['proxy_sha256'] != PROXY_SHA256 or hashlib.sha256(data).hexdigest() != PROXY_SHA256:
        raise WorkerFailure('accepted_proxy_hash_differs')
    module = types.ModuleType('_granite_accepted_proxy')
    module.__file__ = str(path)
    exec(compile(data, str(path), 'exec'), module.__dict__)
    if module.COMMIT != COMMIT or module.SOURCE != SOURCE or module.CEILING != CEILING:
        raise WorkerFailure('accepted_proxy_contract_differs')
    return module


def validate_proxy_terminal(path, closed, prior):
    try:
        data = Path(path).read_bytes()
    except OSError as error:
        raise WorkerFailure('proxy_ledger_missing_or_unreadable') from error
    if not data.endswith(b'\n'):
        raise WorkerFailure('partial_proxy_ledger')
    try:
        records = [json.loads(line) for line in data.splitlines()]
        if not records or records[0]['event'] != 'start' or records[0]['prior_bytes'] != prior:
            raise ValueError('initial credit differs')
        total = prior
        totals = {}
        for index, row in enumerate(records):
            if row['event'] not in {'start', 'acquisition_clock', 'listening', 'tunnel_start', 'debit', 'tunnel_end', 'end'}:
                raise ValueError('unknown ledger event')
            if row['event'] == 'start' and index != 0:
                raise ValueError('duplicate ledger start')
            value = row['cumulative_bytes']
            if type(value) is not int or not prior <= value < CEILING:
                raise ValueError('counter outside remaining allowance')
            if row['event'] == 'debit':
                count = row['bytes_read']
                key = row['tunnel_id']
                if type(count) is not int or count <= 0 or value != total + count or row['destination'] != 'github.com:443':
                    raise ValueError('invalid debit')
                totals[key] = totals.get(key, 0) + count
                if row['tunnel_bytes'] != totals[key]:
                    raise ValueError('tunnel total differs')
            elif value != total:
                raise ValueError('non-debit changed counter')
            if row['event'] == 'end' and index != len(records) - 1:
                raise ValueError('records after terminal')
            total = value
        end = records[-1]
        if end['event'] != 'end' or end['status'] != 'closed_unqualified' or end['sockets_closed'] is not True:
            raise ValueError('missing or failed terminal')
        if (closed['status'] != 'meter_closed_unqualified' or closed['cleanup_verified'] is not True
                or closed['cumulative_bytes'] != total
                or closed['ledger_sha256'] != hashlib.sha256(data).hexdigest()):
            raise ValueError('proxy terminal differs')
        return total
    except (ValueError, KeyError, TypeError) as error:
        raise WorkerFailure('proxy_terminal_invalid') from error


def extract_source(archive, destination):
    destination = Path(destination)
    if destination.exists():
        raise WorkerFailure('source_directory_already_exists')
    with ZipFile(archive) as value:
        for entry in value.infolist():
            parts = PurePosixPath(entry.filename).parts
            if (not parts or PurePosixPath(entry.filename).is_absolute() or '..' in parts
                    or '\\' in entry.filename or ':' in entry.filename
                    or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise WorkerFailure('unsafe_source_archive_member')
        value.extractall(destination)


def _clean_git_environment(env, empty_config):
    clean = {k: v for k, v in env.items() if not k.upper().startswith('GIT_')
             and not k.lower().endswith('_proxy') and k.upper() not in ('SSH_ASKPASS', 'CURL_HOME')}
    clean.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=str(empty_config),
                 GIT_CONFIG_SYSTEM=str(empty_config), GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    return clean


def run_acquisition(config, journal, runner=None):
    root = Path(config['root']); evidence = root / 'evidence'
    journal.emit('phase_start', phase='acquisition', original_start_utc=config['original_start_utc'])
    for name in ('source-repository', 'llama-620d2225-source.zip', 'src', 'build'):
        if (root / name).exists():
            raise WorkerFailure('fresh_acquisition_paths_required:' + name)
    module = load_proxy(config)
    prior = module.load_prior(config['prior_receipt'], config['prior_sha256'])
    empty = evidence / 'proxy-empty.config'; empty.open('xb').close()
    hooks = evidence / 'proxy-empty-hooks'; hooks.mkdir()
    env = _clean_git_environment(config.get('environment', os.environ), empty)
    runner = runner or NativeRunner(root, journal, env)
    for executable, label in [(GIT, 'git-version'), (CMAKE, 'cmake-version'), (NINJA, 'ninja-version')]:
        runner.run([executable, '--version'], label, env)
    tool_paths = [GIT, CMAKE, NINJA, CL, SDK + r'\Bin\glslc.exe',
                  SDK + r'\Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake']
    write_json(evidence / 'tool-hashes.json', [{'path': p, 'sha256': digest(p)} for p in tool_paths])
    write_json(evidence / 'build-environment.json', {key: config.get('environment', os.environ).get(key)
              for key in ('VCToolsVersion', 'WindowsSDKVersion', 'VULKAN_SDK')})
    repo = root / 'source-repository'
    runner.run([GIT, 'init', str(repo)], 'source-init', env)
    runner.run([GIT, '-C', str(repo), 'remote', 'add', 'origin', SOURCE], 'source-origin', env)
    ledger = evidence / 'acquisition-proxy.jsonl'
    argv = [sys.executable, '-I', str(config['proxy_helper']), '--ledger', str(ledger),
            '--prior-receipt', str(config['prior_receipt']), '--prior-sha256', config['prior_sha256'],
            '--acquisition-started-utc', config['original_start_utc']]
    proxy = runner.start(argv, 'proxy', env, stdin=True)
    ready = runner.ready(proxy)
    if (ready.get('pid') != proxy.identity['pid'] or ready.get('ledger') != str(ledger)
            or ready.get('prior_bytes') != prior or ready.get('remaining_bytes') != CEILING - prior):
        raise WorkerFailure('proxy_readiness_identity_differs')
    from urllib.parse import urlsplit
    url = urlsplit(ready['proxy_url'])
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.path or url.username or not url.port:
        raise WorkerFailure('proxy_readiness_address_differs')
    journal.emit('proxy_started', ledger_path=str(ledger), **proxy.identity)
    fetch_argv, fetch_env = module.git_fetch_spec(GIT, repo, ('127.0.0.1', url.port), empty, hooks, env)
    write_json(evidence / 'source-fetch.proxy-spec.json', {'argv': fetch_argv,
               'proxy_url': ready['proxy_url'], 'proxy_pid': proxy.identity['pid']})
    runner.run(fetch_argv, 'source-fetch', fetch_env, proxy)
    journal.emit('proxy_closing', **proxy.identity)
    proxy.process.stdin.write(b'CLOSE\n'); proxy.process.stdin.flush(); proxy.process.stdin.close()
    proxy_lines = [json.loads(line) for line in runner.wait(proxy).splitlines()]
    if len(proxy_lines) != 2 or proxy_lines[0] != ready:
        raise WorkerFailure('proxy_stdout_terminal_differs')
    total = validate_proxy_terminal(ledger, proxy_lines[1], prior)
    if digest(config['proxy_helper']) != PROXY_SHA256:
        raise WorkerFailure('proxy_changed_during_acquisition')
    revision = runner.run([GIT, '-C', str(repo), 'rev-parse', '--verify', 'FETCH_HEAD^{commit}'],
                          'source-revision', env).strip()
    if revision != COMMIT:
        raise WorkerFailure('fetched_commit_differs')
    runner.run([GIT, '-C', str(repo), 'fsck', '--full', '--strict', COMMIT], 'source-fsck', env)
    archive = root / 'llama-620d2225-source.zip'
    runner.run([GIT, '-C', str(repo), 'archive', '--format=zip', '--output=' + str(archive), COMMIT],
               'source-archive', env)
    tree = runner.run([GIT, '-C', str(repo), 'rev-parse', COMMIT + '^{tree}'], 'source-tree', env).strip()
    if len(tree) != 40 or any(c not in '0123456789abcdef' for c in tree):
        raise WorkerFailure('source_tree_identity_invalid')
    write_json(evidence / 'source-identity.json', dict(version='v0.7.0', commit=COMMIT, tree=tree,
               archive=str(archive), bytes=archive.stat().st_size, sha256=digest(archive)))
    extract_source(archive, root / 'src')
    journal.emit('acquisition_terminal', ledger_path=str(ledger), ledger_sha256=digest(ledger),
                 cumulative_bytes=total, prior_bytes=prior, proxy_pid=proxy.identity['pid'])
    journal.emit('phase_complete', phase='acquisition')


def run_build(config, journal, runner=None):
    root = Path(config['root']); evidence = root / 'evidence'
    journal.emit('phase_start', phase='build')
    source = root / 'src'; build = root / 'build'
    if not source.is_dir() or build.exists():
        raise WorkerFailure('source_missing_or_build_not_fresh')
    if json.loads((evidence / 'source-identity.json').read_text())['commit'] != COMMIT:
        raise WorkerFailure('source_identity_differs')
    env = config.get('environment', os.environ)
    runner = runner or NativeRunner(root, journal, env)
    runner.run([CMAKE, '-S', str(source), '-B', str(build), '-G', 'Ninja'] + build_flags(), 'configure', env)
    cache = {}
    for line in (build / 'CMakeCache.txt').read_text().splitlines():
        if ':' in line and '=' in line and not line.startswith(('#', '//')):
            key, value = line.split('=', 1)
            cache[key.split(':', 1)[0]] = value
    expected = {'CMAKE_C_COMPILER': CL, 'CMAKE_CXX_COMPILER': CL, 'CMAKE_MAKE_PROGRAM': NINJA,
                'Vulkan_GLSLC_EXECUTABLE': SDK + r'\Bin\glslc.exe',
                'SPIRV-Headers_DIR': SDK + r'\Lib\cmake\SPIRV-Headers'}
    for key, value in expected.items():
        if ntpath.normcase(ntpath.normpath(cache.get(key, ''))) != ntpath.normcase(ntpath.normpath(value)):
            raise WorkerFailure('configured_tool_differs:' + key)
    runner.run([CMAKE, '--build', str(build), '--config', 'Release', '--target', 'llama-server',
                '--parallel', '2'], 'build', env)
    server = build / 'bin/llama-server.exe'
    if not server.is_file():
        raise WorkerFailure('server_artifact_missing')
    artifacts = [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p)}
                 for p in sorted((build / 'bin').iterdir()) if p.is_file()]
    write_json(evidence / 'built-artifacts.json', artifacts)
    write_json(evidence / 'build-metadata-hashes.json', [{'path': str(p), 'sha256': digest(p)}
               for p in (build / 'CMakeCache.txt', build / 'build.ninja')])
    manifest = evidence / 'built-artifacts.json'
    journal.emit('build_terminal', artifact_manifest_path=str(manifest),
                 artifact_manifest_sha256=digest(manifest), artifact_count=len(artifacts))
    journal.emit('phase_complete', phase='build')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('acquisition', 'build'), required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--events', type=Path, required=True)
    args = parser.parse_args()
    if os.name != 'nt' or sys.version_info[:3] != (3, 12, 11):
        raise WorkerFailure('approved_windows_python_required')
    config = json.loads(args.config.read_text())
    if ntpath.normcase(config['root']) != ntpath.normcase(ROOT):
        raise WorkerFailure('fixed_native_root_required')
    config['environment'] = validate_environment(os.environ)
    with Journal(args.events) as journal:
        try:
            (run_acquisition if args.phase == 'acquisition' else run_build)(config, journal)
        except BaseException as error:
            journal.emit('worker_failure', phase=args.phase, reason=str(error))
            raise


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print(json.dumps(dict(status='worker_failure', reason=str(error))), file=sys.stderr, flush=True)
        raise SystemExit(1)
