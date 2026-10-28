import hashlib
import json
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

from app.domain.interpretation import ContractViolation
from scripts.uc001_execution_v1_3_0.controls import RunBudget
from scripts.uc001_execution_v1_3_0.run import require_review
from scripts.uc001_contract_local.capture import CaptureTransport, capture_case, finalize_export, load_preparation
from scripts.uc001_contract_local.replay import replay_case


KEY = 'synthetic-only-secret-which-must-not-be-exported'
TEMPLATE = '<|im_start|>synthetic<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'


def packet():
    return {'recognition': {'status': 'unknown', 'language': None}, 'meaning_status': 'needs_clarification',
        'clauses': [{'span': {'quote': 'Velo', 'occurrence': 1}, 'meaning_status': 'needs_clarification',
            'normalized': None, 'item_ids': []}], 'items': [], 'message': 'Synthetic fixture: clarify the subject.'}


def response(value=None):
    return {'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(value or packet())}}],
        'usage': {'prompt_tokens': 200, 'completion_tokens': 100}}


def native_fixture(mode='good', seen=None):
    def handle(request):
        if seen is not None:
            seen.append(request)
        assert request.url.host == '127.0.0.1' and request.url.port == 49187
        assert request.headers['authorization'] == 'Bearer ' + KEY
        if request.url.path == '/apply-template':
            return httpx.Response(200, content=json.dumps({'prompt': TEMPLATE}).encode())
        if request.url.path == '/tokenize':
            return httpx.Response(200, json={'tokens': [1] * (5121 if mode == 'overflow' else 200)})
        content = json.dumps(response()).encode()
        if mode == 'duplicate': content = b'{"choices":[],"choices":[]}'
        if mode == 'envelope': content = json.dumps({'choices': [], 'usage': {}}).encode()
        if mode == 'case': content = json.dumps(response({**packet(), 'meaning_status': 'unsupported', 'message': 'Synthetic limitation'})).encode()
        return httpx.Response(503 if mode == 'http' else 200, content=content)
    return httpx.MockTransport(handle)


def prepared_case(tmp_path, mode='good'):
    bundle = load_preparation()
    case = bundle['cases']['cases'][8]
    budget = RunBudget(tmp_path/'attempts.jsonl', [case['text']], 10**12)
    capture_case(case, bundle, tmp_path, KEY, budget, transport=native_fixture(mode))
    finalize_export(tmp_path, bundle)
    return bundle, case, budget


def test_frozen_inputs_original_attempt_identity_and_qualified_gate():
    bundle = load_preparation()
    assert bundle['freeze']['attempt_identity'] == 'bda2015c0ffbe89ab1a612fb4003b2b12f254871cf32f2e47dbbbe9d45cf0f52'
    for name in ('prompt.txt', 'schema.json', 'cases.json', 'config.json'):
        assert bundle['parent_hashes'][name] == hashlib.sha256((Path('scripts/uc001_execution_v1_3_0')/name).read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='Qualified expectations review'):
        require_review(Path('scripts/uc001_execution_v1_3_0/review-template.json'), bundle['freeze_sha256'])


def test_codespace_replay_cannot_silently_use_different_validation_dependencies(monkeypatch):
    import importlib.metadata
    current=importlib.metadata.version
    monkeypatch.setattr(importlib.metadata,'version',lambda name: '0.0' if name=='pydantic' else current(name))
    with pytest.raises(ValueError,match='dependency versions'):
        load_preparation()


def test_capture_and_replay_use_unchanged_shared_validation_and_exact_bytes(tmp_path):
    bundle, case, budget = prepared_case(tmp_path)
    result = replay_case(case, bundle, tmp_path/'export')
    assert result.meaning_status == 'needs_clarification' and budget.index == 1
    raw = tmp_path/'private/cases/09/003/response.bin'
    assert raw.read_bytes() == json.dumps(response()).encode()
    public = tmp_path/'export/cases/09/003'
    assert (public/'response.bin').read_bytes() == raw.read_bytes()
    body = (public/'request.bin').read_bytes()
    sent = json.loads(body)
    assert sent['messages'][-1] == {'role': 'user', 'content': 'Velo'}
    assert 'country' not in sent and 'preferred_language' not in sent
    assert all(KEY.encode() not in p.read_bytes() for p in (tmp_path/'export').rglob('*') if p.is_file())
    manifest = json.loads((tmp_path/'export/manifest.json').read_text())
    assert manifest['live_api_real_adapter_verified'] is False and manifest['deferred_live_cases'] == [1, 5, 10]


@pytest.mark.parametrize('mode,error', [('duplicate', ContractViolation), ('envelope', ContractViolation), ('case', ValueError), ('http', httpx.HTTPStatusError)])
def test_bad_response_saved_before_shared_failure_and_no_next_generation(tmp_path, mode, error):
    bundle = load_preparation(); case = bundle['cases']['cases'][8]
    budget = RunBudget(tmp_path/'attempts.jsonl', [case['text'], 'never permitted next'], 10**12)
    with pytest.raises(error):
        capture_case(case, bundle, tmp_path, KEY, budget, transport=native_fixture(mode))
    assert (tmp_path/'private/cases/09/003/response.bin').exists()
    assert not (tmp_path/'export/cases/09/result.json').exists()
    assert budget.index == 1


def test_actual_prompt_fit_overflow_does_not_spend_generation(tmp_path):
    bundle=load_preparation(); case=bundle['cases']['cases'][8]
    budget=RunBudget(tmp_path/'attempts.jsonl',[case['text']],10**12)
    with pytest.raises(ContractViolation, match='exceeds context'):
        capture_case(case,bundle,tmp_path,KEY,budget,transport=native_fixture('overflow'))
    assert budget.index == 0


class BrokenStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b'{"partial":'
        raise httpx.ReadError('synthetic stream interruption')


@pytest.mark.parametrize('kind', ['interrupted', 'oversized', 'secret', 'headers', 'escaped_secret', 'compressed_secret', 'utf16_secret'])
def test_incomplete_or_secret_capture_is_preserved_privately_and_not_exported(tmp_path, kind):
    def handle(request):
        if kind == 'interrupted': return httpx.Response(200, stream=BrokenStream())
        if kind == 'oversized': return httpx.Response(200, content=b'x'*262145)
        if kind == 'headers': return httpx.Response(200, headers={'content-type': KEY}, content=b'{}')
        if kind == 'escaped_secret':
            return httpx.Response(200,content=('{"echo":"'+''.join('\\u%04x'%ord(c) for c in KEY)+'"}').encode())
        if kind == 'compressed_secret':
            import gzip
            return httpx.Response(200,headers={'content-encoding':'gzip'},stream=httpx.ByteStream(gzip.compress(json.dumps({'echo':KEY}).encode())))
        if kind == 'utf16_secret': return httpx.Response(200,content=json.dumps({'echo':KEY}).encode('utf-16'))
        return httpx.Response(200, content=KEY.encode())
    transport=CaptureTransport(tmp_path/'private',tmp_path/'export',KEY,transport=httpx.MockTransport(handle))
    with httpx.Client(transport=transport,trust_env=False) as client:
        with pytest.raises((ContractViolation,httpx.ReadError)):
            client.post('http://127.0.0.1:49188/v1/chat/completions',json={})
    assert (tmp_path/'private/001/response.bin').exists()
    meta=json.loads((tmp_path/'private/001/exchange.json').read_text())
    assert meta['exported'] is False
    assert len((tmp_path/'private/001/response.bin').read_bytes()) <= 262144
    assert not list((tmp_path/'export').rglob('*.bin'))


@pytest.mark.parametrize('change', ['body', 'metadata', 'incomplete', 'original', 'extra'])
def test_replay_rejects_tampering_and_has_no_network_fallback(tmp_path, change, monkeypatch):
    bundle,case,_=prepared_case(tmp_path)
    root=tmp_path/'export'; exchange=root/'cases/09/003'
    if change == 'body': (exchange/'response.bin').write_bytes(b'{}')
    if change in ('metadata','incomplete'):
        p=exchange/'exchange.json'; d=json.loads(p.read_text()); d['complete']=False if change=='incomplete' else True
        if change=='metadata': d['path']='/wrong'
        p.write_text(json.dumps(d))
    if change == 'original': case={**case,'text':'not the frozen original'}
    if change == 'extra': (root/'cases/09/004').mkdir()
    def prohibited(*args,**kwargs): raise AssertionError('Real network fallback attempted')
    monkeypatch.setattr(httpx.HTTPTransport,'handle_request',prohibited)
    with pytest.raises((ValueError,ContractViolation)):
        replay_case(case,bundle,root)


def test_default_capture_cli_cannot_infer_and_replay_requires_explicit_test_only_root():
    p=subprocess.run([sys.executable,'-m','scripts.uc001_contract_local.capture'],capture_output=True,text=True)
    assert p.returncode == 2 and '--' in p.stderr


def test_transport_does_not_follow_redirect_or_map_an_external_destination(tmp_path):
    calls=[]
    def redirect(request):
        calls.append(request)
        return httpx.Response(302,headers={'location':'https://external.invalid'},content=b'raw redirect')
    with httpx.Client(transport=CaptureTransport(tmp_path/'private',tmp_path/'export',KEY,
            transport=httpx.MockTransport(redirect)),trust_env=False,follow_redirects=False) as client:
        assert client.get('http://127.0.0.1:49188/props').status_code==302
        with pytest.raises(ContractViolation): client.get('https://external.invalid/props')
    assert len(calls)==1


@pytest.mark.parametrize('valid',[True,False])
def test_raw_compressed_bytes_remain_complete_even_when_later_http_decoding_fails(tmp_path,valid):
    import gzip
    raw=gzip.compress(b'{"synthetic":true}') if valid else b'synthetic invalid gzip'
    def handle(request):
        return httpx.Response(200,headers={'content-encoding':'gzip'},stream=httpx.ByteStream(raw))
    with httpx.Client(transport=CaptureTransport(tmp_path/'private',tmp_path/'export',KEY,
            transport=httpx.MockTransport(handle)),trust_env=False) as client:
        if valid: assert client.get('http://127.0.0.1:49188/props').json()=={'synthetic':True}
        else:
            with pytest.raises(httpx.DecodingError): client.get('http://127.0.0.1:49188/props')
    private=tmp_path/'private/001';public=tmp_path/'export/001'
    assert (private/'response.bin').read_bytes()==raw
    assert json.loads((private/'exchange.json').read_text())['complete'] is True
    if valid:
        assert (public/'response.bin').read_bytes()==raw
        assert json.loads((private/'exchange.json').read_text())==json.loads((public/'exchange.json').read_text())
    else:
        assert not (public/'response.bin').exists()
        assert json.loads((private/'exchange.json').read_text())['exported'] is False


def test_server_arguments_remain_exactly_the_retained_arguments():
    import re
    pattern = r'\$argsList\s*=\s*(@\([\s\S]*?\))\n'
    old = re.search(pattern, Path('scripts/uc001_execution_v1_3_0/Run-Windows.ps1').read_text()).group(1)
    new = re.search(pattern, Path('scripts/uc001_contract_local/Run-Windows.ps1').read_text()).group(1)
    assert old == new


@pytest.mark.parametrize('case', ['timer_expiry', 'timer_disarm', 'timer_close_failure', 'timer_limit'])
def test_native_deadline_guard_is_independent_of_blocked_powershell(case):
    p=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File','scripts/uc001_contract_local/Test-Offline.ps1','-Case',case],capture_output=True,text=True,timeout=20)
    assert p.returncode==0,p.stdout+p.stderr
    assert 'PASS '+case in p.stdout


@pytest.mark.parametrize('case', ['deadline', 'late_validation', 'hang', 'wrong_case', 'success', 'cleanup_failure', 'job_close_failure', 'resource_failure', 'existing_attempt', 'review_missing', 'progress_atomic', 'complete_race'])
def test_windows_local_native_supervision_paths_offline(case):
    p=subprocess.run(['pwsh','-NoProfile','-NonInteractive','-File','scripts/uc001_contract_local/Test-Offline.ps1','-Case',case],capture_output=True,text=True,timeout=20)
    assert p.returncode == 0,p.stdout+p.stderr
    assert 'PASS '+case in p.stdout
