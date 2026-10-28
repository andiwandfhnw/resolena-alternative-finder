from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess
import zipfile

import pytest


ROOT = Path('scripts/uc001_execution_v1_3_0')
BUILD = Path('build/uc001-execution-v1_3_0')
PWSH = shutil.which('pwsh')


@pytest.mark.skipif(PWSH is None, reason='PowerShell absent; execution monitor remains unverified')
@pytest.mark.parametrize('case', [
    'owned_zero', 'owned_valid', 'foreign_rows', 'owned_missing', 'owned_duplicate', 'owned_other_pid', 'owned_other_luid',
    'owned_lookalike', 'owned_phys1', 'owned_multiple_phys', 'owned_null', 'owned_string', 'owned_negative', 'owned_fraction',
    'owned_capacity', 'query_failed', 'rss_null', 'rss_string', 'rss_negative', 'rss_capacity', 'process_exited', 'process_exits_during_sample',
    'process_pid_changes', 'process_start_changes', 'pid_invalid', 'adapter_luid_changes', 'adapter_pci_changes', 'adapter_capacity_changes',
    'ram_invalid', 'ram_bounds', 'disk_invalid', 'disk_bounds', 'gpu_missing', 'gpu_duplicate', 'gpu_negative',
    'flow_missing', 'flow_capacity', 'flow_zero', 'flow_resource_floor', 'flow_cleanup_unconfirmed', 'flow_client_cleanup_error', 'flow_job_close_failed', 'flow_existing_attempt',
    'flow_startup_identity', 'flow_runtime_identity', 'cleanup_two_owned',
])
def test_execution_monitor_offline(case):
    result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-File', str(ROOT/'Test-Monitor.ps1'), '-Case', case], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'PASS {case}' in result.stdout


def test_execution_bundle_preserves_originals_and_fixed_inputs():
    for name in ('config.json','runtime-files.json','prompt.txt','schema.json','cases.json','review-template.json','ProcessTools.cs','controls.py','development.py'):
        assert (ROOT/name).read_bytes() == (Path('scripts/uc001_contract_check')/name).read_bytes(), name
    assert (ROOT/'AdapterIdentity.cs').read_bytes() == (Path('scripts/uc001_preflight_capacity_v1_2_0')/'AdapterIdentity.cs').read_bytes()
    for name,expected in json.loads((BUILD/'baseline.json').read_text()).items():
        assert sha256(Path(name).read_bytes()).hexdigest()==expected,name


def test_execution_bundle_freeze_and_attempt_identity():
    from scripts.uc001_execution_v1_3_0.controls import load_bundle
    bundle=load_bundle(ROOT)
    assert bundle['freeze']['version']=='uc001-execution-v1.3.0'
    assert bundle['freeze']['attempt_identity']=='bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52'
    with zipfile.ZipFile(BUILD/'windows-execution-v1_3_0.zip') as package:
        assert package.testzip() is None
        assert set(package.namelist())==set(bundle['freeze']['files'])|{'freeze.json'}
        for name in package.namelist():
            assert package.read(name)==(ROOT/name).read_bytes(),name


def test_execution_runner_default_and_qualified_review_gate_are_preserved():
    from scripts.uc001_execution_v1_3_0.run import require_review
    with pytest.raises(ValueError, match='Qualified expectations review'):
        require_review(ROOT/'review-template.json','a'*64)
    result=subprocess.run(['.venv/bin/python','-m','scripts.uc001_execution_v1_3_0.run'],capture_output=True,text=True)
    assert result.returncode==2 and '--execute' in result.stderr


@pytest.mark.skipif(PWSH is None, reason='PowerShell absent; Windows no-execute gate unverified')
def test_windows_launcher_without_execute_starts_nothing():
    result=subprocess.run([PWSH,'-NoProfile','-NonInteractive','-File',str(ROOT/'Run-Windows.ps1'),'-Codespace','offline'],capture_output=True,text=True)
    assert result.returncode!=0 and 'separate owner authorization' in result.stderr


OWNERSHIP_ROOT = Path('scripts/uc001_native_ownership_check')


@pytest.mark.skipif(PWSH is None, reason='PowerShell absent; diagnostic remains unverified')
@pytest.mark.parametrize('case', [
    'owned_abort', 'start_failed', 'pid_changed', 'creation_changed', 'identity_failed',
    'job_close_failed', 'exit_unconfirmed', 'dispose_failed', 'worker_deadline',
    'supervisor_timeout', 'supervisor_exit_unconfirmed', 'recover_owned',
    'recover_wrong_creation', 'missing_child_identity', 'bad_worker_receipt',
    'supervisor_success', 'supervisor_identity_failed', 'cleanup_receipt_mismatch', 'deadline_boundaries',
    'recover_query_failed', 'recover_pid_absent',
])
def test_native_ownership_diagnostic_offline(case):
    result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-File',
        str(OWNERSHIP_ROOT/'Test-Offline.ps1'), '-Case', case], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'PASS {case}' in result.stdout


def test_native_ownership_diagnostic_preserves_existing_work():
    for name, expected in json.loads(Path('build/uc001-native-ownership-check/baseline.json').read_text()).items():
        assert sha256(Path(name).read_bytes()).hexdigest() == expected, name


@pytest.mark.skipif(PWSH is None, reason='PowerShell absent; offline syntax/gate unchecked')
def test_native_ownership_diagnostic_syntax_and_non_windows_gate():
    script = r'''
    Get-ChildItem scripts/uc001_native_ownership_check/*.ps1 | ForEach-Object {
        $tokens=$null; $errors=$null
        $null=[Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors)
        if($errors.Count){throw $errors[0]}
    }
    '''
    result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    # Core pwsh fails the actual Desktop/64-bit gate before any diagnostic child/job starts.
    result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-File', str(OWNERSHIP_ROOT/'Check-NativeOwnership.ps1'),
        '-BundleDirectory', str(ROOT.resolve())], capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    assert '64-bit Windows PowerShell 5.1' in json.loads(result.stdout)['error']
    assert not (OWNERSHIP_ROOT/'results').exists()


def test_native_ownership_diagnostic_package_is_separate_and_complete():
    artifact = Path('build/uc001-native-ownership-check/windows-native-ownership-check.zip')
    with zipfile.ZipFile(artifact) as package:
        assert package.testzip() is None
        assert set(package.namelist()) == {'Check-NativeOwnership.ps1', 'README.md'}
        for name in package.namelist():
            assert package.read(name) == (OWNERSHIP_ROOT/name).read_bytes()
