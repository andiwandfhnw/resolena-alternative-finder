from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess

import httpx
import pytest


ROOT = Path('scripts/uc001_transport_preparation')


@pytest.mark.parametrize('failure', [None, 'missing_accepted', 'wrong_accepted', 'right_denied', 'wrong_body', 'redirect'])
def test_model_free_forwarded_authentication_is_protected(failure):
    from scripts.uc001_transport_preparation.probe_forward import check_service
    seen = []

    def respond(request):
        seen.append(request)
        assert request.url.path == '/probe'
        right = request.headers.get('Authorization') == 'Bearer synthetic-key'
        status = 200 if right else 401
        if failure == 'missing_accepted' and len(seen) == 1:
            status = 200
        if failure == 'wrong_accepted' and len(seen) == 2:
            status = 200
        if failure == 'right_denied' and right:
            status = 403
        if failure == 'redirect':
            status = 302
        body = b'wrong' if failure == 'wrong_body' else b'uc001-model-free-transport\n'
        return httpx.Response(status, content=body)

    with httpx.Client(base_url='http://127.0.0.1:49188', transport=httpx.MockTransport(respond), trust_env=False, follow_redirects=False) as client:
        if failure:
            with pytest.raises(ValueError):
                check_service(client, 'synthetic-key')
        else:
            check_service(client, 'synthetic-key')
            assert len(seen) == 3
            assert 'authorization' not in seen[0].headers


def test_transport_preparation_preserves_originals_and_prior_results():
    baseline = json.loads(Path('build/uc001-transport-preparation/baseline.json').read_text())
    for name, expected in baseline.items():
        assert sha256(Path(name).read_bytes()).hexdigest() == expected, name


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell parser absent')
def test_transport_scripts_parse_and_default_starts_nothing():
    command = r'''
    Get-ChildItem scripts/uc001_transport_preparation/*.ps1 | ForEach-Object {
        $tokens=$null;$errors=$null
        $null=[Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors)
        if($errors.Count){throw $errors[0]}
    }
    '''
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-Command', command], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File', str(ROOT/'Test-Transport.ps1')], capture_output=True, text=True, timeout=10)
    assert result.returncode != 0 and 'transport-only approval' in result.stderr
    assert not (ROOT/'results').exists()


@pytest.mark.skipif(shutil.which('pwsh') is None, reason='PowerShell fixture absent')
@pytest.mark.parametrize('case', ['success', 'remote_failed', 'bridge_wildcard', 'endpoint_foreign', 'job_close_failed', 'exit_unconfirmed'])
def test_model_free_transport_owned_cleanup_offline(case):
    result = subprocess.run(['pwsh', '-NoProfile', '-NonInteractive', '-File', str(ROOT/'Test-Offline.ps1'), '-Case', case], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'PASS {case}' in result.stdout
