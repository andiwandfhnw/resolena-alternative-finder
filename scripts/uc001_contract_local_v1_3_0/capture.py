"""Development-only Windows capture; execution requires the owned PS supervisor."""

import argparse
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'uc001_execution_v1_3_0'
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]

import httpx

from app.domain.interpretation import ContractViolation
from app.infrastructure.llama_cpp_interpreter import LlamaCppInterpreter, WireResult, strict_json
from scripts.uc001_execution_v1_3_0.controls import RunBudget, check_case_state, load_bundle, verify_authentication
from scripts.uc001_contract_local_v1_3_0.review_gate import require_technical_review, verify_technical_review, review_status
from scripts.uc001_contract_local_v1_3_0.harness_checks import HarnessStop, stop_record, verify_python_ownership, verify_effective, verify_request_limit, adapter_limit_body
from scripts.uc001_contract_local_v1_3_0.execution_gate import require_execution_approval, verify_execution_approval


LIMIT = 262144


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('wb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def load_preparation():
    bundle = load_bundle(PARENT)
    freeze = strict_json((HERE / 'freeze.json').read_bytes())
    for name, expected in freeze['files'].items():
        if sha256((HERE / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Local preparation changed: ' + name)
    if (bundle['freeze_sha256'] != freeze['parent_freeze_sha256'] or
            freeze['original_attempt_identity'] != bundle['freeze']['attempt_identity'] or
            freeze['attempt_identity'] == freeze['original_attempt_identity']):
        raise ValueError('Parent freeze/attempt identity changed; no reset')
    if json.loads((PARENT / 'schema.json').read_text()) != WireResult.model_json_schema():
        raise ValueError('Frozen schema differs; do not regenerate it')
    local = strict_json((HERE / 'config.json').read_bytes())
    if any(importlib.metadata.version(name) != version for name, version in local['dependencies'].items()
            if name != 'colorama' or sys.platform == 'win32'):
        raise ValueError('Verified dependency versions changed; no acquisition/upgrade')
    return {**bundle, 'parent_hashes': bundle['freeze']['files'],
        'parent_freeze_sha256': bundle['freeze_sha256'], 'freeze': freeze,
        'freeze_sha256': sha256((HERE / 'freeze.json').read_bytes()).hexdigest(),
        'local': local, 'technical_decision': strict_json((HERE / 'technical-decision.json').read_bytes())}


def contains_secret(body, key):
    text = body.decode(json.detect_encoding(body), errors='replace')
    if key in text:
        return True
    # Privacy scan only: unescape JSON string tokens, without interpreting meaning.
    for match in re.finditer(r'"(?:[^"\\]|\\.)*"', text):
        try:
            if key in json.loads(match.group()):
                return True
        except json.JSONDecodeError:
            pass
    return False


def publish(files, private, public, key):
    # Exact bodies are exported only after a complete capture and a secret scan.
    values = {name: (private / name).read_bytes() for name in files}
    if any(contains_secret(body, key) for body in values.values()):
        raise ContractViolation('Secret-bearing artifact retained privately; export prohibited')
    public.mkdir(parents=True, exist_ok=True)
    for name, body in values.items():
        with (public / name).open('xb') as output:
            output.write(body)


class CaptureTransport(httpx.BaseTransport):
    def __init__(self, private, public, key, *, transport=None):
        self.private, self.public, self.key = Path(private), Path(public), key
        self.transport = transport if transport is not None else httpx.HTTPTransport(retries=0, trust_env=False)
        self.index = 0

    def handle_request(self, request):
        if (request.url.scheme != 'http' or request.url.host != '127.0.0.1' or request.url.port != 49188
                or request.url.query or request.url.path not in
                ('/apply-template', '/tokenize', '/v1/chat/completions', '/props', '/v1/models')):
            raise ContractViolation('Only the explicit logical-loopback mapping is allowed')
        self.index += 1
        private, public = self.private / f'{self.index:03}', self.public / f'{self.index:03}'
        private.mkdir(parents=True, exist_ok=False)
        meta = {'method': request.method, 'path': request.url.path, 'status': None,
            'response_headers': {}, 'complete': False, 'exported': False, 'failure': None}
        write_json(private / 'exchange.json', meta)
        response = None
        try:
            body = bytearray()
            with (private / 'request.bin').open('xb') as output:
                for part in request.stream:
                    available = LIMIT - len(body)
                    output.write(part[:available]); output.flush()
                    body.extend(part[:available])
                    if len(part) > available:
                        raise ContractViolation('Request capture exceeds the bounded body allowance')
            if contains_secret(body, self.key):
                raise ContractViolation('Secret in request body; retained privately')
            if request.url.path == '/v1/chat/completions':
                verify_request_limit(strict_json(bytes(body)))
            headers = dict(request.headers)
            headers['host'] = '127.0.0.1:49187'
            mapped = httpx.Request(request.method, request.url.copy_with(port=49187),
                headers=headers, content=bytes(body), extensions=request.extensions)
            response = self.transport.handle_request(mapped)
            meta['status'] = response.status_code
            meta['response_headers'] = {k: v for k, v in response.headers.items() if k in ('content-type', 'content-encoding')}
            if len(json.dumps(meta).encode()) > 16384:
                raise ContractViolation('Response metadata exceeds capture allowance')
            content = bytearray()
            with (private / 'response.bin').open('xb') as output:
                for part in response.stream:
                    available = LIMIT - len(content)
                    output.write(part[:available]); output.flush()
                    content.extend(part[:available])
                    if len(part) > available:
                        raise ContractViolation('Response capture exceeds the bounded body allowance')
            meta.update(complete=True,
                request_sha256=sha256(body).hexdigest(), response_sha256=sha256(content).hexdigest())
            write_json(private / 'exchange.json', meta)
            decoded = httpx.Response(response.status_code, headers=meta['response_headers'], content=bytes(content))
            if len(decoded.content) > LIMIT:
                raise ContractViolation('Decoded response exceeds the unchanged body allowance')
            if contains_secret(decoded.content, self.key) or contains_secret(json.dumps(meta).encode(), self.key):
                raise ContractViolation('Secret-bearing response retained privately')
            meta['exported'] = True
            write_json(private / 'exchange.json', meta)
            publish(('request.bin', 'response.bin', 'exchange.json'), private, public, self.key)
            return decoded
        except BaseException as error:
            meta.update(exported=False, failure=type(error).__name__)
            write_json(private / 'exchange.json', meta)
            raise
        finally:
            if response is not None:
                response.close()

    def close(self):
        self.transport.close()


def capture_case(case, bundle, run_root, key, budget, *, transport=None):
    relative = Path('cases') / f'{case["id"]:02}'
    private, public = Path(run_root) / 'private' / relative, Path(run_root) / 'export' / relative
    with LlamaCppInterpreter(bundle['config']['endpoint'], key, bundle['prompt'],
            transport=CaptureTransport(private, public, key, transport=transport), before_generation=budget.consume) as interpreter:
        result = interpreter.interpret(case['text'])
    state = asdict(result)
    state['recognition'].pop('version')
    check_case_state(case, state)
    write_json(private / 'result.json', {'case': case['id'], 'result': asdict(result),
        'validation': 'shared_contract_and_case_state_passed', 'technical_validation': 'passed',
        'provisional_case_check': 'passed', **review_status()})
    publish(('result.json',), private, public, key)
    return result


def finalize_export(run_root, bundle, *, classification='synthetic_offline_fixture'):
    run_root = Path(run_root)
    cases = []
    for case in bundle['cases']['cases']:
        private = run_root / 'private/cases' / f'{case["id"]:02}'
        public = run_root / 'export/cases' / f'{case["id"]:02}'
        exchanges = []
        for path in sorted(private.glob('*/exchange.json')):
            data = strict_json(path.read_bytes())
            exchanges.append({'exchange': path.parent.name, 'complete': data['complete'], 'exported': data['exported'],
                'private_response_bytes': (path.parent / 'response.bin').stat().st_size if (path.parent / 'response.bin').exists() else None})
        cases.append({'case': case['id'], 'shared_validation_completed': (public / 'result.json').is_file(), 'exchanges': exchanges})
    write_json(run_root / 'export/manifest.json', {'version': 'uc001-contract-local-1.3.0',
        'classification': classification, 'freeze_sha256': bundle['freeze_sha256'],
        'attempt_identity': bundle['freeze']['attempt_identity'], 'cases': cases,
        'original_attempt_identity': bundle['freeze']['original_attempt_identity'],
        **review_status(), 'live_api_real_adapter_verified': False, 'deferred_live_cases': [1, 5, 10],
        'technical_decision_sha256': bundle['freeze']['files']['technical-decision.json'],
        'partial_review_sha256': bundle['freeze']['files']['partial-expectations-review.json'],
        'review_original_freeze_sha256': bundle['freeze']['previous_freeze_sha256'],
        'incomplete_policy': 'Incomplete/secret-bearing bodies stay private on Windows; exported status never substitutes for them'})
    if (run_root / 'attempts.jsonl').exists():
        shutil.copyfile(run_root / 'attempts.jsonl', run_root / 'export/attempts.jsonl')


def verify_windows_environment():
    if (sys.platform != 'win32' or sys.version_info[:3] != (3, 12, 10) or not sys.flags.utf8_mode
            or Path(sys.executable) != Path(r'C:\ResolenaExperiments\uc001-validator-env\Scripts\python.exe')):
        raise ValueError('Use the verified explicit Windows Python 3.12.10 x64 venv with -I -X utf8')
    import struct
    if struct.calcsize('P') != 8:
        raise ValueError('64-bit Python required')


def run_capture(bundle, review, receipt, run_root, key, input_stream, approval):
    verify_execution_approval(approval, bundle)
    verify_technical_review(review, bundle)
    start = datetime.fromisoformat(receipt['started_utc']).timestamp()
    total = datetime.fromisoformat(receipt['total_started_utc']).timestamp()
    deadline = min(start + 1500, total + 2400)
    if (receipt['freeze_sha256'] != bundle['freeze_sha256'] or not receipt['authentication_verified']
            or receipt['attempt_identity'] != bundle['freeze']['attempt_identity']
            or receipt['original_attempt_identity'] != bundle['freeze']['original_attempt_identity']
            or not start <= time.time() < deadline
            or not 0 <= time.time() - receipt['receipt_epoch'] <= 90 or len(key) < 32):
        raise ValueError('Fresh authenticated owned-supervisor receipt is required')
    verify_python_ownership(receipt['python_ownership'])
    verify_effective(receipt['props'], receipt['startup_log'], receipt['launch_args'], adapter_limit_body())
    budget = RunBudget(run_root / 'attempts.jsonl', [c['text'] for c in bundle['cases']['cases']], deadline)
    classification = 'owner_operated_windows_capture'
    finalize_export(run_root, bundle, classification=classification)
    write_json(run_root / 'private/review.json', review)
    write_json(run_root / 'private/technical-decision.json', bundle['technical_decision'])
    write_json(run_root / 'private/execution-approval.json', approval)
    write_json(run_root / 'private/windows-receipt.json', receipt)
    publish(('review.json', 'technical-decision.json', 'execution-approval.json', 'windows-receipt.json'), run_root / 'private', run_root / 'export', key)
    with httpx.Client(base_url=bundle['config']['endpoint'], headers={'Authorization': 'Bearer ' + key},
            timeout=90, trust_env=False, follow_redirects=False,
            transport=CaptureTransport(run_root / 'private/preconditions', run_root / 'export/preconditions', key)) as client:
        verify_authentication(client)
        props = client.get('/props'); props.raise_for_status()
        verify_effective(strict_json(props.content), receipt['startup_log'], receipt['launch_args'], adapter_limit_body())
    try:
        for case in bundle['cases']['cases']:
            write_json(run_root / 'progress.json', {'case': case['id'], 'phase': 'ready'})
            if input_stream.readline().strip() != f'begin {case["id"]}':
                raise ValueError('Owned supervisor must arm the request deadline before generation')
            write_json(run_root / 'progress.json', {'case': case['id'], 'phase': 'running'})
            capture_case(case, bundle, run_root, key, budget)
            if budget.index != case['id']:
                raise ValueError('Original generation order/count changed')
            finalize_export(run_root, bundle, classification=classification)
            write_json(run_root / 'progress.json', {'case': case['id'], 'phase': 'validated'})
            if input_stream.readline().strip() != f'advance {case["id"]}':
                raise ValueError('No next request without supervisor validation acknowledgment')
        write_json(run_root / 'progress.json', {'case': 14, 'phase': 'complete'})
    finally:
        finalize_export(run_root, bundle, classification=classification)
        if (run_root / 'attempts.jsonl').exists():
            shutil.copyfile(run_root / 'attempts.jsonl', run_root / 'export/attempts.jsonl')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--verify-only', action='store_true')
    mode.add_argument('--preflight', action='store_true')
    mode.add_argument('--supervised-capture', action='store_true')
    parser.add_argument('--review', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--run-root', type=Path)
    parser.add_argument('--approval', type=Path)
    args = parser.parse_args(argv)
    bundle = load_preparation()
    if args.verify_only:
        verify_windows_environment()
        print(json.dumps({'outcome': 'local_preparation_verified', 'freeze_sha256': bundle['freeze_sha256'],
            **review_status(), 'startup_authorized': False}))
        return
    approval = require_execution_approval(args.approval, bundle)
    verify_windows_environment()
    review = require_technical_review(args.review, bundle)
    if args.preflight:
        return
    key = sys.stdin.readline().strip()
    receipt = strict_json(args.receipt.read_bytes())
    expected = Path(bundle['config']['reuse_root']).parent / 'uc001-contract-runs' / bundle['freeze']['attempt_identity']
    if args.run_root.resolve() != expected.resolve() or not args.run_root.is_dir():
        raise ValueError('Use the separately reserved approved additional-attempt directory; no reset')
    try:
        run_capture(bundle, review, receipt, args.run_root, key, sys.stdin, approval)
    except BaseException as error:
        write_json(args.run_root / 'capture-stopped.json', stop_record(error))
        raise


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(stop_record(error)), file=sys.stderr)
        sys.exit(1)
