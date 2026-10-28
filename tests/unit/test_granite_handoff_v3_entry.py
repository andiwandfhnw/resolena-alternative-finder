import hashlib
import json
import ntpath
from pathlib import Path
import sys
import types

import pytest


SOURCE = Path('build/uc001-granite-native-handoff-v3/verify_config.py')
ISSUED = Path('build/uc001-granite-native-handoff-v2/package')


@pytest.fixture
def verifier(monkeypatch):
    monkeypatch.setattr(sys, 'dont_write_bytecode', True)
    module = types.ModuleType('granite_handoff_v3_entry_test')
    module.__file__ = str(SOURCE.resolve())
    exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), module.__dict__)
    return module


@pytest.fixture
def package(tmp_path, verifier):
    root = tmp_path / 'package'
    root.mkdir()
    for name in verifier.FILES:
        source = ISSUED / name
        if name == 'worker.py':
            source = Path('scripts/uc001_granite_controller/worker.py')
        elif name == 'verify_config.py':
            source = SOURCE
        (root / name).write_bytes(source.read_bytes())
    config = json.loads((root / 'native-config.inactive.json').read_text())
    config['helper_hashes'] = verifier.HELPERS
    for key, name in [('proxy_helper', 'proxy.py'), ('prior_receipt', 'prior-budget.json'),
                      ('frozen_config', 'frozen-config.json')]:
        config[key] = ntpath.join(verifier.DESTINATION, name)
    (root / 'native-config.inactive.json').write_text(json.dumps(config, indent=2) + '\n')
    manifest = dict(version=verifier.VERSION, execution_authorized=False,
                    scope='pinned_runtime_source_and_model_free_build_only',
                    destination=verifier.DESTINATION,
                    files={name: verifier.sha(root / name) for name in sorted(verifier.FILES)})
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return root, verifier.sha(root / 'manifest.json')


@pytest.fixture
def windows_environment():
    return {'VCTOOLSVERSION': '14.43.34808\\', 'WINDOWSSDKVERSION': '10.0.22621.0\\',
            'VSCMD_ARG_HOST_ARCH': 'x64', 'VSCMD_ARG_TGT_ARCH': 'x64',
            'VULKAN_SDK': r'C:\VulkanSDK\1.4.357.0',
            'VK_SDK_PATH': r'C:\VulkanSDK\1.4.357.0', 'PATH': r'C:\synthetic\bin'}


def injected_actual_worker(monkeypatch, verifier, windows_environment):
    calls = []
    original = verifier.check_worker_environment
    monkeypatch.setattr(verifier.os, 'environ', windows_environment)
    monkeypatch.setattr(verifier, 'runtime_metadata', lambda: dict(
        python_version='3.12.11', pointer_bits=64, platform='win32', executable='injected'))

    def observe(worker):
        actual = worker.validate_environment

        def validate(environ):
            calls.append((str(Path(worker.__file__).resolve()), dict(environ)))
            lookup = {'cl.exe': worker.CL, 'glslc.exe': worker.SDK + r'\Bin\glslc.exe'}
            return actual(environ, exists=lambda _: True, which=lookup.get)

        worker.validate_environment = validate
        return original(worker)

    monkeypatch.setattr(verifier, 'check_worker_environment', observe)
    return calls


def test_cli_wires_explicit_environment_check(monkeypatch, verifier, capsys):
    observed = []
    monkeypatch.setattr(sys, 'argv', ['verify_config.py', '--package-root', 'synthetic',
                                    '--expected-manifest-sha256', 'a' * 64, '--check-environment'])
    monkeypatch.setattr(sys, 'addaudithook', lambda _: None)

    def verify(root, manifest, *, check_environment=False):
        observed.append((str(root), manifest, check_environment))
        return {'worker_environment_validation_required': check_environment,
                'worker_environment_validation_passed': check_environment}

    monkeypatch.setattr(verifier, 'verify', verify)
    assert verifier.main() == 0
    assert observed == [('synthetic', 'a' * 64, True)]
    assert json.loads(capsys.readouterr().out)['worker_environment_validation_passed'] is True


def test_structural_only_does_not_invoke_environment_check(monkeypatch, verifier, package):
    monkeypatch.setattr(verifier, 'check_worker_environment', lambda _: pytest.fail('Environment check without opt-in'))
    root, digest = package
    result = verifier.verify(root, digest)
    assert result['worker_environment_validation_required'] is False
    assert result['worker_environment_validation_passed'] is False
    assert result['resource_fit_established'] is False
    assert result['native_api_invoked'] is False


def test_opt_in_calls_corrected_packaged_validator(monkeypatch, verifier, package, windows_environment):
    original = dict(windows_environment)
    calls = injected_actual_worker(monkeypatch, verifier, windows_environment)
    root, digest = package
    result = verifier.verify(root, digest, check_environment=True)
    assert calls == [(str((root / 'worker.py').resolve()), original)]
    assert result['worker_environment_validation_required'] is True
    assert result['worker_environment_validation_passed'] is True
    assert result['worker_module_path'] == str((root / 'worker.py').resolve())
    assert result['configuration_inactive'] is True
    assert result['execution_config_written'] is False
    assert result['acquisition_or_build'] is False
    assert result['native_api_invoked'] is False
    assert result['resource_fit_established'] is False
    assert windows_environment == original
    assert {path.name for path in root.iterdir()} == verifier.FILES | {'manifest.json'}


def test_wrong_activation_fails_actual_validator(monkeypatch, verifier, package, windows_environment):
    windows_environment['VCTOOLSVERSION'] = 'unapproved'
    calls = injected_actual_worker(monkeypatch, verifier, windows_environment)
    root, digest = package
    with pytest.raises(RuntimeError, match='frozen_x64_environment_not_active'):
        verifier.verify(root, digest, check_environment=True)
    assert len(calls) == 1
    assert {path.name for path in root.iterdir()} == verifier.FILES | {'manifest.json'}


@pytest.mark.parametrize('runtime', [
    dict(python_version='3.12.11', pointer_bits=64, platform='linux'),
    dict(python_version='3.12.10', pointer_bits=64, platform='win32'),
    dict(python_version='3.12.11', pointer_bits=32, platform='win32'),
])
def test_actual_entry_requires_approved_windows_runtime(monkeypatch, verifier, package, windows_environment, runtime):
    calls = injected_actual_worker(monkeypatch, verifier, windows_environment)
    monkeypatch.setattr(verifier, 'runtime_metadata', lambda: dict(runtime, executable='injected'))
    root, digest = package
    with pytest.raises(ValueError, match='Approved Windows Python 3.12.11 x64'):
        verifier.verify(root, digest, check_environment=True)
    assert calls == []
