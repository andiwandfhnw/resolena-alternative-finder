"""Explicit synthetic approvals/processes/responses; no Windows/model execution."""

import copy
import importlib
import io
import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path('scripts/uc001_contract_local_v1_3_0')


def module(name):
    return importlib.import_module('scripts.uc001_contract_local_v1_3_0.' + name)


def prepared():
    return module('capture').load_preparation()


def synthetic_approval(bundle):
    value = json.loads((ROOT / 'approval.pending.json').read_text())
    value.update(approved=True, freeze_sha256=bundle['freeze_sha256'], approval_reference='EXPLICIT SYNTHETIC OFFLINE FIXTURE; no owner approval')
    return value


@pytest.mark.parametrize('change', ['pending', 'missing', 'identity', 'original', 'proposal', 'freeze', 'startups', 'bool_startup', 'generations', 'reset', 'semantic', 'reference'])
def test_pending_or_mismatched_approval_cannot_grant_new_allowance(change):
    gate = module('execution_gate')
    bundle = prepared()
    value = synthetic_approval(bundle)
    if change == 'pending': value['approved'] = False
    if change == 'missing': value = None
    if change == 'identity': value['attempt_identity'] = bundle['freeze']['original_attempt_identity']
    if change == 'original': value['original_attempt_identity'] = 'other'
    if change == 'proposal': value['proposal_sha256'] = 'other'
    if change == 'freeze': value['freeze_sha256'] = 'other'
    if change == 'startups': value['additional_startups'] = 2
    if change == 'bool_startup': value['additional_startups'] = True
    if change == 'generations': value['generations'] = 15
    if change == 'reset': value['allowance_reset'] = True
    if change == 'semantic': value['purpose'] = 'semantic_acceptance'
    if change == 'reference': value['approval_reference'] = None
    with pytest.raises(ValueError, match='approval'):
        gate.verify_execution_approval(value, bundle)
    assert json.loads((ROOT / 'approval.pending.json').read_text())['approved'] is False


def test_new_identity_links_consumed_original_without_rewriting_review_or_settings():
    bundle = prepared()
    gate = module('execution_gate')
    gate.verify_execution_approval(synthetic_approval(bundle), bundle)
    assert bundle['freeze']['attempt_identity'] != bundle['freeze']['original_attempt_identity']
    assert bundle['freeze']['original_startup_allowance_consumed'] is True
    old = Path('scripts/uc001_contract_local_v1_2_2')
    for name in ('PythonOwnership.cs', 'Python-Ownership.ps1', 'harness_checks.py', 'DeadlineGuard.cs', 'partial-expectations-review.json', 'previous-freeze.json', 'technical-decision.json'):
        assert (ROOT / name).read_bytes() == (old / name).read_bytes()
    assert module('review_gate').require_technical_review(ROOT / 'partial-expectations-review.json', bundle)['expected_meanings_approved'] is False
    assert bundle['config']['limits']['startup_count'] == 1 and bundle['config']['limits']['generations'] == 14


@pytest.mark.parametrize('field,value', [('status', 'approved'), ('expected_meanings_approved', True), ('unapproved_cases', [])])
def test_additional_attempt_cannot_rewrite_pending_linguistic_confirmation(field, value):
    bundle = prepared()
    review = json.loads((ROOT / 'partial-expectations-review.json').read_text())
    review[field] = value
    with pytest.raises(ValueError, match='review|confirmation'):
        module('review_gate').verify_technical_review(review, bundle)


def test_capture_cli_blocks_unapproved_execution_before_stdin_or_attempt(monkeypatch, tmp_path):
    capture = module('capture')
    monkeypatch.setattr(capture, 'verify_windows_environment', lambda: None)
    monkeypatch.setattr(capture.sys, 'stdin', None)
    with pytest.raises(ValueError, match='approval'):
        capture.main(['--supervised-capture', '--approval', str(ROOT / 'approval.pending.json'),
            '--review', str(ROOT / 'partial-expectations-review.json'), '--run-root', str(tmp_path)])
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('mode', ['complete', 'case_failure', 'settings_failure', 'pending'])
def test_actual_capture_uses_corrected_settings_order_validation_and_prospective_ledger(tmp_path, monkeypatch, mode):
    import time
    from datetime import datetime, timezone
    import httpx
    from tests.unit.test_contract_run_controls import effective, LOG
    capture = module('capture'); bundle = prepared()
    props = effective(); props['default_generation_settings']['params']['n_predict'] = -1
    if mode == 'settings_failure': props['default_generation_settings']['params']['top_k'] = 21
    now = datetime.now(timezone.utc).isoformat()
    receipt = dict(freeze_sha256=bundle['freeze_sha256'], attempt_identity=bundle['freeze']['attempt_identity'],
        original_attempt_identity=bundle['freeze']['original_attempt_identity'],
        started_utc=now, total_started_utc=now, receipt_epoch=time.time(), authentication_verified=True,
        python_ownership={'classification': 'explicit_synthetic_native_proof'}, props=props,
        startup_log=LOG, launch_args=['--predict', '3072'])
    key = 'explicit-synthetic-key-never-a-credential'
    monkeypatch.setattr(capture, 'verify_python_ownership', lambda proof: None)
    monkeypatch.setattr(capture, 'verify_authentication', lambda client: None)
    client = httpx.Client(base_url='http://127.0.0.1:49188', transport=httpx.MockTransport(lambda request: httpx.Response(200, json=props)))
    monkeypatch.setattr(capture.httpx, 'Client', lambda **kwargs: client)
    phases = []
    real_write = capture.write_json
    def observed_write(path, value):
        if Path(path).name == 'progress.json': phases.append((value['case'], value['phase']))
        real_write(path, value)
    monkeypatch.setattr(capture, 'write_json', observed_write)
    generated = []
    def synthetic_case(case, bundle, root, key, budget):
        budget.consume(case['text']); generated.append(case['id'])
        if mode == 'case_failure': raise ValueError('Explicit synthetic case-state validation failure')
    monkeypatch.setattr(capture, 'capture_case', synthetic_case)
    approval = synthetic_approval(bundle)
    if mode == 'pending': approval['approved'] = False
    commands = io.StringIO(''.join(f'begin {i}\nadvance {i}\n' for i in range(1, 15)))
    review = json.loads((ROOT / 'partial-expectations-review.json').read_text())
    if mode == 'complete': capture.run_capture(bundle, review, receipt, tmp_path, key, commands, approval)
    else:
        with pytest.raises(ValueError): capture.run_capture(bundle, review, receipt, tmp_path, key, commands, approval)
    ledger = tmp_path / 'attempts.jsonl'
    if mode in ('settings_failure', 'pending'):
        assert not ledger.exists() and not generated
    else:
        rows = [json.loads(line) for line in ledger.read_text().splitlines()]
        count = 14 if mode == 'complete' else 1
        assert generated == list(range(1, count + 1))
        assert [row['case'] for row in rows] == [c['text'] for c in bundle['cases']['cases'][:count]]
        assert [i for i, phase in phases if phase == 'validated'] == (list(range(1, 15)) if mode == 'complete' else [])


@pytest.mark.parametrize('case', ['success', 'approval_pending', 'existing_attempt', 'resource_failure', 'settings_worker_stop', 'late_validation', 'cleanup_failure'])
def test_actual_launcher_wires_owned_capture_deadlines_and_cleanup_with_substitutes(case):
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File',
        'tests/support/uc001_additional_launcher.ps1', '-Case', case], capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS ' + case in result.stdout


@pytest.mark.parametrize('broken', [False, True])
def test_replay_accounts_helper_cleanup_without_live_credit(tmp_path, monkeypatch, broken):
    import shutil
    from uuid import uuid4
    from tests.integration import test_contract_local_replay as fixture
    from tests.unit.test_contract_local_harness_correction import ownership
    capture, replay = module('capture'), module('replay')
    for name in ('load_preparation', 'capture_case', 'finalize_export'): monkeypatch.setattr(fixture, name, getattr(capture, name))
    exported = fixture.captured_all(tmp_path)
    path = exported / 'manifest.json'; manifest = json.loads(path.read_text()); manifest['classification'] = 'owner_operated_windows_capture'; path.write_text(json.dumps(manifest))
    for source, target in [('partial-expectations-review.json', 'review.json'), ('technical-decision.json', 'technical-decision.json')]: shutil.copyfile(ROOT / source, exported / target)
    (exported / 'execution-approval.json').write_text(json.dumps(synthetic_approval(prepared())))
    (exported / 'supervision.json').write_text(json.dumps({'completed': True}))
    proof = ownership(); proof['console_helpers'] = [{'pid': 400, 'created': 2500, 'parent_pid': 200, 'image': r'C:\Windows\System32\conhost.exe'}]
    (exported / 'windows-receipt.json').write_text(json.dumps({'owned_pid': 50, 'python_ownership': proof}))
    (exported / 'cleanup.json').write_text(json.dumps({'owned_job_closed': True, 'errors': [], 'unidentified_job_pids': [],
        'owned_exits': [{'pid': 50, 'exit_confirmed': True}, {'pid': 200, 'created': 2000, 'role': 'redirector', 'exit_confirmed': True},
            {'pid': 300, 'created': 3000, 'role': 'interpreter', 'exit_confirmed': True},
            {'pid': 400, 'created': 2500, 'role': 'console_helper', 'exit_confirmed': not broken}]}))
    for i in range(1,15): (exported / f'accepted-{i:02}.json').write_text(json.dumps({'case': i, 'elapsed_ms': 100}))
    output = Path('build/test-only') / ('additional-replay-' + str(uuid4()))
    try:
        if broken:
            with pytest.raises(ValueError, match='cleanup'): replay.replay(exported, output)
        else:
            result = replay.replay(exported, output)
            assert result['semantic_review'] == 'pending' and result['expected_meanings_approved'] is False
            assert result['deferred_live_cases'] == [1,5,10] and result['live_api_real_adapter_verified'] is False
    finally:
        if output.exists(): shutil.rmtree(output)


CORRECTED_ROOT = Path('scripts/uc001_contract_local_v1_4_0')


def corrected_module(name):
    return importlib.import_module('scripts.uc001_contract_local_v1_4_0.'+name)


def corrected_prepared():
    return corrected_module('capture').load_preparation()


def corrected_approval(bundle):
    value=json.loads((CORRECTED_ROOT/'approval.pending.json').read_text())
    value.update(approved=True,freeze_sha256=bundle['freeze_sha256'],approval_reference='EXPLICIT SYNTHETIC OFFLINE FIXTURE; no owner approval')
    return value


def corrected_proof():
    from tests.unit.test_combined_ownership import combined_proof
    proof=combined_proof();proof['server']['image']=r'C:\ResolenaExperiments\qwen3-8b-v1\runtime\llama-server.exe'
    return proof


def test_corrected_capture_imports_windows_verified_policy_in_its_own_package():
    capture=corrected_module('capture')
    assert capture.verify_python_ownership.__module__=='scripts.uc001_contract_local_v1_4_0.harness_checks'


@pytest.mark.parametrize('case',['success','approval_pending','existing_attempt','resource_failure','settings_worker_stop','late_validation','cleanup_failure','binding_partial'])
def test_corrected_actual_launcher_with_full_server_both_helpers_and_cleanup(case):
    result=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File','tests/support/uc001_additional_launcher.ps1','-Corrected','-Case',case],capture_output=True,text=True,timeout=25)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'PASS '+case in result.stdout


@pytest.mark.parametrize('mode',['complete','server_path','server_pid','server_created','case_failure','pending'])
def test_corrected_actual_capture_validates_full_server_before_any_generation(tmp_path,monkeypatch,mode):
    import time
    from datetime import datetime,timezone
    import httpx
    from tests.unit.test_contract_run_controls import effective,LOG
    capture=corrected_module('capture');bundle=corrected_prepared();checks=corrected_module('harness_checks')
    proof=corrected_proof();live={p['pid']:p.copy() for p in [proof[k] for k in ('supervisor','server','redirector','interpreter')]+proof['console_helpers']}
    props=effective();props['default_generation_settings']['params']['n_predict']=-1
    now=datetime.now(timezone.utc).isoformat()
    receipt=dict(freeze_sha256=bundle['freeze_sha256'],attempt_identity=bundle['freeze']['attempt_identity'],
        original_attempt_identity=bundle['freeze']['original_attempt_identity'],previous_attempt_identity=bundle['freeze']['previous_attempt_identity'],
        started_utc=now,total_started_utc=now,receipt_epoch=time.time(),authentication_verified=True,
        owned_pid=101,owned_created=1500,python_ownership=proof,props=props,startup_log=LOG,launch_args=['--predict','3072'])
    if mode=='server_path':proof['server']['image']=r'C:\fake\llama-server.exe';live[101]['image']=proof['server']['image']
    if mode=='server_pid':receipt['owned_pid']=102
    if mode=='server_created':receipt['owned_created']=1501
    calls=[]
    def live_validator(value,**kwargs):
        calls.append(kwargs)
        checks.verify_python_ownership(value,reader=lambda pid:live[pid],self_pid=300,self_parent=200,
            system_directory=lambda:r'C:\Windows\System32',**kwargs)
    monkeypatch.setattr(capture,'verify_python_ownership',live_validator)
    monkeypatch.setattr(capture,'verify_authentication',lambda client:None)
    client=httpx.Client(base_url='http://127.0.0.1:49188',transport=httpx.MockTransport(lambda request:httpx.Response(200,json=props)))
    monkeypatch.setattr(capture.httpx,'Client',lambda **kwargs:client)
    generated=[]
    def synthetic_case(case,bundle,root,key,budget):
        budget.consume(case['text']);generated.append(case['id'])
        if mode=='case_failure':raise ValueError('Explicit synthetic case failure')
    monkeypatch.setattr(capture,'capture_case',synthetic_case)
    approval=corrected_approval(bundle)
    if mode=='pending':approval['approved']=False
    review=json.loads((CORRECTED_ROOT/'partial-expectations-review.json').read_text())
    commands=io.StringIO(''.join(f'begin {i}\nadvance {i}\n' for i in range(1,15)))
    try:
        if mode=='complete':capture.run_capture(bundle,review,receipt,tmp_path,'explicit-synthetic-key-never-a-credential',commands,approval)
        else:
            with pytest.raises(ValueError):capture.run_capture(bundle,review,receipt,tmp_path,'explicit-synthetic-key-never-a-credential',commands,approval)
    finally:client.close()
    if mode=='complete':
        assert calls==[{'server_executable':r'C:\ResolenaExperiments\qwen3-8b-v1\runtime\llama-server.exe'}]
        assert generated==list(range(1,15))
    elif mode=='case_failure':assert generated==[1]
    else:assert not generated and not (tmp_path/'attempts.jsonl').exists()


@pytest.mark.parametrize('change',[None,'pending','previous','identity','allowance','freeze'])
def test_corrected_approval_links_both_consumed_allowances_without_reset(change):
    bundle=corrected_prepared();gate=corrected_module('execution_gate');value=corrected_approval(bundle)
    if change=='pending':value['approved']=False
    if change=='previous':value['previous_attempt_identity']='other'
    if change=='identity':value['attempt_identity']=bundle['freeze']['previous_attempt_identity']
    if change=='allowance':value['additional_startups']=2
    if change=='freeze':value['freeze_sha256']='other'
    if change is None:
        assert gate.verify_execution_approval(value,bundle)==value
        assert len(set([bundle['freeze'][k] for k in ('attempt_identity','original_attempt_identity','previous_attempt_identity')]))==3
        assert bundle['freeze']['previous_startup_allowance_consumed'] is True
    else:
        with pytest.raises(ValueError,match='approval'):gate.verify_execution_approval(value,bundle)
    assert json.loads((CORRECTED_ROOT/'approval.pending.json').read_text())['approved'] is False


@pytest.mark.parametrize('change',[None,'server_path','server_created','helper_parent','helper_exit','unknown','server_pid_only'])
def test_corrected_actual_replay_requires_full_server_and_two_branch_cleanup(tmp_path,monkeypatch,change):
    import shutil
    from uuid import uuid4
    import httpx
    from tests.integration import test_contract_local_replay as fixture
    capture,replay=corrected_module('capture'),corrected_module('replay')
    for name in ('load_preparation','capture_case','finalize_export'):monkeypatch.setattr(fixture,name,getattr(capture,name))
    exported=fixture.captured_all(tmp_path)
    path=exported/'manifest.json';manifest=json.loads(path.read_text());manifest['classification']='owner_operated_windows_capture';path.write_text(json.dumps(manifest))
    for name,target in [('partial-expectations-review.json','review.json'),('technical-decision.json','technical-decision.json')]:shutil.copyfile(CORRECTED_ROOT/name,exported/target)
    (exported/'execution-approval.json').write_text(json.dumps(corrected_approval(corrected_prepared())))
    (exported/'supervision.json').write_text(json.dumps({'completed':True}))
    proof=corrected_proof();identities=[proof[k] for k in ('server','redirector','interpreter')]+proof['console_helpers']
    exits=[dict(pid=p['pid'],created=p['created'],role=('console_helper' if i>2 else ('server','redirector','interpreter')[i]),exit_confirmed=True) for i,p in enumerate(identities)]
    if change=='server_path':proof['server']['image']=r'C:\fake\llama-server.exe'
    if change=='server_created':exits[0]['created']=1501
    if change=='helper_parent':proof['console_helpers'][0]['parent_pid']=999
    if change=='helper_exit':exits[3]['exit_confirmed']=False
    if change=='unknown':exits.append(dict(pid=999,created=3500,exit_confirmed=True))
    if change=='server_pid_only':proof.pop('server')
    (exported/'windows-receipt.json').write_text(json.dumps(dict(owned_pid=101,owned_created=1500,python_ownership=proof)))
    (exported/'cleanup.json').write_text(json.dumps(dict(owned_job_closed=True,errors=[],unidentified_job_pids=[],owned_exits=exits)))
    for i in range(1,15):(exported/f'accepted-{i:02}.json').write_text(json.dumps(dict(case=i,elapsed_ms=100)))
    monkeypatch.setattr(httpx.HTTPTransport,'handle_request',lambda *args,**kwargs:pytest.fail('Replay network fallback'))
    output=Path('build/test-only')/('corrected-replay-'+str(uuid4()))
    try:
        if change is not None:
            with pytest.raises(ValueError):replay.replay(exported,output)
        else:
            summary=replay.replay(exported,output)
            assert summary['ownership_evidence']=='recorded_identity_consistency_only'
            assert summary['live_api_real_adapter_verified'] is False and summary['deferred_live_cases']==[1,5,10]
            assert summary['expected_meanings_approved'] is False and summary['semantic_review']=='pending'
    finally:
        if output.exists():shutil.rmtree(output)


def test_corrected_helpers_inputs_review_and_limits_match_frozen_predecessors():
    bundle=corrected_prepared()
    for name in ('PythonOwnership.cs','Python-Ownership.ps1','harness_checks.py','DeadlineGuard.cs'):
        assert (CORRECTED_ROOT/name).read_bytes()==(Path('scripts/uc001_combined_ownership_v1_1_0')/name).read_bytes()
    for name in ('partial-expectations-review.json','previous-freeze.json','technical-decision.json'):
        assert (CORRECTED_ROOT/name).read_bytes()==(ROOT/name).read_bytes()
    launch=(CORRECTED_ROOT/'Run-Windows.ps1').read_text()
    old_launch=(ROOT/'Run-Windows.ps1').read_text()
    assert launch[launch.index('        $argsList ='):launch.index("        $stage='startup'")] == old_launch[old_launch.index('        $argsList ='):old_launch.index("        $stage='startup'")]
    old=prepared()
    assert bundle['config']==old['config'] and bundle['cases']==old['cases'] and bundle['prompt']==old['prompt']
    assert corrected_module('review_gate').require_technical_review(CORRECTED_ROOT/'partial-expectations-review.json',bundle)['expected_meanings_approved'] is False


@pytest.mark.parametrize('case',['matching','mismatched','extra_file','reuse_approval','pending_approval'])
def test_corrected_actual_windows_handoff_reuse_controls_offline(case):
    result=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File','tests/support/uc001_execution_handoff.ps1','-Case',case],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'PASS '+case in result.stdout
