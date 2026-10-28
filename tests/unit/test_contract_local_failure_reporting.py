from pathlib import Path
import subprocess

import pytest


ROOT = Path('scripts/uc001_contract_local_v1_2_1')


@pytest.mark.parametrize('case', [
    'primary_cleanup', 'identified_before_proof', 'identified_exit_unconfirmed',
    'primary_cleanup_deadline', 'private_error', 'private_code_error', 'wrapped_native_error', 'success', 'membership_failure',
    'cleanup_failure', 'job_close_failure', 'deadline', 'layout',
])
@pytest.mark.parametrize('root', [ROOT, Path('scripts/uc001_contract_local_v1_2_2')])
def test_independent_failure_reporting_and_strict_cleanup_offline(case, root):
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File',
        str(root / 'Test-Offline.ps1'), '-Case', case], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS ' + case in result.stdout


def test_binding_retains_only_unique_verified_interpreter_before_complete_proof():
    code = (ROOT / 'PythonOwnership.cs').read_text()
    unique = code.index('Require(members.Length==(serverPid==0?2:3)')
    retained = code.index('InterpreterIdentity=child;Interpreter=candidate')
    supervisor = code.index('using(Process supervisor=Process.GetProcessById(supervisorPid))')
    completed = code.index('LastProof=new Ownership')
    assert unique < retained < supervisor < completed
    assert 'Member(process,job)' in code and 'Require(candidate==null,"interpreter_ambiguous")' in code


REVISION = Path('scripts/uc001_contract_local_v1_2_2')


@pytest.mark.parametrize('case', [
    'role_helper_pending', 'role_helper_interpreter', 'role_helper_python_parent',
    'role_no_helper', 'role_wrong_path', 'role_unknown', 'role_ambiguous',
    'role_bad_parent', 'role_bad_time', 'role_duplicate_helper', 'role_reused_helper',
    'role_wrong_python', 'helper_success',
    'helper_cleanup_partial', 'helper_cleanup_unconfirmed', 'helper_missing_identity',
    'helper_unknown_member', 'helper_deadline',
])
def test_console_roles_and_cleanup_with_explicit_offline_substitutes(case):
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File',
        str(REVISION / 'Test-Offline.ps1'), '-Case', case], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS ' + case in result.stdout


@pytest.mark.parametrize('change', [None, 'python_parent', 'wrong_path', 'basename', 'parent',
    'time', 'reused', 'missing_member', 'extra_member', 'duplicate', 'no_python', 'bool_pid'])
def test_python_validates_console_role_and_exact_membership(change):
    import copy
    import importlib
    from tests.unit.test_contract_local_harness_correction import ownership
    checks = importlib.import_module('scripts.uc001_contract_local_v1_2_2.harness_checks')
    proof = ownership()
    helper = {'pid': 400, 'parent_pid': 200, 'created': 2500, 'image': r'C:\Windows\System32\conhost.exe'}
    proof['console_helpers'] = [helper]
    proof['job_verified_pids'].append(400)
    if change == 'python_parent': helper.update(parent_pid=300, created=3500)
    if change == 'wrong_path': helper['image'] = r'C:\other\conhost.exe'
    if change == 'basename': helper['image'] = 'conhost.exe'
    if change == 'parent': helper['parent_pid'] = 999
    if change == 'time': helper['created'] = 1500
    if change == 'missing_member': proof['job_verified_pids'].remove(400)
    if change == 'extra_member': proof['job_verified_pids'].append(999)
    if change == 'duplicate': proof['console_helpers'].append(copy.deepcopy(helper))
    if change == 'no_python': proof['interpreter'] = None
    if change == 'bool_pid': helper['pid'] = True
    live = {row['pid']: copy.deepcopy(row) for row in [proof['supervisor'], proof['redirector'], helper, *([proof['interpreter']] if proof['interpreter'] else [])]}
    if change == 'reused': live[400]['created'] += 1
    kwargs = dict(reader=lambda pid: live[pid], self_pid=300, self_parent=200,
        system_directory=lambda: r'C:\Windows\System32')
    if change in (None, 'python_parent'):
        checks.verify_python_ownership(proof, **kwargs)
    else:
        with pytest.raises(ValueError): checks.verify_python_ownership(proof, **kwargs)


def test_native_dispatch_accounts_and_retains_roles_without_fixed_member_total():
    code = (REVISION / 'PythonOwnership.cs').read_text()
    bind = code[code.index('public Ownership Bind('):code.index('public static ContractPython Start(')]
    assert 'Roles roles=AccountMembers(' in bind
    assert 'Member(process,job)' in bind and 'Same(value,Read(process))' in bind
    assert 'helpers.Add(new Helper {identity=value,process=process})' in bind
    assert bind.index('helpers.Add(') < bind.index('if(roles.interpreter==null)') < bind.index('LastProof=new Ownership')
    assert 'members.Length==' not in bind
    assert 'freshMembers.SetEquals(memberSet)' in bind
    assert 'Member(helper.process,job)' in bind and 'Same(helper.identity,current)' in bind
    assert 'Environment.GetFolderPath(Environment.SpecialFolder.System)' in code


def test_new_revision_still_rejects_model_capture_without_writing_attempt(tmp_path):
    import importlib
    module = importlib.import_module('scripts.uc001_contract_local_v1_2_2.capture')
    with pytest.raises(ValueError, match='allowance_consumed'):
        module.run_capture({}, {}, {}, tmp_path, '', None)
    assert not list(tmp_path.iterdir())
    command = ". ./scripts/uc001_contract_local_v1_2_2/Run-Windows.ps1; try {Invoke-LocalExecution 'unused';throw 'incorrect'} catch {if($_.Exception.Message -notmatch 'allowance_consumed'){throw}}; exit 0"
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
