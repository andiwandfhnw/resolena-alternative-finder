"""Create a separate identity-diagnostic bundle without changing prior packages."""
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

VERSION = 'uc001-granite-controller-identity-diagnostic-v1'
HELPERS = ('controller.py', 'windows_job.py', 'worker.py', 'standins.py')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_package(repo, destination, runner, readme):
    repo, destination = Path(repo), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name in HELPERS:
        shutil.copyfile(repo/'scripts/uc001_granite_controller'/name, destination/name)
    template = json.loads((repo/'build/uc001-granite-controller/controller-config.template.json').read_text())
    template['execution_authorized'] = False
    template['helper_hashes'] = {name: digest(destination/name) for name in HELPERS}
    (destination/'controller-config.template.json').write_text(json.dumps(template, indent=2)+'\n')
    shutil.copyfile(runner, destination/'Run-IdentityDiagnostic.ps1')
    shutil.copyfile(readme, destination/'README.md')
    manifest = dict(version=VERSION, execution_authorized=False,
        purpose='offline-prepared-scoped-unknown-identity-diagnostic',
        files={p.name: digest(p) for p in sorted(destination.iterdir())})
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    archive = destination.parent/(VERSION+'.zip')
    with ZipFile(archive, 'x', compression=ZIP_DEFLATED) as bundle:
        for path in sorted(destination.iterdir()):
            info = ZipInfo(path.name, date_time=(2026, 10, 26, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    return dict(archive=str(archive), bytes=archive.stat().st_size, sha256=digest(archive),
        manifest_sha256=digest(destination/'manifest.json'),
        template_sha256=digest(destination/'controller-config.template.json'))
