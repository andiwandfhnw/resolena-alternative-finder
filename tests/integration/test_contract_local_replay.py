import json
from pathlib import Path
import shutil
from uuid import uuid4

import httpx
import pytest

from app.domain.interpretation import ContractViolation
from scripts.uc001_contract_local.capture import capture_case, finalize_export, load_preparation
from scripts.uc001_contract_local.replay import replay
from scripts.uc001_execution_v1_3_0.controls import RunBudget


KEY = 'synthetic-capture-integration-secret'


def synthetic_packet(case):
    text = case['text']; state = case['allowed_meaning_states'][0]
    recognition = {'status': 'supported', 'language': 'en'} if state == 'understood' else {'status': 'unsupported' if state == 'unsupported' else 'unknown', 'language': None}
    items = []
    if state == 'understood':
        # Deliberately shallow synthetic packet: structural success is not semantics.
        items = [{'id': 's', 'kind': 'subject', 'normalized': 'synthetic subject',
            'span': {'quote': text, 'occurrence': 1}, 'negation': None, 'quantity': None}]
    if case['id'] == 5:
        items = [
            {'id': 's', 'kind': 'subject', 'normalized': 'bicycle', 'span': {'quote': 'bicycle', 'occurrence': 1}, 'negation': None, 'quantity': None},
            {'id': 'a', 'kind': 'action', 'normalized': 'repair', 'span': {'quote': 'repair', 'occurrence': 1}, 'negation': None, 'quantity': None},
            {'id': 'c', 'kind': 'constraint', 'normalized': 'no_replacement', 'span': {'quote': 'without replacing it', 'occurrence': 1}, 'negation': {'quote': 'without', 'occurrence': 1}, 'quantity': None}]
    return {'recognition': recognition, 'meaning_status': state,
        'clauses': [{'span': {'quote': text, 'occurrence': 1}, 'meaning_status': state,
            'normalized': 'Explicit synthetic fixture' if state == 'understood' else None, 'item_ids': [i['id'] for i in items]}],
        'items': items, 'message': None if state == 'understood' else 'Synthetic uncertainty or rephrasing limitation.'}


def captured_all(tmp_path):
    bundle = load_preparation()
    budget = RunBudget(tmp_path/'attempts.jsonl', [c['text'] for c in bundle['cases']['cases']], 10**12)
    for case in bundle['cases']['cases']:
        def handle(request):
            if request.url.path == '/apply-template':
                return httpx.Response(200, json={'prompt': '<|im_start|>synthetic<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'})
            if request.url.path == '/tokenize': return httpx.Response(200, json={'tokens': [1]*200})
            return httpx.Response(200, json={'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(synthetic_packet(case))}}],
                'usage': {'prompt_tokens': 200, 'completion_tokens': 100}})
        capture_case(case, bundle, tmp_path, KEY, budget, transport=httpx.MockTransport(handle))
    finalize_export(tmp_path, bundle)
    assert budget.index == 14
    return tmp_path/'export'


def test_all_exposed_synthetic_captures_replay_api_save_and_policy_without_live_credit(tmp_path, monkeypatch):
    exported = captured_all(tmp_path)
    output = Path('build/test-only') / ('local-replay-test-'+str(uuid4()))
    def no_network(*args, **kwargs): raise AssertionError('Replay attempted a network connection')
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', no_network)
    try:
        result = replay(exported, output)
        assert len(result['cases']) == 14
        assert result['live_api_real_adapter_verified'] is False
        assert result['deferred_live_cases'] == [1, 5, 10]
        assert result['cases'][0]['api_replay']['body']['outcome'] == 'interpretation_unavailable'
        assert result['cases'][4]['api_replay']['body']['outcome'] == 'comparison'
        assert result['cases'][9]['api_replay']['body']['outcome'] == 'clarification_required'
        assert all(c['evidence'] == 'replay_substitute' for c in result['cases'])
        assert all(not c['api_replay']['live_check_satisfied'] for c in result['cases'] if 'api_replay' in c)
        assert result['semantic_review'] == 'pending'
    finally:
        if output.exists(): shutil.rmtree(output)


def test_incomplete_capture_and_failed_native_supervision_cannot_become_replay_success(tmp_path):
    exported = captured_all(tmp_path)
    output = Path('build/test-only') / ('local-replay-test-'+str(uuid4()))
    path = exported/'manifest.json'; manifest=json.loads(path.read_text())
    manifest['cases'][1]['shared_validation_completed'] = False
    path.write_text(json.dumps(manifest))
    try:
        with pytest.raises(ValueError, match='Incomplete/stopped'):
            replay(exported,output)
        assert 'outcome' not in json.loads((output/'replay.json').read_text())
    finally:
        if output.exists(): shutil.rmtree(output)


@pytest.mark.parametrize('change', ['duplicate','missing','wrong_original'])
def test_replay_preserves_original_generation_ledger_semantics(tmp_path,change):
    exported=captured_all(tmp_path)
    path=exported/'attempts.jsonl'; rows=path.read_text().splitlines()
    if change=='duplicate': rows.append(rows[-1])
    if change=='missing': rows.pop()
    if change=='wrong_original':
        first=json.loads(rows[0]);first['case']='invented original';rows[0]=json.dumps(first)
    path.write_text('\n'.join(rows)+'\n')
    with pytest.raises(ValueError,match='generation ledger'):
        replay(exported,Path('build/test-only')/('must-not-create-'+str(uuid4())))


def test_transferred_capture_and_replay_output_share_the_existing_codespace_artifact_cap(tmp_path,monkeypatch):
    import importlib
    module=importlib.import_module('scripts.uc001_contract_local.replay')
    exported=captured_all(tmp_path)
    limit=load_preparation()['config']['limits']['codespace_artifact_bytes']
    monkeypatch.setattr(module,'artifact_bytes',lambda path: limit if Path(path).resolve()==exported.resolve() else 1)
    output=Path('build/test-only')/('local-replay-test-'+str(uuid4()))
    try:
        with pytest.raises(ValueError,match='artifact sub-budget'):
            replay(exported,output)
    finally:
        if output.exists():shutil.rmtree(output)
