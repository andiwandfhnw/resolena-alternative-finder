import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path('build/uc001-granite-proxy-binding-selftest-v1')
PACKAGE = ROOT / 'package'
PROXY_SHA = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
PRIOR_SHA = '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a'
PYTHON_FILES = {'controller.py', 'worker.py', 'windows_job.py', 'standins.py',
                'proxy.py', 'proxy_no_network.py', 'proxy_binding_selftest.py'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def test_archive_contains_exact_final_sources_and_receipt():
    receipt = json.loads((ROOT / 'package-result.json').read_text())
    archive = ROOT / 'uc001-granite-proxy-binding-selftest-v1.zip'
    assert digest(archive.read_bytes()) == receipt['sha256']
    assert archive.stat().st_size == receipt['bytes']
    with ZipFile(archive) as value:
        assert len(value.namelist()) == len(set(value.namelist())) == 14
        assert all('/' not in name and '\\' not in name for name in value.namelist())
        manifest = json.loads(value.read('manifest.json'))
        assert digest(value.read('manifest.json')) == receipt['manifest_sha256']
        assert set(value.namelist()) == set(manifest['files']) | {'manifest.json'}
        for name, sha in manifest['files'].items():
            data = value.read(name)
            assert digest(data) == sha
            assert data == (PACKAGE / name).read_bytes()
        assert manifest['files']['proxy.py'] == PROXY_SHA
        assert manifest['files']['prior-budget.json'] == PRIOR_SHA
        for name in PYTHON_FILES - {'proxy.py'}:
            assert value.read(name) == (Path('scripts/uc001_granite_controller') / name).read_bytes()


def test_configuration_is_explicitly_selftest_only_with_fixed_accounting():
    config = json.loads((PACKAGE / 'selftest-config.json').read_text())
    assert config['selftest_only'] is True
    assert 'root' not in config and 'execution_authorized' not in config
    assert config['proxy_sha256'] == PROXY_SHA
    assert config['prior_sha256'] == PRIOR_SHA
    assert set(config['selftest_hashes']) == PYTHON_FILES
    assert config['guard_sha256'] == config['selftest_hashes']['proxy_no_network.py']
    assert config['proxy_helper'] == 'proxy.py'
    assert config['prior_receipt'] == 'prior-budget.json'
    assert config['guard_entry'] == 'proxy_no_network.py'
    assert all(digest((PACKAGE / name).read_bytes()) == sha
               for name, sha in config['selftest_hashes'].items())


def test_wrapper_requires_owner_gate_and_external_manifest_before_native_call():
    script = (PACKAGE / 'Run-ProxyBindingCheck.ps1').read_text()
    assert script.index('if (-not $OwnerAuthorized)') < script.index('Get-FileHash')
    assert script.index('Get-FileHash') < script.index('& $GranitePython')
    assert '$ExpectedManifestSha256' in script
    assert r'granite-python-3.12.11-20250702\env\Scripts\python.exe' in script
    assert '--owner-authorized' in script and '-I -B' in script
    assert 'without fixes/retry' in script
    assert 'native_run' not in script
    assert 'granite-proxy-binding-selftest-v1' in script


def test_old_receipt_and_owner_statement_are_copied_without_refreeze():
    prior = Path('build/uc001-granite-prior-accounting-final-v1')
    for name in ('prior-budget.json', 'prior-budget.json.sha256', 'owner-statement.txt'):
        assert (PACKAGE / name).read_bytes() == (prior / name).read_bytes()
    receipt = json.loads((PACKAGE / 'prior-budget.json').read_text())
    assert receipt['previously_charged_bytes'] == 0
    assert receipt['execution_authorized'] is False
    assert receipt['helper_hashes']['worker.py'] != digest((PACKAGE / 'worker.py').read_bytes())
