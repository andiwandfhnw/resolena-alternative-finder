import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

import pytest


ARTIFACT = Path('build/uc001-granite-controller-launcher-fix').resolve()


def builder():
    path=ARTIFACT/'build_package.py'
    spec=importlib.util.spec_from_file_location('granite_correction_packager',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_new_archive_includes_template_all_helpers_and_one_stopping_runner(tmp_path):
    result=builder().build_package(Path.cwd(),tmp_path/'package',ARTIFACT/'Run-OwnershipCheck.ps1',ARTIFACT/'package-readme.md')
    with ZipFile(result['archive']) as archive:
        files=set(archive.namelist())
        assert files=={'controller.py','windows_job.py','worker.py','standins.py',
                       'controller-config.template.json','Run-OwnershipCheck.ps1','README.md','manifest.json'}
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['execution_authorized'] is False
        assert set(manifest['files'])==files-{'manifest.json'}
        for name,digest in manifest['files'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest
        config=json.loads(archive.read('controller-config.template.json'))
        assert config['execution_authorized'] is False
        assert set(config['helper_hashes'])=={'controller.py','windows_job.py','worker.py','standins.py'}
        for name,digest in config['helper_hashes'].items():
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest
    assert hashlib.sha256(Path(result['archive']).read_bytes()).hexdigest()==result['sha256']


def test_packager_refuses_existing_destination(tmp_path):
    destination=tmp_path/'package';destination.mkdir();(destination/'old.txt').write_text('retain')
    with pytest.raises(FileExistsError):
        builder().build_package(Path.cwd(),destination,ARTIFACT/'Run-OwnershipCheck.ps1',ARTIFACT/'package-readme.md')
    assert (destination/'old.txt').read_text()=='retain'


@pytest.mark.parametrize('defect',['missing_template','bad_helper','valid'])
def test_single_powershell_script_cannot_continue_after_failed_precheck(tmp_path,defect):
    # An isolated synthetic copy substitutes only a harmless local marker program.
    pwsh=shutil.which('pwsh');assert pwsh
    package=tmp_path/'gate';package.mkdir()
    marker=tmp_path/'invoked'
    fake=tmp_path/'fake-python'
    fake.write_text('#!/bin/sh\nprintf invoked > '+str(marker)+'\nexit 0\n');fake.chmod(0o700)
    script=(ARTIFACT/'Run-OwnershipCheck.ps1').read_text()
    script=script.replace(r'C:\Users\AndiWand\Downloads\granite-python-3.12.11-20250702\env\Scripts\python.exe',str(fake))
    (package/'Run-OwnershipCheck.ps1').write_text(script)
    helper_hashes={}
    for name in ('controller.py','windows_job.py','worker.py','standins.py'):
        data=b'# synthetic non-executed helper\n';(package/name).write_bytes(data)
        helper_hashes[name]=hashlib.sha256(data).hexdigest()
    (package/'controller-config.template.json').write_text(json.dumps(dict(execution_authorized=False,helper_hashes=helper_hashes)))
    (package/'README.md').write_text('Synthetic gate fixture only.\n')
    manifest=dict(version='uc001-granite-controller-launcher-fix-v1',execution_authorized=False,
                  files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in package.iterdir()})
    (package/'manifest.json').write_text(json.dumps(manifest))
    manifest_hash=hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest()
    if defect=='missing_template':
        (package/'controller-config.template.json').unlink()
    elif defect=='bad_helper':
        (package/'standins.py').write_text('changed')
    result=subprocess.run([pwsh,'-NoLogo','-NoProfile','-NonInteractive','-File',
        str(package/'Run-OwnershipCheck.ps1'),'-ExpectedManifestSha256',manifest_hash],
        capture_output=True,timeout=10)
    assert (result.returncode==0)==(defect=='valid'),result.stderr
    assert marker.exists()==(defect=='valid')
