import copy
import json
from pathlib import Path
import subprocess

import pytest

from scripts.uc001_execution_v1_3_0.run import require_review


REVISION = Path('scripts/uc001_contract_local_v1_1_0')


def prepared():
    from scripts.uc001_contract_local_v1_1_0.capture import load_preparation
    from scripts.uc001_contract_local_v1_1_0.review_gate import require_technical_review
    bundle = load_preparation()
    return bundle, require_technical_review


def test_owner_decision_allows_only_technical_execution_of_unchanged_pending_expectations():
    bundle, gate = prepared()
    review = gate(REVISION / 'partial-expectations-review.json', bundle)
    assert review['status'] == 'pending' and review['expected_meanings_approved'] is False
    assert review['confirmed_cases'] == [2, 5, 10, 11, 12, 13, 14]
    assert review['unapproved_cases'] == [1, 3, 4, 6, 7, 8, 9]
    assert review['freeze_sha256'] == '4a38c66c09c4611530f3290f3d3f3de16fbd7ab2b403b764435d0a598c150079'
    assert review['freeze_sha256'] != bundle['freeze_sha256']
    with pytest.raises(ValueError, match='Qualified expectations review'):
        require_review(REVISION / 'partial-expectations-review.json', bundle['freeze_sha256'])


@pytest.mark.parametrize('change', ['approval', 'status', 'hash', 'unapproved', 'dialect', 'owner'])
def test_gate_rejects_fabricated_approval_or_rewritten_owner_confirmation(tmp_path, change):
    bundle, gate = prepared()
    review = json.loads((REVISION / 'partial-expectations-review.json').read_text())
    if change == 'approval': review['expected_meanings_approved'] = True
    if change == 'status': review['status'] = 'approved'
    if change == 'hash': review['freeze_sha256'] = bundle['freeze_sha256']
    if change == 'unapproved': review['unapproved_cases'] = []
    if change == 'dialect': review['reviewers'][0]['additional_confirmation'] = None
    if change == 'owner': review['reviewers'][0]['github_account'] = 'fabricated'
    path = tmp_path / 'review.json'; path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match='review|confirmation'):
        gate(path, bundle)


@pytest.mark.parametrize('change', ['absent', 'permission', 'semantic', 'reset', 'identity', 'cases', 'review_hash', 'owner'])
def test_gate_requires_bounded_owner_decision_and_exact_input_applicability(change):
    bundle, gate = prepared(); bundle = copy.deepcopy(bundle)
    decision = bundle['technical_decision']
    if change == 'absent': bundle.pop('technical_decision')
    if change == 'permission': decision['technical_execution_permitted'] = False
    if change == 'semantic': decision['semantic_acceptance_permitted'] = True
    if change == 'reset': decision['allowance_reset'] = True
    if change == 'identity': decision['attempt_identity'] = 'other'
    if change == 'cases': decision['unchanged_inputs']['cases.json'] = 'other'
    if change == 'review_hash': decision['partial_review_sha256'] = 'other'
    if change == 'owner': decision['owner'] = {}
    with pytest.raises(ValueError, match='decision|unchanged|review|confirmation'):
        gate(REVISION / 'partial-expectations-review.json', bundle)


def test_launcher_and_capture_cli_use_same_gate_before_assets_or_ledger(monkeypatch, tmp_path):
    from scripts.uc001_contract_local_v1_1_0 import capture
    bundle, _ = prepared()
    calls = []
    monkeypatch.setattr(capture, 'load_preparation', lambda: bundle)
    monkeypatch.setattr(capture, 'verify_windows_environment', lambda: None)
    gate = capture.require_technical_review
    def observed(path, current):
        calls.append(path)
        return gate(path, current)
    monkeypatch.setattr(capture, 'require_technical_review', observed)
    capture.main(['--preflight', '--review', str(REVISION / 'partial-expectations-review.json')])
    with pytest.raises((ValueError, FileNotFoundError)):
        capture.main(['--preflight', '--review', str(tmp_path / 'missing.json')])
    with pytest.raises((ValueError, FileNotFoundError)):
        capture.main(['--supervised-capture', '--review', str(tmp_path / 'missing.json')])
    assert len(calls) == 3
    ps = (REVISION / 'Run-Windows.ps1').read_text()
    assert ps.index('Invoke-LocalPythonPreflight $ReviewPath') < ps.index('Get-ContractAssets $config')
    assert '--preflight --review $ReviewPath' in ps
    assert "'--supervised-capture','--review',$ReviewPath" in ps


def test_capture_rechecks_gate_before_generation_or_budget_creation(tmp_path):
    from scripts.uc001_contract_local_v1_1_0.capture import run_capture
    bundle, _ = prepared()
    with pytest.raises(ValueError, match='review|confirmation'):
        run_capture(bundle, {}, {}, tmp_path, 'synthetic-only-key', None)
    assert not (tmp_path / 'attempts.jsonl').exists()


@pytest.mark.parametrize('case', ['success', 'review_missing', 'existing_attempt', 'late_validation', 'cleanup_failure', 'resource_failure'])
def test_revised_actual_launcher_preserves_supervision_and_abort_paths_offline(case):
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File',
        str(REVISION / 'Test-Offline.ps1'), '-Case', case], capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS ' + case in result.stdout


@pytest.mark.parametrize('mode', ['duplicate', 'envelope', 'case', 'http', 'overflow'])
def test_provisional_expectations_preserve_existing_capture_stop_and_generation_rules(tmp_path, monkeypatch, mode):
    from tests.unit import test_contract_local as checks
    from scripts.uc001_contract_local_v1_1_0 import capture
    for name in ('load_preparation', 'capture_case', 'finalize_export'):
        monkeypatch.setattr(checks, name, getattr(capture, name))
    if mode == 'overflow':
        checks.test_actual_prompt_fit_overflow_does_not_spend_generation(tmp_path)
    else:
        from app.domain.interpretation import ContractViolation
        import httpx
        error = {'duplicate': ContractViolation, 'envelope': ContractViolation, 'case': ValueError, 'http': httpx.HTTPStatusError}[mode]
        checks.test_bad_response_saved_before_shared_failure_and_no_next_generation(tmp_path, mode, error)


def test_revised_supervision_and_model_arguments_remain_unchanged():
    import re
    original = Path('scripts/uc001_contract_local')
    assert (REVISION / 'DeadlineGuard.cs').read_bytes() == (original / 'DeadlineGuard.cs').read_bytes()
    assert (REVISION / 'Test-Offline.ps1').read_bytes() == (original / 'Test-Offline.ps1').read_bytes()
    pattern = r'\$argsList\s*=\s*(@\([\s\S]*?\))\n'
    assert re.search(pattern, (REVISION / 'Run-Windows.ps1').read_text()).group(1) == re.search(pattern, (original / 'Run-Windows.ps1').read_text()).group(1)
    from scripts.uc001_contract_local_v1_1_0.capture import load_preparation
    bundle = load_preparation()
    assert bundle['config']['limits']['startup_count'] == 1
    assert bundle['config']['limits']['generations'] == 14
