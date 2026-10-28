import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

import pytest


ARTIFACT = Path('build/uc001-granite-proxy-identities-v1').resolve()
VERSION = 'uc001-granite-proxy-identities-v1'
PROXY_SHA256 = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
FILES = {'controller.py','windows_job.py','worker.py','standins.py','proxy.py','check.py',
         'controller-config.template.json','Run-ReadinessCheck.ps1','README.md','manifest.json'}


def module(name):
    path = ARTIFACT/(name+'.py')
    spec = importlib.util.spec_from_file_location('granite_identity_'+name,path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_identity_package_is_complete_hash_bound_and_execution_disabled(tmp_path):
    result=module('build_package').build_package(Path.cwd(),tmp_path/'package',
        ARTIFACT/'Run-ReadinessCheck.ps1',ARTIFACT/'package-readme.md')
    with ZipFile(result['archive']) as archive:
        assert set(archive.namelist())==FILES
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['version']==VERSION
        assert manifest['purpose']=='offline-prepared-proxy-identity-binding'
        assert manifest['execution_authorized'] is False
        assert manifest['readiness_scope']=='structural_only'
        assert set(manifest['files'])==FILES-{'manifest.json'}
        assert all(hashlib.sha256(archive.read(name)).hexdigest()==digest for name,digest in manifest['files'].items())
        assert hashlib.sha256(archive.read('proxy.py')).hexdigest()==PROXY_SHA256
        config=json.loads(archive.read('controller-config.template.json'))
        assert config['execution_authorized'] is False
        assert set(config['helper_hashes'])=={'controller.py','windows_job.py','worker.py','standins.py'}
    assert hashlib.sha256(Path(result['archive']).read_bytes()).hexdigest()==result['sha256']


def test_identity_package_does_not_replace_existing_destination(tmp_path):
    destination=tmp_path/'package';destination.mkdir();(destination/'keep').write_text('retain')
    with pytest.raises(FileExistsError):
        module('build_package').build_package(Path.cwd(),destination,
            ARTIFACT/'Run-ReadinessCheck.ps1',ARTIFACT/'package-readme.md')
    assert (destination/'keep').read_text()=='retain'


def test_readiness_runner_denies_without_future_owner_authorization():
    pwsh=shutil.which('pwsh');assert pwsh
    result=subprocess.run([pwsh,'-NoLogo','-NoProfile','-NonInteractive','-File',
        str(ARTIFACT/'Run-ReadinessCheck.ps1'),'-ExpectedManifestSha256','0'*64],
        capture_output=True,text=True,timeout=10)
    assert result.returncode==1
    assert 'Separate owner authorization is required; readiness check not executed.' in result.stderr
    assert 'manifest' not in result.stderr.lower()


def test_readiness_runner_is_syntax_only_and_has_no_native_phase_command():
    pwsh=shutil.which('pwsh');assert pwsh
    path=str(ARTIFACT/'Run-ReadinessCheck.ps1').replace("'","''")
    script="$errors=$null; $tokens=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('"+path+"',[ref]$tokens,[ref]$errors); if ($errors.Count) { $errors | Out-String | Write-Error; exit 1 }"
    result=subprocess.run([pwsh,'-NoLogo','-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    body=(ARTIFACT/'Run-ReadinessCheck.ps1').read_text()
    assert body.count('& $GranitePython -I -B')==1
    assert "'check.py'" in body
    assert 'ownership-self-test' not in body
    assert ' native ' not in body


def synthetic_package(tmp_path,*,worker='PROXY_IDENTITY_SCHEMA = 1\n',controller='PROXY_IDENTITY_SCHEMA = 1\n'):
    package=tmp_path/'synthetic-package';package.mkdir()
    for name,source in {'worker.py':worker,'controller.py':controller,
        'windows_job.py':"raise RuntimeError('native backend must not import')\n",
        'standins.py':"raise RuntimeError('closed self-test must not import')\n"}.items():
        (package/name).write_text(source)
    shutil.copyfile('scripts/uc001_granite_acquisition_proxy/proxy.py',package/'proxy.py')
    shutil.copyfile(ARTIFACT/'check.py',package/'check.py')
    shutil.copyfile(ARTIFACT/'Run-ReadinessCheck.ps1',package/'Run-ReadinessCheck.ps1')
    (package/'README.md').write_text('Synthetic structural-check fixture only.\n')
    hashes={name:hashlib.sha256((package/name).read_bytes()).hexdigest() for name in ('controller.py','windows_job.py','worker.py','standins.py')}
    (package/'controller-config.template.json').write_text(json.dumps(dict(execution_authorized=False,helper_hashes=hashes)))
    manifest=dict(version=VERSION,purpose='offline-prepared-proxy-identity-binding',
        readiness_scope='structural_only',execution_authorized=False,
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.iterdir())})
    (package/'manifest.json').write_text(json.dumps(manifest))
    return package,hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest()


def test_structural_readiness_imports_only_explicit_worker_controller_and_never_native(tmp_path):
    package,manifest_hash=synthetic_package(tmp_path)
    result=module('check').verify_preparation(package,manifest_hash,runtime_check=lambda:None)
    assert result['preparation_integrity_passed'] is True
    assert result['proxy_identity_schema']==1
    assert result['native_binding_verified'] is False
    assert result['native_api_invoked'] is False
    assert result['live_proxy_started'] is False
    assert result['ownership_selftest_run'] is False
    assert result['forbidden_attempts']==[]
    assert result['runtime_check_injected'] is True
    assert set(result['module_paths'])=={'worker','controller'}
    assert all(Path(path).parent==package for path in result['module_paths'].values())
    assert {path.name for path in package.iterdir()}==FILES


@pytest.mark.parametrize('damage',['helper_changed','proxy_changed','schema_mismatch'])
def test_structural_readiness_rejects_hash_or_schema_gaps(tmp_path,damage):
    package,manifest_hash=synthetic_package(tmp_path,controller='PROXY_IDENTITY_SCHEMA = 2\n' if damage=='schema_mismatch' else 'PROXY_IDENTITY_SCHEMA = 1\n')
    if damage=='helper_changed':(package/'worker.py').write_text('changed')
    if damage=='proxy_changed':(package/'proxy.py').write_text('changed')
    with pytest.raises(RuntimeError):
        module('check').verify_preparation(package,manifest_hash,runtime_check=lambda:None)


def test_structural_import_process_launch_is_blocked_before_execution(tmp_path):
    package,manifest_hash=synthetic_package(tmp_path,worker="import subprocess\nsubprocess.Popen(['never-start-this'])\nPROXY_IDENTITY_SCHEMA = 1\n")
    with pytest.raises(RuntimeError,match='forbidden preparation action'):
        module('check').verify_preparation(package,manifest_hash,runtime_check=lambda:None)
