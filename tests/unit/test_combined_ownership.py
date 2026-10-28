"""Synthetic ownership data only; Windows combined reproduction remains owner-run."""

from pathlib import Path
import subprocess

import pytest


SOURCE = Path('scripts/uc001_combined_ownership')


@pytest.mark.parametrize('case', ['combined_rejected', 'server_parent_rejected', 'unexpected_rejected',
    'retained_before_classification', 'partial_cleanup', 'unknown_cleanup', 'missing_identity',
    'missing_handle', 'foreign_job', 'unconfirmed_exit', 'approved_cleanup', 'primary_cleanup_deadline', 'missing_server_identity', 'production_dispatch'])
def test_combined_retention_and_strict_reproduction_offline(case):
    result = subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File',
        'tests/support/uc001_combined_offline.ps1','-Case',case],capture_output=True,text=True,timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS '+case in result.stdout


def test_policy_not_relaxed_without_actual_windows_branch_evidence():
    code = (SOURCE/'PythonOwnership.cs').read_text()
    original = Path('scripts/uc001_contract_local_v1_3_0/PythonOwnership.cs').read_text()
    start='    public static Roles AccountMembers('
    assert code[code.index(start):code.index('    public Ownership Bind(')] == original[original.index(start):original.index('    public Ownership Bind(')]
    assert (SOURCE/'harness_checks.py').read_bytes() == Path('scripts/uc001_contract_local_v1_3_0/harness_checks.py').read_bytes()


def test_frozen_cleanup_reproduces_lost_observed_handles_with_same_synthetic_fixture():
    result = subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File',
        'tests/support/uc001_combined_offline.ps1','-Case','partial_cleanup','-LegacyCleanup'],capture_output=True,text=True,timeout=20)
    assert result.returncode != 0
    assert 'Observed handles lost when role classification failed' in result.stderr


@pytest.mark.parametrize('two_helpers', [False, True])
def test_python_branch_policy_also_stays_closed_pending_windows_evidence(two_helpers):
    import importlib
    from tests.unit.test_contract_local_harness_correction import ownership
    checks = importlib.import_module('scripts.uc001_contract_local_v1_3_0.harness_checks')
    proof = ownership(); proof['server_pid'] = 101
    proof['console_helpers'] = [{'pid':501, 'parent_pid':101, 'created':1500, 'image':r'C:\Windows\System32\conhost.exe'}]
    if two_helpers: proof['console_helpers'].append({'pid':401, 'parent_pid':200, 'created':2500, 'image':r'C:\Windows\System32\conhost.exe'})
    proof['job_verified_pids'] = [101,200,300,501] + ([401] if two_helpers else [])
    identities = [proof['supervisor'],proof['redirector'],proof['interpreter'],*proof['console_helpers']]
    live = {row['pid']:row for row in identities}
    with pytest.raises(ValueError, match='identity_mismatch'):
        checks.verify_python_ownership(proof, reader=lambda pid:live[pid],self_pid=300,self_parent=200,system_directory=lambda:r'C:\Windows\System32')


# Explicit synthetic topology derived from the owner-reported combined Windows check.
CORRECTED = Path('scripts/uc001_combined_ownership_v1_1_0')
SHELL = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'


def combined_proof():
    from tests.unit.test_contract_local_harness_correction import ownership
    proof = ownership()
    proof.update(server={'pid':101,'created':1500,'parent_pid':100,'image':SHELL}, server_pid=101,
        console_helpers=[{'pid':501,'created':1600,'parent_pid':101,'image':r'C:\Windows\System32\conhost.exe'},
            {'pid':401,'created':2500,'parent_pid':200,'image':r'C:\Windows\System32\conhost.exe'}],
        job_verified_pids=[101,200,300,401,501])
    return proof


def corrected_checks():
    import importlib
    return importlib.import_module('scripts.uc001_combined_ownership_v1_1_0.harness_checks')


def validate_combined(proof, live=None):
    identities = [proof[key] for key in ('supervisor','server','redirector','interpreter') if key in proof] + proof['console_helpers']
    if live is None: live={p['pid']:p for p in identities}
    corrected_checks().verify_python_ownership(proof, reader=lambda pid:live[pid],self_pid=300,self_parent=200,
        system_directory=lambda:r'C:\Windows\System32', server_executable=SHELL)


def test_python_accepts_one_exact_helper_per_fully_verified_branch():
    validate_combined(combined_proof())


@pytest.mark.parametrize('change',['wrong_parent','supervisor_parent','server_path','server_parent','server_time',
    'server_reused','server_missing','server_pid_only','helper_path','helper_time','duplicate_branch',
    'unknown_member','missing_member','duplicate_member','ambiguous_interpreter','stale_job'])
def test_python_rejects_incorrect_combined_proof(change):
    import copy
    proof=combined_proof()
    if change=='wrong_parent': proof['console_helpers'][0]['parent_pid']=999
    if change=='supervisor_parent': proof['console_helpers'][0]['parent_pid']=100
    if change=='server_path': proof['server']['image']=r'C:\elsewhere\powershell.exe'
    if change=='server_parent': proof['server']['parent_pid']=99
    if change=='server_time': proof['server']['created']=500
    if change=='server_pid_only': proof.pop('server')
    if change=='helper_path': proof['console_helpers'][0]['image']=r'C:\fake\conhost.exe'
    if change=='helper_time': proof['console_helpers'][0]['created']=1000
    if change=='duplicate_branch': proof['console_helpers'][0]['parent_pid']=300;proof['console_helpers'][0]['created']=3500
    if change=='unknown_member': proof['job_verified_pids'].append(999)
    if change=='missing_member': proof['job_verified_pids'].remove(101)
    if change=='duplicate_member': proof['job_verified_pids'].append(101)
    if change=='ambiguous_interpreter': proof['interpreter']['pid']=301;proof['job_verified_pids'].append(301)
    if change=='stale_job': proof['job_membership_verified']=False
    live={p['pid']:copy.deepcopy(p) for key in ('supervisor','server','redirector','interpreter') if (p:=proof.get(key))}
    live.update({p['pid']:copy.deepcopy(p) for p in proof['console_helpers']})
    if change=='server_reused': live[101]['created']=1550
    if change=='server_missing': live.pop(101)
    with pytest.raises(ValueError,match='identity_mismatch'): validate_combined(proof,live)


@pytest.mark.parametrize('case',['combined','helper_before_interpreter','python_interpreter_parent',
    'wrong_parent','wrong_path','unknown','ambiguous_python','duplicate_branch','server_parent','server_path','server_time',
    'partial_cleanup','combined_cleanup','unconfirmed_exit','missing_identity','both_validators','validator_failure','deadline_failure','primary_cleanup_deadline'])
def test_corrected_combined_native_and_supervision_offline(case):
    result=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File',
        'tests/support/uc001_combined_branches_offline.ps1','-Case',case],capture_output=True,text=True,timeout=25)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'PASS '+case in result.stdout


@pytest.mark.parametrize('bad_server',[False, True])
def test_actual_worker_uses_actual_python_validator_with_combined_proof(tmp_path,monkeypatch,bad_server):
    import importlib
    import io
    import json
    worker=importlib.import_module('scripts.uc001_combined_ownership_v1_1_0.idle')
    proof=combined_proof();live={p['pid']:p.copy() for p in [proof[k] for k in ('supervisor','server','redirector','interpreter')]+proof['console_helpers']}
    if bad_server: live[101]['parent_pid']=999
    calls=[];actual=corrected_checks().verify_python_ownership
    def check(value,*,server_executable):
        calls.append(value)
        actual(value,reader=lambda pid:live[pid],self_pid=300,self_parent=200,
            system_directory=lambda:r'C:\Windows\System32',server_executable=server_executable)
    monkeypatch.setattr(worker,'verify_python_ownership',check)
    monkeypatch.setattr(worker,'windows_system_directory',lambda:r'C:\Windows\System32')
    monkeypatch.setattr(worker.sys,'stdin',io.StringIO(json.dumps(proof)+'\n\n'))
    worker.run(tmp_path/'ready.json',tmp_path/'python-result.json')
    result=json.loads((tmp_path/'python-result.json').read_text())
    assert calls==[proof]
    assert result['outcome']==('failed' if bad_server else 'python_combined_ownership_verified')
    if bad_server: assert result['failure']['stage']=='ownership'
    else: assert result['proof']==proof and result['validator']=='verify_python_ownership'


def test_corrected_check_and_native_bind_preserve_production_dispatch_and_freshness():
    ps=(CORRECTED/'Check-CombinedOwnership.ps1').read_text()
    native=(CORRECTED/'PythonOwnership.cs').read_text()
    bridge=(CORRECTED/'Python-Ownership.ps1').read_text()
    assert 'Start-ContractProcess $job' in ps and 'Start-OwnedPython $job' in ps
    assert 'Get-OwnedPythonProof $launch $job $PID $server $serverIdentity (Get-CombinedShell)' in ps
    assert "$stage='python_validation'" in ps and "$stage='final_native_validation'" in ps
    assert ps.index('$launch.StandardInput.WriteLine($proofText)') < ps.index("$stage='final_native_validation'") < ps.index('Complete-OwnedPythonCleanup $null')
    assert 'ReadInJob(server,job)' in native and 'Same(current,expectedServer)' in native
    assert 'Same(ServerIdentity,ReadInJob(server,job))' in native and 'Members(job)' in native
    assert 'Observe(job,serverPid)' in native and 'observations.Add(record)' in native
    assert 'helpers.Count==0' not in native and 'consoles.Count<=1' not in native
    assert 'branches.Add(branch)' in native
    assert '$Launch.Bind($Job,$SupervisorId,$Server,$ServerIdentity,$ServerPath)' in bridge
    assert 'llama-server.exe' not in ps


def test_owner_transcript_stays_failed_while_its_topology_is_tested_explicitly():
    import copy
    import json
    evidence=Path('build/uc001-combined-ownership-v1_1_0/owner-evidence')
    historical=json.loads((evidence/'result.owner-pasted.json').read_text())
    cleanup=json.loads((evidence/'cleanup.owner-pasted.json').read_text())
    observed=json.loads((evidence/'observation.owner-pasted.json').read_text())
    assert historical['observation']==observed
    assert historical['outcome']=='failed' and historical['cleanup_confirmed'] is False and historical['ownership'] is None
    assert cleanup['errors']==['cleanup/interpreter_not_identified']
    assert len({p['pid'] for p in cleanup['owned_exits'] if p['exit_confirmed']})==5
    assert cleanup['owned_exits'][2]['pid'] is None and not cleanup['owned_exits'][2]['exit_confirmed']
    # Explicit test-only proof assembled from observations; never written as historical evidence.
    proof={key:copy.deepcopy(observed[key]) for key in ('supervisor','server','redirector')}
    rows=[copy.deepcopy(row['identity']) for row in observed['observed_members']]
    proof.update(interpreter=rows[2],console_helpers=rows[:2],server_pid=proof['server']['pid'],
        job_membership_verified=True,job_verified_pids=observed['job_member_pids'])
    live={p['pid']:p for p in [proof[k] for k in ('supervisor','server','redirector','interpreter')]+proof['console_helpers']}
    corrected_checks().verify_python_ownership(proof,reader=lambda pid:live[pid],self_pid=proof['interpreter']['pid'],
        self_parent=proof['redirector']['pid'],system_directory=lambda:r'C:\Windows\System32',server_executable=SHELL)
    import importlib
    with pytest.raises(ValueError,match='identity_mismatch'):
        importlib.import_module('scripts.uc001_combined_ownership.harness_checks').verify_python_ownership(
            proof,reader=lambda pid:live[pid],self_pid=proof['interpreter']['pid'],self_parent=proof['redirector']['pid'],
            system_directory=lambda:r'C:\Windows\System32')
