"""Create the separate review package; never execute its diagnostic."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPTS = ROOT / 'scripts/uc001_granite_controller'
PRIOR = ROOT / 'build/uc001-granite-prior-accounting-final-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    package = HERE / 'package'
    package.mkdir(exist_ok=False)
    files = {name: (SCRIPTS / name).read_bytes() for name in (
        'controller.py', 'windows_job.py', 'worker.py', 'standins.py',
        'proxy_no_network.py', 'proxy_binding_selftest.py')}
    files['proxy.py'] = (ROOT / 'scripts/uc001_granite_acquisition_proxy/proxy.py').read_bytes()
    for name in ('prior-budget.json', 'prior-budget.json.sha256', 'owner-statement.txt'):
        files[name] = (PRIOR / name).read_bytes()
    assert sha(files['proxy.py']) == 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
    assert sha(files['prior-budget.json']) == '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a'
    config = dict(selftest_only=True, proxy_helper='proxy.py', prior_receipt='prior-budget.json',
                  guard_entry='proxy_no_network.py', proxy_sha256=sha(files['proxy.py']),
                  prior_sha256=sha(files['prior-budget.json']),
                  guard_sha256=sha(files['proxy_no_network.py']),
                  selftest_hashes={name: sha(data) for name, data in files.items() if name.endswith('.py')})
    files['selftest-config.json'] = (json.dumps(config, indent=2) + '\n').encode()
    files['Run-ProxyBindingCheck.ps1'] = (HERE / 'Run-ProxyBindingCheck.ps1').read_bytes()
    files['README.md'] = (HERE / 'package-readme.md').read_bytes()
    manifest = dict(version=HERE.name, scope='network-free-proxy-native-binding-selftest',
                    execution_authorized=False, files={name: sha(data) for name, data in sorted(files.items())})
    files['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    for name, data in files.items():
        (package / name).write_bytes(data)
    archive = HERE / (HERE.name + '.zip')
    with ZipFile(archive, 'x', compression=ZIP_DEFLATED) as value:
        for name, data in sorted(files.items()):
            item = ZipInfo(name, (2026, 10, 27, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            value.writestr(item, data)
    result = dict(archive=archive.name, bytes=archive.stat().st_size,
                  sha256=sha(archive.read_bytes()), manifest_sha256=sha(files['manifest.json']),
                  config_sha256=sha(files['selftest-config.json']),
                  helper_sha256=config['selftest_hashes'], execution_authorized=False,
                  windows_execution=False)
    with (HERE / 'package-result.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
