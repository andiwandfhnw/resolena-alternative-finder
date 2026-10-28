import importlib
import json
from pathlib import Path
import shutil
from uuid import uuid4

import httpx
import pytest

from tests.integration import test_contract_local_replay as original_fixture


@pytest.fixture
def technical_capture(tmp_path, monkeypatch):
    from scripts.uc001_contract_local_v1_1_0 import capture
    for name in ('load_preparation', 'capture_case', 'finalize_export'):
        monkeypatch.setattr(original_fixture, name, getattr(capture, name))
    exported = original_fixture.captured_all(tmp_path)
    # Explicit synthetic fixture exercising the owner-capture replay branch only.
    manifest_path = exported / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['classification'] = 'owner_operated_windows_capture'
    manifest_path.write_text(json.dumps(manifest))
    source = Path('scripts/uc001_contract_local_v1_1_0')
    shutil.copyfile(source / 'partial-expectations-review.json', exported / 'review.json')
    shutil.copyfile(source / 'technical-decision.json', exported / 'technical-decision.json')
    (exported / 'supervision.json').write_text(json.dumps({'completed': True}))
    (exported / 'cleanup.json').write_text(json.dumps({'owned_job_closed': True, 'errors': [],
        'owned_exits': [{'exit_confirmed': True}, {'exit_confirmed': True}]}))
    for case_id in range(1, 15):
        (exported / f'accepted-{case_id:02}.json').write_text(json.dumps({'case': case_id, 'elapsed_ms': 100}))
    return exported


def test_pending_review_technical_replay_separates_structure_provisional_policy_and_acceptance(technical_capture, monkeypatch):
    module = importlib.import_module('scripts.uc001_contract_local_v1_1_0.replay')
    gate = module.require_technical_review
    observed = []
    def recording_gate(path, bundle):
        observed.append(path)
        return gate(path, bundle)
    monkeypatch.setattr(module, 'require_technical_review', recording_gate)
    def no_network(*args, **kwargs): raise AssertionError('Network fallback attempted')
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', no_network)
    output = Path('build/test-only') / ('technical-replay-' + str(uuid4()))
    try:
        result = module.replay(technical_capture, output)
        assert observed == [technical_capture.resolve() / 'review.json']
        assert result['technical_result'] == 'passed'
        assert result['provisional_policy_result'] == 'passed'
        assert result['semantic_review'] == 'pending'
        assert result['expected_meanings_approved'] is False
        assert result['interpreter_suitability_verified'] is False
        assert result['multilingual_acceptance_verified'] is False
        assert result['live_api_real_adapter_verified'] is False
        assert result['deferred_live_cases'] == [1, 5, 10]
        assert len(result['cases']) == 14
        assert all(item['evidence'] == 'replay_substitute' for item in result['cases'])
        assert all(item['policy_expectations'] == 'provisional' for item in result['cases'])
        case = json.loads((technical_capture / 'cases/09/result.json').read_text())
        assert case['technical_validation'] == 'passed'
        assert case['provisional_case_check'] == 'passed'
        assert case['expected_meanings_approved'] is False
    finally:
        if output.exists(): shutil.rmtree(output)


@pytest.mark.parametrize('change', ['review', 'decision', 'supervision', 'cleanup', 'case', 'manifest'])
def test_technical_permission_does_not_bypass_review_provenance_or_existing_replay_stops(technical_capture, change):
    from scripts.uc001_contract_local_v1_1_0.replay import replay
    if change == 'review':
        path = technical_capture / 'review.json'; data = json.loads(path.read_text()); data['expected_meanings_approved'] = True
    elif change == 'decision':
        path = technical_capture / 'technical-decision.json'; data = json.loads(path.read_text()); data['allowance_reset'] = True
    elif change == 'supervision':
        path = technical_capture / 'supervision.json'; data = {'completed': False}
    elif change == 'cleanup':
        path = technical_capture / 'cleanup.json'; data = {'owned_job_closed': False, 'errors': [], 'owned_exits': []}
    elif change == 'manifest':
        path = technical_capture / 'manifest.json'; data = json.loads(path.read_text()); data['expected_meanings_approved'] = True
    else:
        path = technical_capture / 'manifest.json'; data = json.loads(path.read_text()); data['cases'][8]['shared_validation_completed'] = False
    path.write_text(json.dumps(data))
    output = Path('build/test-only') / ('technical-replay-' + str(uuid4()))
    try:
        with pytest.raises(ValueError): replay(technical_capture, output)
        if (output / 'replay.json').exists():
            summary = json.loads((output / 'replay.json').read_text())
            assert summary['technical_result'] != 'passed'
            assert summary['semantic_review'] == 'pending'
    finally:
        if output.exists(): shutil.rmtree(output)
