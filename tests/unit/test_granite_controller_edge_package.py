import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

import pytest


ARTIFACT = Path('build/uc001-granite-controller-edge-diagnostic-v1').resolve()
VERSION = 'uc001-granite-controller-edge-diagnostic-v1'


def builder():
    spec = importlib.util.spec_from_file_location('granite_edge_packager', ARTIFACT/'build_package.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diagnostic_archive_is_complete_hash_bound_and_native_execution_disabled(tmp_path):
    result = builder().build_package(Path.cwd(), tmp_path/'package',
        ARTIFACT/'Run-OwnershipDiagnostic.ps1', ARTIFACT/'package-readme.md')
    with ZipFile(result['archive']) as archive:
        names = set(archive.namelist())
        assert names == {'controller.py', 'windows_job.py', 'worker.py', 'standins.py',
            'controller-config.template.json', 'Run-OwnershipDiagnostic.ps1', 'README.md', 'manifest.json'}
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['version'] == VERSION
        assert manifest['execution_authorized'] is False
        assert manifest['purpose'] == 'offline-prepared-scoped-child-edge-diagnostic'
        assert set(manifest['files']) == names-{'manifest.json'}
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        config = json.loads(archive.read('controller-config.template.json'))
        assert config['execution_authorized'] is False
        for name, digest in config['helper_hashes'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
    assert hashlib.sha256(Path(result['archive']).read_bytes()).hexdigest() == result['sha256']
    assert hashlib.sha256((tmp_path/'package/manifest.json').read_bytes()).hexdigest() == result['manifest_sha256']


def test_diagnostic_packager_preserves_existing_destination(tmp_path):
    destination = tmp_path/'package'
    destination.mkdir()
    (destination/'keep').write_text('preserve')
    with pytest.raises(FileExistsError):
        builder().build_package(Path.cwd(), destination, ARTIFACT/'Run-OwnershipDiagnostic.ps1',
            ARTIFACT/'package-readme.md')
    assert (destination/'keep').read_text() == 'preserve'


def test_diagnostic_runner_requires_future_authorization_before_any_integrity_or_native_action():
    pwsh = shutil.which('pwsh')
    assert pwsh
    result = subprocess.run([pwsh, '-NoLogo', '-NoProfile', '-NonInteractive', '-File',
        str(ARTIFACT/'Run-OwnershipDiagnostic.ps1'), '-ExpectedManifestSha256', '0'*64],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert 'Separate owner authorization is required; diagnostic not executed.' in result.stderr
    assert 'manifest' not in result.stderr.lower()


def test_diagnostic_runner_powershell_syntax_only():
    pwsh = shutil.which('pwsh')
    assert pwsh
    path = str(ARTIFACT/'Run-OwnershipDiagnostic.ps1').replace("'", "''")
    script = "$errors = $null; $tokens = $null; [void][System.Management.Automation.Language.Parser]::ParseFile('"+path+"', [ref]$tokens, [ref]$errors); if ($errors.Count) { $errors | Out-String | Write-Error; exit 1 }"
    result = subprocess.run([pwsh, '-NoLogo', '-NoProfile', '-NonInteractive', '-Command',
        script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_diagnostic_runner_scope_remains_single_harmless_selftest():
    script = (ARTIFACT/'Run-OwnershipDiagnostic.ps1').read_text()
    assert '[switch]$OwnerAuthorized' in script
    assert script.count('& $GranitePython -I -B') == 1
    assert "ownership-self-test --output $GraniteOutput" in script
    assert "'ownership-edge-diagnostic-'" in script
    assert 'C:\\Users\\AndiWand\\Downloads\\granite-python-3.12.11-20250702\\env\\Scripts\\python.exe' in script
    assert "'Run-OwnershipDiagnostic.ps1'" in script
    assert VERSION in script
    assert 'stop without fixes/retry' in script
