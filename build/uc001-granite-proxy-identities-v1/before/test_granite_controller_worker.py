import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.uc001_granite_controller.worker import (
    COMMIT, GIT, CMAKE, NINJA, CL, SDK, WorkerFailure,
    Journal, build_flags, extract_source, run_acquisition, run_build,
    validate_environment, validate_proxy_terminal,
)


class Events:
    def __init__(self):
        self.events = []
    def emit(self, event, **data):
        self.events.append(dict(event=event, **data))


def config(tmp_path):
    root = tmp_path / 'native'
    (root / 'evidence').mkdir(parents=True)
    return {'root': str(root), 'original_start_utc': '2026-10-25T12:00:00+00:00',
            'proxy_helper': 'proxy.py', 'proxy_sha256': 'test',
            'prior_receipt': 'prior.json', 'prior_sha256': 'prior'}


def test_flags_match_frozen_manifest_without_new_allowances():
    frozen = json.loads(Path('scripts/uc001_granite_contract_v1/config.json').read_text())
    expected = dict(frozen['runtime']['build_options'], CMAKE_BUILD_TYPE='Release')
    actual = dict(flag[2:].split('=', 1) for flag in build_flags())
    assert actual == expected
    assert len(build_flags()) == 17


def test_journal_is_exclusive_and_durable(tmp_path):
    path = tmp_path / 'events.jsonl'
    with Journal(path) as journal:
        journal.emit('phase_start', phase='acquisition')
    record = json.loads(path.read_text().strip())
    assert record['event'] == 'phase_start'
    assert record['timestamp_utc']
    assert type(record['monotonic_ns']) is int
    with pytest.raises(FileExistsError):
        Journal(path)


def test_environment_guard_rejects_unactivated_toolchain():
    with pytest.raises(WorkerFailure):
        validate_environment({}, exists=lambda _: True, which=lambda _: None)


def test_environment_guard_accepts_only_frozen_activation():
    env = {'VCToolsVersion': '14.43.34808\\', 'WindowsSDKVersion': '10.0.22621.0\\',
           'VSCMD_ARG_HOST_ARCH': 'x64', 'VSCMD_ARG_TGT_ARCH': 'x64',
           'VULKAN_SDK': SDK, 'VK_SDK_PATH': SDK}
    lookup = {'cl.exe': CL, 'glslc.exe': SDK + r'\Bin\glslc.exe', 'ninja.exe': NINJA}
    result = validate_environment(env, exists=lambda _: True, which=lookup.get)
    assert result['CMAKE_BUILD_PARALLEL_LEVEL'] == '2'
    assert result['GIT_LFS_SKIP_SMUDGE'] == '1'
    with pytest.raises(WorkerFailure):
        validate_environment(dict(env, CC='unreviewed'), exists=lambda _: True, which=lookup.get)


def test_archive_extraction_rejects_path_traversal(tmp_path):
    archive = tmp_path / 'source.zip'
    with ZipFile(archive, 'w') as value:
        value.writestr('../escape.txt', 'unsafe')
    with pytest.raises(WorkerFailure):
        extract_source(archive, tmp_path / 'src')
    assert not (tmp_path / 'escape.txt').exists()


def test_archive_extraction_preserves_safe_files(tmp_path):
    archive = tmp_path / 'source.zip'
    with ZipFile(archive, 'w') as value:
        value.writestr('src/file.txt', b'synthetic source')
    extract_source(archive, tmp_path / 'src')
    assert (tmp_path / 'src/src/file.txt').read_bytes() == b'synthetic source'


def ledger_fixture(tmp_path, cumulative=12):
    path = tmp_path / 'proxy.jsonl'
    records = [dict(event='start', cumulative_bytes=7, prior_bytes=7),
               dict(event='debit', cumulative_bytes=cumulative, bytes_read=cumulative - 7,
                    tunnel_id='1', destination='github.com:443', tunnel_bytes=cumulative - 7),
               dict(event='end', cumulative_bytes=cumulative, status='closed_unqualified',
                    sockets_closed=True)]
    path.write_text(''.join(json.dumps(x) + '\n' for x in records))
    return path


def test_proxy_terminal_requires_complete_matching_ledger(tmp_path):
    path = ledger_fixture(tmp_path)
    closed = {'status': 'meter_closed_unqualified', 'cumulative_bytes': 12,
              'cleanup_verified': True, 'ledger_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    assert validate_proxy_terminal(path, closed, 7) == 12
    path.write_text(path.read_text().rstrip('\n'))
    with pytest.raises(WorkerFailure):
        validate_proxy_terminal(path, closed, 7)


@pytest.mark.parametrize('damage', ['missing_end', 'bad_json', 'counter_decrease', 'cap_exhausted'])
def test_proxy_unknown_or_failed_terminal_never_passes(tmp_path, damage):
    path = ledger_fixture(tmp_path)
    if damage == 'missing_end':
        path.write_text('\n'.join(path.read_text().splitlines()[:-1]) + '\n')
    elif damage == 'bad_json':
        path.write_text(path.read_text() + 'broken\n')
    elif damage == 'counter_decrease':
        path.write_text(path.read_text().replace('"cumulative_bytes": 12', '"cumulative_bytes": 6'))
    else:
        path.write_text(path.read_text().replace('"cumulative_bytes": 12', '"cumulative_bytes": 10737418240'))
    closed = {'status': 'meter_closed_unqualified', 'cumulative_bytes': 12,
              'cleanup_verified': True, 'ledger_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    with pytest.raises(WorkerFailure):
        validate_proxy_terminal(path, closed, 7)


class BuildRunner:
    def __init__(self, root, failed=None, cache_mismatch=False):
        self.root, self.failed, self.cache_mismatch = root, failed, cache_mismatch
        self.commands = []
    def run(self, argv, label, env=None, proxy=None):
        self.commands.append((argv, label, env))
        if label == self.failed:
            raise WorkerFailure('synthetic command failed')
        if label == 'configure':
            build = self.root / 'build'
            build.mkdir()
            entries = {'CMAKE_C_COMPILER': CL, 'CMAKE_CXX_COMPILER': CL,
                       'CMAKE_MAKE_PROGRAM': NINJA,
                       'Vulkan_GLSLC_EXECUTABLE': SDK + r'\Bin\glslc.exe',
                       'SPIRV-Headers_DIR': SDK + r'\Lib\cmake\SPIRV-Headers'}
            if self.cache_mismatch:
                entries['CMAKE_C_COMPILER'] = 'wrong compiler'
            (build / 'CMakeCache.txt').write_text(''.join(f'{k}:FILEPATH={v}\n' for k,v in entries.items()))
            (build / 'build.ninja').write_text('synthetic build metadata')
        if label == 'build':
            (self.root / 'build/bin').mkdir()
            (self.root / 'build/bin/llama-server.exe').write_bytes(b'synthetic artifact, not executed')
        return ''


def build_config(tmp_path):
    value = config(tmp_path)
    root = Path(value['root'])
    (root / 'src').mkdir()
    (root / 'evidence/source-identity.json').write_text(json.dumps({'commit': COMMIT}))
    return value


def test_build_configure_and_build_share_one_phase_with_exact_flags(tmp_path):
    value = build_config(tmp_path); events = Events(); root = Path(value['root'])
    runner = BuildRunner(root)
    run_build(value, events, runner=runner)
    assert [label for _,label,_ in runner.commands] == ['configure', 'build']
    assert runner.commands[0][0] == [CMAKE, '-S', str(root/'src'), '-B', str(root/'build'), '-G', 'Ninja'] + build_flags()
    assert runner.commands[1][0][-2:] == ['--parallel', '2']
    assert [r['event'] for r in events.events].count('phase_start') == 1
    assert [r['event'] for r in events.events].count('phase_complete') == 1
    assert (root / 'evidence/built-artifacts.json').is_file()


@pytest.mark.parametrize('failure', ['configure', 'build'])
def test_failed_command_is_not_retried(tmp_path, failure):
    value = build_config(tmp_path); runner = BuildRunner(Path(value['root']), failed=failure)
    with pytest.raises(WorkerFailure):
        run_build(value, Events(), runner=runner)
    assert sum(label == failure for _,label,_ in runner.commands) == 1
    if failure == 'configure':
        assert not any(label == 'build' for _,label,_ in runner.commands)


def test_cache_tool_mismatch_stops_before_build(tmp_path):
    value = build_config(tmp_path); runner = BuildRunner(Path(value['root']), cache_mismatch=True)
    with pytest.raises(WorkerFailure):
        run_build(value, Events(), runner=runner)
    assert [label for _,label,_ in runner.commands] == ['configure']


class ProxyInput:
    def __init__(self):
        self.value = bytearray(); self.closed = False
    def write(self, value):
        self.value.extend(value)
    def flush(self):
        pass
    def close(self):
        self.closed = True


class AcquisitionRunner:
    def __init__(self, root, revision=COMMIT, failed=None):
        self.root, self.revision, self.failed = root, revision, failed
        self.commands = []
        self.ready_value = None
    def run(self, argv, label, env=None, proxy=None):
        self.commands.append((argv, label, env))
        if label == self.failed:
            raise WorkerFailure('synthetic command failed')
        repo = self.root / 'source-repository'
        if label == 'source-init':
            (repo / '.git').mkdir(parents=True)
            (repo / '.git/config').write_text('[core]\nrepositoryformatversion = 0\nfilemode = true\nbare = false\nlogallrefupdates = true\n')
        elif label == 'source-origin':
            with (repo / '.git/config').open('a') as stream:
                stream.write('[remote "origin"]\nurl = https://github.com/ggml-org/llama.cpp.git\nfetch = +refs/heads/*:refs/remotes/origin/*\n')
        elif label == 'source-revision':
            return self.revision + '\n'
        elif label == 'source-tree':
            return 'a' * 40 + '\n'
        elif label == 'source-archive':
            with ZipFile(self.root / 'llama-620d2225-source.zip', 'w') as archive:
                archive.writestr('CMakeLists.txt', 'synthetic, never configured')
        return ''
    def start(self, argv, label, env=None, stdin=False):
        from types import SimpleNamespace
        assert label == 'proxy' and stdin
        self.commands.append((argv, label, env))
        assert argv[argv.index('--acquisition-started-utc')+1] == '2026-10-25T12:00:00+00:00'
        ledger = self.root / 'evidence/acquisition-proxy.jsonl'
        self.ready_value = dict(pid=700, proxy_url='http://127.0.0.1:12345', ledger=str(ledger),
                                prior_bytes=7, remaining_bytes=10737418240-7)
        records = [dict(event='start', cumulative_bytes=7, prior_bytes=7),
                   dict(event='debit', cumulative_bytes=12, bytes_read=5,
                        tunnel_id='1', destination='github.com:443', tunnel_bytes=5),
                   dict(event='end', cumulative_bytes=12, status='closed_unqualified', sockets_closed=True)]
        ledger.write_text(''.join(json.dumps(x)+'\n' for x in records))
        self.proxy = SimpleNamespace(identity=dict(pid=700, creation_time_100ns=900, in_any_job=True),
                                     process=SimpleNamespace(stdin=ProxyInput()))
        return self.proxy
    def ready(self, proxy):
        assert proxy is self.proxy
        return self.ready_value
    def wait(self, proxy):
        assert proxy is self.proxy
        assert proxy.process.stdin.value == b'CLOSE\n'
        ledger = self.root / 'evidence/acquisition-proxy.jsonl'
        closed = dict(status='meter_closed_unqualified', cleanup_verified=True,
                      cumulative_bytes=12, ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest())
        return json.dumps(self.ready_value)+'\n'+json.dumps(closed)+'\n'


def acquisition_config(tmp_path, monkeypatch):
    from scripts.uc001_granite_controller import worker
    value = config(tmp_path)
    helper = Path('scripts/uc001_granite_acquisition_proxy/proxy.py').resolve()
    prior = tmp_path / 'prior.json'
    prior.write_text(json.dumps(dict(bundle_id='9a4acb903c834737809b2648c358da9f2d91b116471966fb7b691847a069f4b4',
                                    owner='synthetic test', accounting_complete=True, previously_charged_bytes=7)))
    value.update(proxy_helper=str(helper), proxy_sha256=worker.PROXY_SHA256,
                 prior_receipt=str(prior), prior_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
                 environment={'NO_PROXY': '*', 'GIT_EXEC_PATH': 'untrusted'})
    real_digest = worker.digest
    monkeypatch.setattr(worker, 'digest', lambda path: '0'*64 if str(path) in
                        [GIT, CMAKE, NINJA, CL, SDK+r'\Bin\glslc.exe', SDK+r'\Lib\cmake\SPIRV-Headers\SPIRV-HeadersConfig.cmake']
                        else real_digest(path))
    return value


def test_acquisition_preserves_proxy_pin_integrity_archive_and_shared_clock(tmp_path, monkeypatch):
    value = acquisition_config(tmp_path, monkeypatch); root = Path(value['root'])
    runner = AcquisitionRunner(root); events = Events()
    run_acquisition(value, events, runner=runner)
    labels = [label for _,label,_ in runner.commands]
    assert labels == ['git-version', 'cmake-version', 'ninja-version', 'source-init', 'source-origin',
                      'proxy', 'source-fetch', 'source-revision', 'source-fsck', 'source-archive', 'source-tree']
    fetch, _, env = next(row for row in runner.commands if row[1] == 'source-fetch')
    assert fetch[-1] == COMMIT
    assert 'http.proxy=http://127.0.0.1:12345' in fetch
    assert 'remote.origin.proxy=http://127.0.0.1:12345' in fetch
    assert 'NO_PROXY' not in env and 'GIT_EXEC_PATH' not in env
    assert [row['event'] for row in events.events].count('phase_start') == 1
    assert [row['event'] for row in events.events].index('proxy_closing') < [row['event'] for row in events.events].index('acquisition_terminal')
    terminal = next(row for row in events.events if row['event'] == 'acquisition_terminal')
    assert terminal['cumulative_bytes'] == 12 and terminal['prior_bytes'] == 7
    source = json.loads((root/'evidence/source-identity.json').read_text())
    assert source['commit'] == COMMIT and source['tree'] == 'a'*40
    assert (root/'src/CMakeLists.txt').is_file()


def test_fetched_wrong_commit_never_reaches_fsck_archive_or_build(tmp_path, monkeypatch):
    value = acquisition_config(tmp_path, monkeypatch); runner = AcquisitionRunner(Path(value['root']), revision='b'*40)
    with pytest.raises(WorkerFailure):
        run_acquisition(value, Events(), runner=runner)
    assert not any(label in ['source-fsck', 'source-archive', 'configure', 'build'] for _,label,_ in runner.commands)


def test_fetch_failure_is_single_attempt_and_preserves_partial_evidence(tmp_path, monkeypatch):
    value = acquisition_config(tmp_path, monkeypatch); runner = AcquisitionRunner(Path(value['root']), failed='source-fetch')
    events = Events()
    with pytest.raises(WorkerFailure):
        run_acquisition(value, events, runner=runner)
    assert sum(label == 'source-fetch' for _,label,_ in runner.commands) == 1
    assert not any(row['event'] in ('acquisition_terminal', 'phase_complete') for row in events.events)
    assert (Path(value['root'])/'evidence/acquisition-proxy.jsonl').is_file()


def test_missing_proxy_ledger_is_failure_not_zero(tmp_path):
    with pytest.raises(WorkerFailure):
        validate_proxy_terminal(tmp_path / 'missing.jsonl', {}, 0)


@pytest.mark.parametrize('event', ['start', 'unrecognized'])
def test_extra_proxy_ledger_state_cannot_be_silently_ignored(tmp_path, event):
    path = ledger_fixture(tmp_path)
    rows = path.read_text().splitlines()
    rows.insert(-1, json.dumps(dict(event=event, cumulative_bytes=12)))
    path.write_text('\n'.join(rows)+'\n')
    closed = dict(status='meter_closed_unqualified', cleanup_verified=True,
                  cumulative_bytes=12, ledger_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(WorkerFailure):
        validate_proxy_terminal(path, closed, 7)


def test_build_terminal_references_full_manifest_with_bounded_event_size(tmp_path):
    from scripts.uc001_granite_controller.worker import digest
    value = build_config(tmp_path); root = Path(value['root']); events = Events()
    class ManyArtifacts(BuildRunner):
        def run(self, argv, label, env=None, proxy=None):
            result = super().run(argv, label, env, proxy)
            if label == 'build':
                for index in range(100):
                    (self.root/'build/bin'/f'synthetic-library-{index:03d}.dll').write_bytes(b'not executable')
            return result
    run_build(value, events, runner=ManyArtifacts(root))
    terminal = next(row for row in events.events if row['event'] == 'build_terminal')
    manifest = root/'evidence/built-artifacts.json'
    assert len(json.dumps(terminal).encode()) < 4096
    assert 'artifacts' not in terminal
    assert terminal['artifact_manifest_path'] == str(manifest)
    assert terminal['artifact_manifest_sha256'] == digest(manifest)
    assert terminal['artifact_count'] == len(json.loads(manifest.read_text())) == 101
    assert manifest.stat().st_size > 8192
