import copy
import importlib
import json
from pathlib import Path
import subprocess

import pytest

from tests.unit.test_contract_run_controls import effective, LOG


REVISION = Path('scripts/uc001_contract_local_v1_2_0')
VENV = r'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe'
BASE = r'C:\ResolenaExperiments\tools\python-3.12.10\python.exe'


def functions():
    return importlib.import_module('scripts.uc001_contract_local_v1_2_0.harness_checks')


def ownership():
    return {'supervisor': {'pid': 100, 'created': 1000, 'parent_pid': 99, 'image': r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'},
        'redirector': {'pid': 200, 'created': 2000, 'parent_pid': 100, 'image': VENV},
        'interpreter': {'pid': 300, 'created': 3000, 'parent_pid': 200, 'image': BASE},
        'job_verified_pids': [200, 300], 'job_membership_verified': True}


def test_verified_venv_redirector_chain_replaces_direct_parent_assumption():
    checks = functions(); proof = ownership()
    live = {row['pid']: row for row in (proof['supervisor'], proof['redirector'], proof['interpreter'])}
    assert proof['interpreter']['parent_pid'] != proof['supervisor']['pid']
    checks.verify_python_ownership(proof, reader=lambda pid: live[pid], self_pid=300, self_parent=200)


@pytest.mark.parametrize('change', ['pid', 'reused_pid', 'ancestor', 'image', 'base', 'order', 'job', 'missing_member', 'extra_member', 'unavailable'])
def test_ownership_rejects_unverified_lifetime_chain_or_job(change):
    checks=functions(); proof=ownership(); live={row['pid']:copy.deepcopy(row) for row in (proof['supervisor'],proof['redirector'],proof['interpreter'])}
    if change=='pid': proof['interpreter']['pid']=301
    if change=='reused_pid': live[200]['created']=2500
    if change=='ancestor': live[200]['parent_pid']=99
    if change=='image': live[200]['image']=BASE
    if change=='base': live[300]['image']=r'C:\unrelated\python.exe'
    if change=='order': proof['redirector']['created']=4000;live[200]['created']=4000
    if change=='job': proof['job_membership_verified']=False
    if change=='missing_member': proof['job_verified_pids']=[200]
    if change=='extra_member': proof['job_verified_pids'].append(999)
    if change=='unavailable': live.pop(200)
    with pytest.raises(ValueError): checks.verify_python_ownership(proof,reader=lambda pid:live[pid],self_pid=300,self_parent=200)


def test_pinned_reported_default_requires_separate_cli_and_request_limit_evidence():
    checks=functions(); props=effective();props['default_generation_settings']['params']['n_predict']=-1
    props['default_generation_settings']['params'].update(temperature=0.699999988079071,top_p=0.800000011920929)
    result=checks.verify_effective(props,LOG,['--predict','3072'],{'max_tokens':3072})
    assert result['reported_task_default']==-1 and result['request_limit']==result['cli_limit']==3072
    with pytest.raises(ValueError): checks.verify_effective(props,LOG,None,{'max_tokens':3072})
    with pytest.raises(ValueError): checks.verify_effective(props,LOG,['--predict','3072'],None)


@pytest.mark.parametrize('change', ['reported', 'missing', 'cli_unlimited', 'cli_high', 'cli_duplicate', 'request_unlimited', 'request_high', 'request_alias', 'bool', 'sampling', 'runtime'])
def test_output_limit_and_all_other_settings_remain_strict(change):
    checks=functions(); props=effective();props['default_generation_settings']['params']['n_predict']=-1
    args=['--predict','3072'];body={'max_tokens':3072}
    if change=='reported':props['default_generation_settings']['params']['n_predict']=3072
    if change=='missing':props['default_generation_settings']['params'].pop('n_predict')
    if change=='cli_unlimited':args[-1]='-1'
    if change=='cli_high':args[-1]='4096'
    if change=='cli_duplicate':args+=['--n-predict','3072']
    if change=='request_unlimited':body['max_tokens']=-1
    if change=='request_high':body['max_tokens']=4096
    if change=='request_alias':body['n_predict']=-1
    if change=='bool':body['max_tokens']=True
    if change=='sampling':props['default_generation_settings']['params']['temperature']=0
    if change=='runtime':props['build_info']='different'
    with pytest.raises(ValueError):checks.verify_effective(props,LOG,args,body)


def test_saved_receipt_check_does_not_invent_cli_or_generation_evidence():
    checks=functions();props=effective();props['default_generation_settings']['params']['n_predict']=-1
    result=checks.check_saved_receipt({'props':props,'startup_log':LOG})
    assert result['saved_report_compatible'] is True
    assert result['cli_execution_verified'] is False and result['model_readiness_verified'] is False
    assert result['request_limit_code']==3072 and result['generation_evidence']=='unavailable'


def test_consumed_startup_blocks_capture_before_ledger_or_model(tmp_path):
    module=importlib.import_module('scripts.uc001_contract_local_v1_2_0.capture')
    with pytest.raises(ValueError,match='allowance_consumed'):
        module.run_capture({}, {}, {}, tmp_path, '', None)
    assert not list(tmp_path.iterdir())
    command=". ./scripts/uc001_contract_local_v1_2_0/Run-Windows.ps1; try {Invoke-LocalExecution 'unused';throw 'incorrect'} catch {if($_.Exception.Message -notmatch 'allowance_consumed'){throw}}; exit 0"
    result=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr


def test_stop_record_uses_only_fixed_stage_reason_codes():
    checks=functions()
    error=checks.HarnessStop('ownership','identity_mismatch')
    assert checks.stop_record(error)=={'stage':'ownership','reason':'identity_mismatch','type':'HarnessStop'}
    assert checks.stop_record(ValueError('synthetic secret, raw prompt and credentials'))=={'stage':'unknown','reason':'unexpected_failure','type':'ValueError'}


def test_legacy_guards_reproduce_both_assumptions_with_explicit_synthetic_inputs(tmp_path,monkeypatch):
    from datetime import datetime,timezone
    import time
    from scripts.uc001_contract_local_v1_1_0 import capture as legacy
    from scripts.uc001_execution_v1_3_0.controls import verify_effective as legacy_settings
    bundle=legacy.load_preparation()
    review=json.loads(Path('scripts/uc001_contract_local_v1_1_0/partial-expectations-review.json').read_text())
    now=datetime.now(timezone.utc).isoformat()
    receipt={'started_utc':now,'total_started_utc':now,'freeze_sha256':bundle['freeze_sha256'],
        'authentication_verified':True,'supervisor_pid':100,'receipt_epoch':time.time()}
    monkeypatch.setattr(legacy.os,'getppid',lambda:200)
    with pytest.raises(ValueError,match='owned-supervisor'):
        legacy.run_capture(bundle,review,receipt,tmp_path,'explicit-synthetic-key-32-characters',None)
    assert not (tmp_path/'attempts.jsonl').exists()
    props=effective();props['default_generation_settings']['params']['n_predict']=-1
    with pytest.raises(ValueError,match='sampling/output mismatch: n_predict'):
        legacy_settings(props,LOG)


def test_new_collector_calls_corrected_checks_and_enforces_actual_request_limit(tmp_path):
    import httpx
    module=importlib.import_module('scripts.uc001_contract_local_v1_2_0.capture')
    calls=[]
    with httpx.Client(transport=module.CaptureTransport(tmp_path/'private',tmp_path/'export','explicit-synthetic-secret',
            transport=httpx.MockTransport(lambda request:calls.append(request))),trust_env=False) as client:
        with pytest.raises(ValueError,match='request_limit_mismatch'):
            client.post('http://127.0.0.1:49188/v1/chat/completions',json={'max_tokens':4096})
    assert not calls and (tmp_path/'private/001/request.bin').exists()
    code=(REVISION/'capture.py').read_text()
    assert "verify_python_ownership(receipt['python_ownership'])" in code
    assert code.count("receipt['launch_args'], adapter_limit_body()") == 2
    native=(REVISION/'PythonOwnership.cs').read_text()
    assert native.index('Require(AssignProcessToJobObject(job,created.Process)') < native.index('Require(ResumeThread(created.Thread)')
    assert '0x08080404' in native and 'UpdateProcThreadAttribute' in native


@pytest.mark.parametrize('valid_cleanup',[True,False])
def test_revised_replay_requires_interpreter_exit_identity_without_live_credit(tmp_path,monkeypatch,valid_cleanup):
    import httpx
    import shutil
    from uuid import uuid4
    from tests.integration import test_contract_local_replay as fixture
    capture=importlib.import_module('scripts.uc001_contract_local_v1_2_0.capture')
    replay=importlib.import_module('scripts.uc001_contract_local_v1_2_0.replay')
    for name in ('load_preparation','capture_case','finalize_export'):
        monkeypatch.setattr(fixture,name,getattr(capture,name))
    exported=fixture.captured_all(tmp_path)
    # Explicit fabricated supervision/cleanup fixture exercises replay's native-evidence branch only.
    path=exported/'manifest.json';manifest=json.loads(path.read_text());manifest['classification']='owner_operated_windows_capture';path.write_text(json.dumps(manifest))
    for source,target in [('partial-expectations-review.json','review.json'),('technical-decision.json','technical-decision.json')]:
        shutil.copyfile(REVISION/source,exported/target)
    (exported/'supervision.json').write_text(json.dumps({'completed':True}))
    (exported/'cleanup.json').write_text(json.dumps({'owned_job_closed':True,'errors':[],
        'owned_exits':[{'pid':50,'exit_confirmed':True},{'pid':200,'exit_confirmed':True,'created':2000},
        {'pid':300,'exit_confirmed':True,'created':3000 if valid_cleanup else 3001}]}))
    (exported/'windows-receipt.json').write_text(json.dumps({'owned_pid':50,'python_ownership':ownership()}))
    for number in range(1,15):(exported/f'accepted-{number:02}.json').write_text(json.dumps({'case':number,'elapsed_ms':100}))
    def no_network(*args,**kwargs):raise AssertionError('Replay network fallback')
    monkeypatch.setattr(httpx.HTTPTransport,'handle_request',no_network)
    output=Path('build/test-only')/('harness-correction-replay-'+str(uuid4()))
    try:
        if valid_cleanup:
            result=replay.replay(exported,output)
            assert result['technical_result']=='passed' and result['semantic_review']=='pending'
            assert result['live_api_real_adapter_verified'] is False and result['deferred_live_cases']==[1,5,10]
        else:
            with pytest.raises(ValueError,match='cleanup identities'):replay.replay(exported,output)
    finally:
        if output.exists():shutil.rmtree(output)


@pytest.mark.parametrize('case',['success','wrong_identity','membership_failure','worker_failure','cleanup_failure','job_close_failure','deadline','layout'])
def test_model_free_corrected_ownership_and_cleanup_paths_with_explicit_substitutes(case):
    result=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File',str(REVISION/'Test-Offline.ps1'),'-Case',case],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'PASS '+case in result.stdout
