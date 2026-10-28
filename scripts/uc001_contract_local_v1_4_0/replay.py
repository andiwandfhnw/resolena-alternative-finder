"""Explicit test-substitute replay only; never a live API/real-adapter check."""

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]

import httpx

from app.domain.interpretation import LanguageOutcome, apply_language_policy
from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter, strict_json
from scripts.uc001_contract_local_v1_4_0.capture import LIMIT, load_preparation, write_json
from scripts.uc001_execution_v1_3_0.controls import check_case_state
from scripts.uc001_contract_local_v1_4_0.review_gate import require_technical_review, review_status
from scripts.uc001_contract_local_v1_4_0.ownership_receipts import verify_recorded_cleanup
from scripts.uc001_contract_local_v1_4_0.execution_gate import require_execution_approval


def artifact_bytes(directory):
    return sum(p.stat().st_size for p in Path(directory).rglob('*') if p.is_file())


def replay_case(case, bundle, exported):
    frozen = next(c for c in bundle['cases']['cases'] if c['id'] == case['id'])
    if case != frozen:
        raise ValueError('Replay must preserve the exact frozen case and original')
    root = Path(exported) / 'cases' / f'{case["id"]:02}'
    exchanges = sorted(p for p in root.iterdir() if p.is_dir())
    if [p.name for p in exchanges] != ['001', '002', '003']:
        raise ValueError('Missing/extra/incomplete captured exchanges; no network fallback')
    index = 0

    def substitute(request):
        nonlocal index
        if index >= len(exchanges):
            raise ValueError('Replay attempted an extra request')
        path = exchanges[index]; index += 1
        meta = strict_json((path / 'exchange.json').read_bytes())
        if any((path / name).stat().st_size > LIMIT for name in ('request.bin', 'response.bin')):
            raise ValueError('Captured body exceeds the original bounded allowance')
        request_body, response_body = (path / 'request.bin').read_bytes(), (path / 'response.bin').read_bytes()
        if (not meta['complete'] or not meta['exported'] or len(request_body) > LIMIT or len(response_body) > LIMIT
                or sha256(request_body).hexdigest() != meta['request_sha256']
                or sha256(response_body).hexdigest() != meta['response_sha256']
                or request.method != meta['method'] or request.url.path != meta['path'] or request.content != request_body):
            raise ValueError('Replay bytes/identity/completeness differ from captured request')
        return httpx.Response(meta['status'], headers=meta['response_headers'], content=response_body)

    with LlamaCppInterpreter(bundle['config']['endpoint'], 'explicit-offline-replay-substitute', bundle['prompt'],
            transport=httpx.MockTransport(substitute)) as adapter:
        result = adapter.interpret(case['text'])
    if index != 3:
        raise ValueError('Replay did not consume exactly the captured exchanges')
    state = asdict(result); state['recognition'].pop('version')
    check_case_state(case, state)
    captured = strict_json((root / 'result.json').read_bytes())
    if captured['result'] != json.loads(json.dumps(asdict(result))):
        raise ValueError('Replayed contract differs from Windows validation')
    return result


def replay(exported, output):
    bundle = load_preparation()
    exported, output = Path(exported).resolve(), Path(output).resolve()
    if not output.is_relative_to((ROOT / 'build/test-only').resolve()) or output.exists() or output.is_relative_to(exported):
        raise ValueError('Use a new isolated build/test-only replay directory')
    input_bytes = artifact_bytes(exported)
    cap = bundle['config']['limits']['codespace_artifact_bytes']
    if input_bytes > cap:
        raise ValueError('Codespace artifact sub-budget exceeded by imported capture')
    manifest = strict_json((exported / 'manifest.json').read_bytes())
    if (manifest['freeze_sha256'] != bundle['freeze_sha256'] or manifest['attempt_identity'] != bundle['freeze']['attempt_identity']
            or manifest['original_attempt_identity'] != bundle['freeze']['original_attempt_identity']
            or manifest['previous_attempt_identity'] != bundle['freeze']['previous_attempt_identity']):
        raise ValueError('Capture freeze/attempt identity mismatch')
    if (any(manifest.get(key) != value for key, value in review_status().items())
            or manifest.get('technical_decision_sha256') != bundle['freeze']['files']['technical-decision.json']
            or manifest.get('partial_review_sha256') != bundle['freeze']['files']['partial-expectations-review.json']
            or manifest.get('review_original_freeze_sha256') != bundle['freeze']['previous_freeze_sha256']):
        raise ValueError('Technical capture/review provenance or acceptance boundary differs')
    real = manifest['classification'] == 'owner_operated_windows_capture'
    if real:
        require_execution_approval(exported / 'execution-approval.json', bundle)
        require_technical_review(exported / 'review.json', bundle)
        if strict_json((exported / 'technical-decision.json').read_bytes()) != bundle['technical_decision']:
            raise ValueError('Exported technical decision changed')
        if not strict_json((exported / 'supervision.json').read_bytes())['completed']:
            raise ValueError('Windows supervision stopped; no complete feasibility pass')
        cleanup = strict_json((exported / 'cleanup.json').read_bytes())
        if (not cleanup['owned_job_closed'] or cleanup['errors'] or
                cleanup.get('unidentified_job_pids') or not all(p['exit_confirmed'] for p in cleanup['owned_exits'])):
            raise ValueError('Native cleanup is unconfirmed')
        receipt = strict_json((exported / 'windows-receipt.json').read_bytes())
        verify_recorded_cleanup(receipt, cleanup, bundle)
    elif manifest['classification'] != 'synthetic_offline_fixture':
        raise ValueError('Unknown replay classification')
    ledger = [strict_json(line) for line in (exported / 'attempts.jsonl').read_bytes().splitlines()]
    if len(ledger) != 14 or any(type(row['attempt']) is not int or row['attempt'] != i or row['case'] != case['text']
            for i, (row, case) in enumerate(zip(ledger, bundle['cases']['cases'], strict=True), 1)):
        raise ValueError('Original ordered generation ledger is incomplete or inconsistent; no replay credit')
    output.mkdir(parents=True)
    summary = {'evidence': 'explicit_replay_test_substitutes', 'live_api_real_adapter_verified': False,
        'deferred_live_cases': [1, 5, 10], **review_status(), 'cases': [],
        'technical_result': 'incomplete', 'provisional_policy_result': 'incomplete',
        'ownership_evidence': 'recorded_identity_consistency_only' if real else 'explicit_synthetic_fixture'}

    def snapshot():
        previous = output / 'replay.json'
        size = len((json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode())
        if input_bytes + artifact_bytes(output) - (previous.stat().st_size if previous.exists() else 0) + size > cap:
            raise ValueError('Codespace artifact sub-budget exceeded by capture plus replay')
        write_json(previous, summary)

    try:
        for case, recorded in zip(bundle['cases']['cases'], manifest['cases'], strict=True):
            if recorded['case'] != case['id'] or not recorded['shared_validation_completed']:
                raise ValueError('Incomplete/stopped capture; no passing replacement is fabricated')
            if real:
                accepted = strict_json((exported / f'accepted-{case["id"]:02}.json').read_bytes())
                if accepted['case'] != case['id'] or not 0 <= accepted['elapsed_ms'] < 90000:
                    raise ValueError('Windows supervisor did not accept validation before the deadline')
            result = replay_case(case, bundle, exported)
            policies = []
            for context in ({}, {'browser_language': 'fr'}, {'preferred_language': 'en', 'browser_language': 'it'}, {'explanation_language_choice': 'en'}):
                try: policy = asdict(apply_language_policy(result, context))
                except LanguageOutcome as action: policy = {'outcome': action.outcome, 'code': action.code, 'detail': action.detail}
                policies.append({'context': context, 'result': policy})
            item = {'case': case['id'], 'policies': policies, 'evidence': 'replay_substitute',
                'technical_validation': 'passed', 'provisional_case_check': 'passed', 'policy_expectations': 'provisional'}
            if case['api']:
                from fastapi.testclient import TestClient
                from scripts.uc001_execution_v1_3_0.development import create_development_app
                class ReplaySubstitute:
                    def interpret(self, text):
                        if text != case['text']: raise ValueError('Replay substitute original mismatch')
                        return result
                app = create_development_app(output / f'case-{case["id"]}.sqlite3', ReplaySubstitute())
                try:
                    with TestClient(app) as client:
                        response = client.post('/api/comparisons', json={'submission_key': str(uuid4()), 'text': case['text'],
                            'search_location': {'country_code': 'CH'}, 'language_context': {'browser_language': 'en'}},
                            headers={'X-Submission-Proof': 'a' * 64})
                        body = response.json()
                        expected = case['expected_route']
                        if response.status_code >= 400 or (body.get('issues') != [{'code': expected}] if case['id'] == 1 else body.get('outcome') != expected):
                            raise ValueError('Application routing replay differs from the frozen expectation')
                        item['api_replay'] = {'status': response.status_code, 'body': body, 'live_check_satisfied': False}
                finally:
                    app.state.comparisons.store.engine.dispose()
            summary['cases'].append(item)
            snapshot()
        summary.update(outcome='technical_replay_completed_semantics_pending', technical_result='passed', provisional_policy_result='passed')
    finally:
        snapshot()
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    replay(args.export, args.output)


if __name__ == '__main__':
    main()
