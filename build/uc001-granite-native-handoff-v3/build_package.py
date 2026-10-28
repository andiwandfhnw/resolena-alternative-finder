"""Assemble the inactive review handoff; no execution entry point is invoked."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DESTINATION = r'C:\Users\AndiWand\Downloads\granite-native-handoff-v3'
HELPER_HASHES = {
    'controller.py': '9c5f3bab58fd3f2d20d345f5093ca2ac80b1e9149da74c1555fcf9b450e92fc1',
    'worker.py': '7e2660e10139862c7d5542e40c5e4ad0739eea917ee97de59be3671327b8daf5',
    'standins.py': 'eddac526505213644f553b0b8617396ff7898f53dd174ecd6dd030b21f69501f',
    'windows_job.py': '792ee180000065fc39edcccbf2e7130ec68fff5358128b258f2a0e95952f0a22',
}
PROXY_SHA = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
PRIOR_SHA = '56a85b9ded9d6c4bf504462e11d551b59e016fcd1c77d8c5102b93ff7df7475a'
FROZEN_SHA = 'c4610156c24e95cdf1abab658cfde1c18be568940c7cb952c5a673833c620cf4'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def main():
    files = {name: (ROOT / 'scripts/uc001_granite_controller' / name).read_bytes()
             for name in HELPER_HASHES}
    if any(sha(files[name]) != expected for name, expected in HELPER_HASHES.items()):
        raise ValueError('Current native helper binding differs')
    sources = {
        'proxy.py': ROOT / 'scripts/uc001_granite_acquisition_proxy/proxy.py',
        'frozen-config.json': ROOT / 'scripts/uc001_granite_contract_v1/config.json',
        'native-build-procedure.md': ROOT / 'build/uc001-granite-native-build-preparation/README.md',
        'README.md': HERE / 'package-readme.md',
        'Preflight-GraniteNative.ps1': HERE / 'Preflight-GraniteNative.ps1',
        'verify_config.py': HERE / 'verify_config.py',
    }
    prior = ROOT / 'build/uc001-granite-prior-accounting-final-v1'
    sources.update({name: prior / name for name in
                    ('prior-budget.json', 'prior-budget.json.sha256', 'owner-statement.txt')})
    files.update({name: path.read_bytes() for name, path in sources.items()})
    if (sha(files['proxy.py']) != PROXY_SHA or sha(files['prior-budget.json']) != PRIOR_SHA
            or sha(files['frozen-config.json']) != FROZEN_SHA):
        raise ValueError('Accepted proxy/prior/frozen configuration differs')
    config = dict(execution_authorized=False,
                  owner='Project owner; inactive draft pending separate execution approval',
                  root=r'C:\Resolena\gn1-20261025',
                  proxy_helper=DESTINATION + r'\proxy.py',
                  prior_receipt=DESTINATION + r'\prior-budget.json',
                  prior_sha256=PRIOR_SHA,
                  frozen_config=DESTINATION + r'\frozen-config.json',
                  helper_hashes=HELPER_HASHES)
    files['native-config.inactive.json'] = encoded(config)
    manifest = dict(version=HERE.name,
                    scope='pinned_runtime_source_and_model_free_build_only',
                    execution_authorized=False,
                    destination=DESTINATION,
                    files={name: sha(data) for name, data in sorted(files.items())})
    files['manifest.json'] = encoded(manifest)
    package = HERE / 'package'
    package.mkdir(exist_ok=False)
    for name, data in files.items():
        with (package / name).open('xb') as stream:
            stream.write(data)
    archive = HERE / (HERE.name + '.zip')
    with ZipFile(archive, 'x', compression=ZIP_DEFLATED) as value:
        for name, data in sorted(files.items()):
            item = ZipInfo(name, (2026, 10, 28, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            value.writestr(item, data)
    inventory = dict(version=HERE.name, execution_authorized=False,
                     archive=archive.name, archive_sha256=sha(archive.read_bytes()),
                     destination=DESTINATION,
                     files=[dict(name=name, bytes=len(data), sha256=sha(data),
                                 destination=DESTINATION + '\\' + name)
                            for name, data in sorted(files.items())])
    with (HERE / 'transfer-inventory.json').open('xb') as stream:
        stream.write(encoded(inventory))
    result = dict(archive=archive.name, bytes=archive.stat().st_size,
                  sha256=sha(archive.read_bytes()), file_count=len(files),
                  manifest_sha256=sha(files['manifest.json']),
                  inactive_config_sha256=sha(files['native-config.inactive.json']),
                  transfer_inventory_sha256=sha(encoded(inventory)),
                  helper_hashes=HELPER_HASHES, proxy_sha256=PROXY_SHA,
                  frozen_config_sha256=FROZEN_SHA, prior_receipt_sha256=PRIOR_SHA,
                  execution_authorized=False, windows_execution=False)
    with (HERE / 'package-result.json').open('xb') as stream:
        stream.write(encoded(result))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
