import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.uc001_granite_controller.worker import (
    COMMIT, GIT, CMAKE, NINJA, CL, SDK, CEILING, WorkerFailure,
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
    def __init__(self, root, revision=COMMIT, failed=None, journal=None):
        self.root, self.revision, self.failed = root, revision, failed
        self.journal=journal or Events()
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
        from scripts.uc001_granite_controller.worker import Child
        assert label == 'proxy' and stdin
        self.commands.append((argv, label, env))
        assert argv[argv.index('--acquisition-started-utc')+1] == '2026-10-25T12:00:00+00:00'
        ledger = self.root / 'evidence/acquisition-proxy.jsonl'
        self.ready_value = dict(pid=700, proxy_url='http://127.0.0.1:12345', ledger=str(ledger),
                                prior_bytes=7, remaining_bytes=10737418240-7)
        records = [dict(event='start', cumulative_bytes=7, prior_bytes=7),
                   dict(event='listening',pid=700,cumulative_bytes=7),
                   dict(event='debit', cumulative_bytes=12, bytes_read=5,
                        tunnel_id='1', destination='github.com:443', tunnel_bytes=5),
                   dict(event='end', cumulative_bytes=12, status='closed_unqualified', sockets_closed=True)]
        ledger.write_text(''.join(json.dumps(x)+'\n' for x in records))
        self.api=ProxyApi(split=False)
        identity=dict(pid=700,creation_time_100ns=900,parent_pid=42,in_any_job=True)
        process=SimpleNamespace(pid=700,_handle='launcher',stdin=ProxyInput(),
            poll=lambda:self.api.rows['launcher']['exit'],wait=lambda:self.api.rows['launcher']['exit'])
        out_path=self.root/'evidence/proxy.stdout.log';out=out_path.open('xb')
        err_path=self.root/'evidence/proxy.stderr.log';err=err_path.open('xb')
        self.proxy=Child(process,'proxy',out_path,err_path,out,err,identity)
        self.journal.emit('proxy_launcher_started',schema=1,launcher=identity)
        return self.proxy
    def ready(self, proxy):
        assert proxy is self.proxy
        return self.ready_value
    def bind_proxy(self,proxy,ready):
        from io import BytesIO
        from scripts.uc001_granite_controller.worker import NativeRunner
        self.native=NativeRunner(self.root,self.journal,{},api=self.api,control=BytesIO(b'PROXY_BOUND\n'))
        return self.native.bind_proxy(proxy,ready)
    def mark_proxy_closing(self,proxy):self.native.mark_proxy_closing(proxy)
    def close_proxy_handles(self,proxy):
        if hasattr(self,'native'):self.native.close_proxy_handles(proxy)
        else:close_fixture(proxy)
    def wait(self, proxy):
        assert proxy is self.proxy
        assert proxy.process.stdin.value == b'CLOSE\n'
        ledger = self.root / 'evidence/acquisition-proxy.jsonl'
        closed = dict(status='meter_closed_unqualified', cleanup_verified=True,
                      cumulative_bytes=12, ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest())
        proxy.stdout_file.write((json.dumps(self.ready_value)+'\n'+json.dumps(closed)+'\n').encode())
        proxy.stdout_file.flush()
        for row in self.api.rows.values():row['exit']=0
        return self.native.wait(proxy)


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
    events = Events();runner = AcquisitionRunner(root,journal=events)
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
    assert terminal['proxy_identity_schema']==1
    assert terminal['proxy_launcher_pid']==700 and terminal['proxy_interpreter_pid']==700
    assert 'proxy_pid' not in terminal
    assert any(row['event']=='proxy_binding_requested' for row in events.events)
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


class ProxyApi:
    def __init__(self,split=True):
        from types import SimpleNamespace
        self.rows={'launcher':dict(pid=700,birth=900,parent=42,member=True,exit=None)}
        if split:self.rows['interpreter']=dict(pid=701,birth=901,parent=700,member=True,exit=None)
        self.opened=[];self.closed=[]
        self.k=SimpleNamespace(IsProcessInJob=self.any_job)
    def checked(self,value,operation):
        if not value:raise WorkerFailure(operation)
        return value
    def any_job(self,handle,job,pointer):
        assert job is None
        pointer._obj.value=int(self.rows[handle]['member'])
        return 1
    def process_id(self,handle):return self.rows[handle]['pid']
    def creation_time(self,handle):return self.rows[handle]['birth']
    def parent_pid(self,handle):return self.rows[handle]['parent']
    def exit_code(self,handle):return self.rows[handle]['exit']
    def open_process(self,pid,can_terminate=False):
        assert can_terminate is False
        self.opened.append(pid)
        for name,row in self.rows.items():
            if row['pid']==pid:return name
        raise WorkerFailure('unknown readiness pid')
    def close_handle(self,handle):self.closed.append(handle)


def proxy_binding_fixture(tmp_path,*,split=True,ack=b'PROXY_BOUND\n'):
    from io import BytesIO
    from types import SimpleNamespace
    from scripts.uc001_granite_controller.worker import NativeRunner,Child
    root=tmp_path/'binding';(root/'evidence').mkdir(parents=True)
    api=ProxyApi(split);events=Events()
    process=SimpleNamespace(pid=700,_handle='launcher',stdin=ProxyInput(),
        poll=lambda:api.rows['launcher']['exit'],wait=lambda:api.rows['launcher']['exit'])
    out_path=root/'evidence/proxy.stdout.log';out=out_path.open('wb')
    err_path=root/'evidence/proxy.stderr.log';err=err_path.open('wb')
    identity=dict(pid=700,creation_time_100ns=900,parent_pid=42,in_any_job=True)
    proxy=Child(process,'proxy',out_path,err_path,out,err,identity)
    runner=NativeRunner(root,events,{},api=api,control=BytesIO(ack),sleep=lambda _:None)
    ready=dict(pid=701 if split else 700,proxy_url='http://127.0.0.1:12345',
               ledger=str(root/'evidence/ledger.jsonl'),prior_bytes=7,remaining_bytes=CEILING-7)
    return runner,proxy,api,events,ready


def close_fixture(proxy):
    for stream in (proxy.stdout_file,proxy.stderr_file):
        if not stream.closed:stream.close()


@pytest.mark.parametrize('split',[True,False])
def test_proxy_identity_binding_split_and_native_same_handle_proof(tmp_path,split):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path,split=split)
    try:
        binding=runner.bind_proxy(proxy,ready)
        assert binding['schema']==1
        assert binding['launcher']['pid']==700
        assert binding['interpreter']['pid']==(701 if split else 700)
        assert binding['same_process'] is (not split)
        assert api.opened==([701] if split else [])
        assert [row['event'] for row in events.events]==['proxy_binding_requested']
        assert events.events[0]['ready_pid']==ready['pid']
        runner.check_proxy(proxy)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)
    assert api.closed==(['interpreter'] if split else [])


@pytest.mark.parametrize('damage',['wrong_pid','wrong_parent','wrong_member','forged_same_birth'])
def test_proxy_identity_readiness_cannot_bind_unverified_process(tmp_path,damage):
    split=damage!='forged_same_birth'
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path,split=split)
    if damage=='wrong_pid':ready['pid']=999
    elif damage=='wrong_parent':api.rows['interpreter']['parent']=123
    elif damage=='wrong_member':api.rows['interpreter']['member']=False
    else:api.rows['launcher']['birth']=999
    try:
        with pytest.raises(WorkerFailure):runner.bind_proxy(proxy,ready)
        assert not any(row['event']=='proxy_listening' for row in events.events)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


def test_proxy_identity_controller_ack_is_mandatory_before_fetch_use(tmp_path):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path,ack=b'WRONG\n')
    try:
        with pytest.raises(WorkerFailure):runner.bind_proxy(proxy,ready)
        with pytest.raises(WorkerFailure):runner.check_proxy(proxy)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


@pytest.mark.parametrize('role,field,value',[
    ('interpreter','pid',702),('interpreter','birth',999),
    ('interpreter','parent',123),('interpreter','member',False),
    ('launcher','birth',999),
])
def test_proxy_identity_revalidation_rejects_pid_birth_parent_membership_change(tmp_path,role,field,value):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path)
    try:
        runner.bind_proxy(proxy,ready)
        api.rows[role][field]=value
        with pytest.raises(WorkerFailure):runner.check_proxy(proxy)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


@pytest.mark.parametrize('role',['launcher','interpreter'])
def test_proxy_identity_both_roles_are_checked_for_premature_exit(tmp_path,role):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path)
    try:
        runner.bind_proxy(proxy,ready)
        api.rows[role]['exit']=0
        with pytest.raises(WorkerFailure):runner.check_proxy(proxy)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


@pytest.mark.parametrize('split',[True,False])
def test_proxy_identity_cleanup_emits_two_retained_role_exits(tmp_path,split):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path,split=split)
    try:
        runner.bind_proxy(proxy,ready)
        proxy.stdout_file.write((json.dumps(ready)+'\n{}\n').encode());proxy.stdout_file.flush()
        runner.mark_proxy_closing(proxy)
        for row in api.rows.values():row['exit']=0
        runner.wait(proxy)
        exits=[row for row in events.events if row['event'].endswith('_exit')]
        assert [row['event'] for row in exits]==['proxy_interpreter_exit','proxy_launcher_exit']
        assert all(row['identity_verified'] and row['exit_code']==0 for row in exits)
        assert exits[0]['identity']['pid']==(701 if split else 700)
        assert exits[1]['identity']['pid']==700
        assert not any(row['event']=='child_exit' for row in events.events)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


def test_proxy_identity_launcher_exit_without_interpreter_exit_fails_cleanup(tmp_path):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path)
    try:
        runner.bind_proxy(proxy,ready);runner.mark_proxy_closing(proxy)
        api.rows['launcher']['exit']=0
        with pytest.raises(WorkerFailure):runner.wait(proxy)
        assert not any(row['event']=='proxy_interpreter_exit' for row in events.events)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


@pytest.mark.parametrize('pid',[700,999])
def test_proxy_identity_terminal_ledger_rejects_launcher_or_unbound_listening_pid(tmp_path,pid):
    path=ledger_fixture(tmp_path)
    rows=path.read_text().splitlines()
    rows.insert(1,json.dumps(dict(event='listening',pid=pid,cumulative_bytes=7)))
    path.write_text('\n'.join(rows)+'\n')
    closed=dict(status='meter_closed_unqualified',cleanup_verified=True,cumulative_bytes=12,
                ledger_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(WorkerFailure):validate_proxy_terminal(path,closed,7,expected_pid=701)


def test_proxy_identity_terminal_ledger_matches_executing_interpreter_pid(tmp_path):
    path=ledger_fixture(tmp_path)
    rows=path.read_text().splitlines()
    rows.insert(1,json.dumps(dict(event='listening',pid=701,cumulative_bytes=7)))
    path.write_text('\n'.join(rows)+'\n')
    closed=dict(status='meter_closed_unqualified',cleanup_verified=True,cumulative_bytes=12,
                ledger_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    assert validate_proxy_terminal(path,closed,7,expected_pid=701)==12


def test_proxy_identity_start_records_launcher_role_without_generic_child_event(tmp_path,monkeypatch):
    from io import BytesIO
    from types import SimpleNamespace
    from scripts.uc001_granite_controller import worker
    root=tmp_path/'start';(root/'evidence').mkdir(parents=True)
    api=ProxyApi();events=Events()
    process=SimpleNamespace(pid=700,_handle='launcher',stdin=ProxyInput())
    monkeypatch.setattr(worker.os,'getpid',lambda:42)
    monkeypatch.setattr(worker.subprocess,'Popen',lambda *args,**kwargs:process)
    runner=worker.NativeRunner(root,events,{},api=api,control=BytesIO(b'PROXY_BOUND\n'))
    proxy=runner.start(['synthetic-python','accepted-proxy.py'],'proxy',stdin=True)
    try:
        assert [row['event'] for row in events.events]==['proxy_launcher_started']
        assert events.events[0]['launcher']==proxy.identity
    finally:runner.close_proxy_handles(proxy)


def test_proxy_identity_interpreter_exit_without_launcher_exit_cannot_finish(tmp_path):
    runner,proxy,api,events,ready=proxy_binding_fixture(tmp_path)
    def deadline(_):raise WorkerFailure('synthetic controller deadline')
    runner.sleep=deadline
    try:
        runner.bind_proxy(proxy,ready);runner.mark_proxy_closing(proxy)
        api.rows['interpreter']['exit']=0
        with pytest.raises(WorkerFailure):runner.wait(proxy)
        assert not any(row['event']=='proxy_launcher_exit' for row in events.events)
    finally:
        runner.close_proxy_handles(proxy);close_fixture(proxy)


@pytest.mark.parametrize('role',['launcher','interpreter'])
def test_proxy_identity_premature_exit_cannot_be_published_as_planned_close(tmp_path,monkeypatch,role):
    value=acquisition_config(tmp_path,monkeypatch);events=Events()
    class Premature(AcquisitionRunner):
        def start(self,*args,**kwargs):
            child=super().start(*args,**kwargs)
            self.api=ProxyApi(split=True)
            self.ready_value['pid']=701
            ledger=self.root/'evidence/acquisition-proxy.jsonl'
            rows=[json.loads(line) for line in ledger.read_text().splitlines()]
            for row in rows:
                if row['event']=='listening':row['pid']=701
            ledger.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            return child
        def run(self,argv,label,env=None,proxy=None):
            result=super().run(argv,label,env,proxy)
            if label=='source-fetch':self.api.rows[role]['exit']=0
            return result
    runner=Premature(Path(value['root']),journal=events)
    with pytest.raises(WorkerFailure):run_acquisition(value,events,runner=runner)
    assert not any(row['event']=='proxy_closing' for row in events.events)


def test_proxy_identity_ledger_boolean_pid_cannot_equal_integer_identity(tmp_path):
    path=ledger_fixture(tmp_path)
    rows=path.read_text().splitlines()
    rows.insert(1,json.dumps(dict(event='listening',pid=True,cumulative_bytes=7)))
    path.write_text('\n'.join(rows)+'\n')
    closed=dict(status='meter_closed_unqualified',cleanup_verified=True,cumulative_bytes=12,
                ledger_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(WorkerFailure):validate_proxy_terminal(path,closed,7,expected_pid=1)
