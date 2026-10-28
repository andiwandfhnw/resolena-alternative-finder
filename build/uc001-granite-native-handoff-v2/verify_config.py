"""Read-only package/configuration validation; never enter native_run."""
import argparse
import ast
import ctypes
import hashlib
import importlib.util
import json
import ntpath
from pathlib import Path
import sys


VERSION = 'uc001-granite-native-handoff-v2'
DESTINATION = r'C:\Users\AndiWand\Downloads\granite-native-handoff-v2'
NATIVE_ROOT = r'C:\Resolena\gn1-20261025'
HELPERS = {
    'controller.py': '9c5f3bab58fd3f2d20d345f5093ca2ac80b1e9149da74c1555fcf9b450e92fc1',
    'worker.py': '4f0dc7571edeb097ad172f5e423659e94c8026e5f2dbcb6e0f4d0874e8a32028',
    'standins.py': 'eddac526505213644f553b0b8617396ff7898f53dd174ecd6dd030b21f69501f',
    'windows_job.py': '792ee180000065fc39edcccbf2e7130ec68fff5358128b258f2a0e95952f0a22',
}
PROXY_SHA = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
FROZEN_SHA = 'c4610156c24e95cdf1abab658cfde1c18be568940c7cb952c5a673833c620cf4'
PRIOR_SHA = '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a'
FILES = set(HELPERS) | {
    'proxy.py', 'frozen-config.json', 'prior-budget.json', 'prior-budget.json.sha256',
    'owner-statement.txt', 'native-config.inactive.json', 'verify_config.py',
    'Preflight-GraniteNative.ps1', 'README.md', 'native-build-procedure.md',
}
CONFIG_FIELDS = {'execution_authorized', 'owner', 'root', 'proxy_helper',
                 'prior_receipt', 'prior_sha256', 'frozen_config', 'helper_hashes'}
FORBIDDEN = []


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
                 'socket.connect', 'socket.bind', 'socket.getaddrinfo',
                 'ctypes.dlopen', 'ctypes.dlsym'}:
        FORBIDDEN.append(event)
        raise RuntimeError('Forbidden during configuration validation: ' + event)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_metadata():
    return dict(python_version=sys.version.split()[0], pointer_bits=ctypes.sizeof(ctypes.c_void_p) * 8,
                platform=sys.platform, executable=sys.executable)


def strict_json(data):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate JSON key: ' + key)
            value[key] = item
        return value
    return json.loads(data, object_pairs_hook=pairs)


def require_rejection(controller, config, root, reason):
    try:
        controller.validate_native_config(config, root)
    except controller.ControllerFailure as error:
        if str(error) != 'native_preflight_failed:' + reason:
            raise AssertionError(str(error)) from error
    else:
        raise AssertionError('Expected configuration rejection: ' + reason)


def verify(root, expected_manifest_sha256):
    root = Path(root).resolve()
    if sha(root / 'manifest.json') != expected_manifest_sha256:
        raise ValueError('Manifest hash differs')
    manifest = strict_json((root / 'manifest.json').read_bytes())
    if (manifest.get('version') != VERSION or manifest.get('execution_authorized') is not False
            or manifest.get('scope') != 'pinned_runtime_source_and_model_free_build_only'
            or set(manifest.get('files', {})) != FILES
            or {path.name for path in root.iterdir()} != FILES | {'manifest.json'}):
        raise ValueError('Package scope or exact file inventory differs')
    for name, expected in manifest['files'].items():
        path = root / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError('Package file hash differs: ' + name)
        if path.suffix == '.py':
            ast.parse(path.read_bytes(), filename=str(path))
    pinned = dict(HELPERS, **{'proxy.py': PROXY_SHA, 'frozen-config.json': FROZEN_SHA,
                             'prior-budget.json': PRIOR_SHA})
    if any(manifest['files'][name] != expected for name, expected in pinned.items()):
        raise ValueError('Current accepted execution binding differs')
    config = strict_json((root / 'native-config.inactive.json').read_bytes())
    if (set(config) != CONFIG_FIELDS or config['execution_authorized'] is not False
            or not isinstance(config['owner'], str) or not config['owner']
            or config['root'] != NATIVE_ROOT or config['helper_hashes'] != HELPERS
            or config['prior_sha256'] != PRIOR_SHA):
        raise ValueError('Inactive four-helper configuration schema differs')
    for key, name in [('proxy_helper', 'proxy.py'), ('prior_receipt', 'prior-budget.json'),
                      ('frozen_config', 'frozen-config.json')]:
        if config[key] != ntpath.join(DESTINATION, name):
            raise ValueError('Execution destination differs: ' + key)
    prior = strict_json((root / 'prior-budget.json').read_bytes())
    if (prior['accounting_complete'] is not True
            or type(prior['previously_charged_bytes']) is not int
            or prior['previously_charged_bytes'] != 0
            or prior['acquisition_ceiling_bytes'] != 10737418240
            or prior['allowance_reset_or_renewed'] is not False
            or prior['evidence']['independently_measured_by_codex'] is not False
            or sha(root / prior['evidence']['file']) != prior['evidence']['sha256']
            or (root / 'prior-budget.json.sha256').read_text().strip() != PRIOR_SHA + '  prior-budget.json'):
        raise ValueError('Accepted accounting provenance differs')

    spec = importlib.util.spec_from_file_location('_granite_handoff_controller', root / 'controller.py')
    controller = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = controller
    spec.loader.exec_module(controller)
    require_rejection(controller, config, root, 'native_execution_not_authorized')
    # This temporary dictionary is validation input only; never persisted or executed.
    mapped = dict(config, execution_authorized=True, owner='synthetic configuration validation only',
                  proxy_helper=str(root / 'proxy.py'), prior_receipt=str(root / 'prior-budget.json'),
                  frozen_config=str(root / 'frozen-config.json'))
    validated = controller.validate_native_config(mapped, root)
    if type(validated['prior_bytes']) is not int or validated['prior_bytes'] != 0:
        raise ValueError('Actual prior-receipt validation differs')
    stale = dict(mapped, helper_hashes=dict(HELPERS, **{'controller.py': '0' * 64}))
    require_rejection(controller, stale, root, 'controller_helper_hash_differs:controller.py')
    expanded = dict(mapped, helper_hashes=dict(HELPERS, **{'proxy_binding_selftest.py': '0' * 64}))
    require_rejection(controller, expanded, root, 'controller_manifest_incomplete')
    require_rejection(controller, dict(mapped, prior_sha256='0' * 64), root,
                      'prior_receipt_hash_differs')
    for name in ('_granite_controller_worker',):
        if Path(sys.modules[name].__file__).resolve().parent != root:
            raise ValueError('Configuration validation imported a different helper directory')
    if FORBIDDEN:
        raise RuntimeError('Forbidden validation attempt')
    return dict(package_configuration_validation_passed=True, configuration_inactive=True,
                bound_prior_bytes=0, exact_native_helper_count=4,
                runtime=runtime_metadata(),
                manifest_sha256=expected_manifest_sha256,
                controller_sha256=HELPERS['controller.py'], prior_receipt_sha256=PRIOR_SHA,
                historical_prior_preparation_bindings_preserved=True,
                native_api_invoked=False, native_binding_verified=False,
                resource_fit_established=False, windows_entry_conditions_verified=False,
                execution_config_written=False, acquisition_or_build=False,
                forbidden_attempts=FORBIDDEN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', required=True, type=Path)
    parser.add_argument('--expected-manifest-sha256', required=True)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    sys.addaudithook(audit)
    try:
        result = verify(args.package_root, args.expected_manifest_sha256)
    except BaseException as error:
        print(json.dumps(dict(package_configuration_validation_passed=False,
                              failure_reason=str(error), native_api_invoked=False,
                              resource_fit_established=False, runtime=runtime_metadata(),
                              forbidden_attempts=FORBIDDEN), indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
