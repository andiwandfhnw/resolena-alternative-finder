"""Hash/syntax/schema preparation check only; never execute the proxy or native APIs."""
import argparse
import ast
import ctypes
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

VERSION = 'uc001-granite-proxy-identities-v1'
PROXY_SHA256 = 'a7c62f83356636bea839633382bb62a3e53bcce466caea7b32226cece1e7bb1d'
HELPERS = {'controller.py','windows_job.py','worker.py','standins.py'}
FILES = HELPERS | {'proxy.py','check.py','controller-config.template.json',
                  'Run-ReadinessCheck.ps1','README.md','manifest.json'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strict_json(data):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise RuntimeError('duplicate JSON key')
            result[key]=value
        return result
    return json.loads(data,object_pairs_hook=pairs)


def _runtime():
    if os.name!='nt' or sys.version_info[:3]!=(3,12,11) or ctypes.sizeof(ctypes.c_void_p)!=8:
        raise RuntimeError('approved Windows x64 Python 3.12.11 required')


def verify_preparation(package_root, expected_manifest_sha256, *, runtime_check=None):
    package=Path(package_root).resolve(strict=True)
    (runtime_check or _runtime)()
    if not re.fullmatch('[0-9a-f]{64}',expected_manifest_sha256):
        raise RuntimeError('explicit manifest SHA-256 required')
    if {p.name for p in package.iterdir()}!=FILES or any(not (package/name).is_file() or (package/name).is_symlink() for name in FILES):
        raise RuntimeError('unexpected or missing preparation package entry')
    if digest(package/'manifest.json')!=expected_manifest_sha256:
        raise RuntimeError('manifest hash differs')
    manifest=strict_json((package/'manifest.json').read_text())
    if (manifest.get('version')!=VERSION or manifest.get('purpose')!='offline-prepared-proxy-identity-binding'
            or manifest.get('readiness_scope')!='structural_only' or manifest.get('execution_authorized') is not False
            or set(manifest.get('files',{}))!=FILES-{'manifest.json'}):
        raise RuntimeError('preparation scope differs')
    for name,expected in manifest['files'].items():
        if digest(package/name)!=expected:raise RuntimeError('package hash differs:'+name)
    if digest(package/'proxy.py')!=PROXY_SHA256:
        raise RuntimeError('accepted proxy bytes differ')
    config=strict_json((package/'controller-config.template.json').read_text())
    if config.get('execution_authorized') is not False or set(config.get('helper_hashes',{}))!=HELPERS:
        raise RuntimeError('native execution must remain inactive')
    if any(config['helper_hashes'][name]!=manifest['files'][name] for name in HELPERS):
        raise RuntimeError('inactive helper manifest differs')
    for name in sorted(FILES):
        if name.endswith('.py'):ast.parse((package/name).read_text(),filename=str(package/name))

    active=True
    forbidden=[]
    def audit(event,args):
        if active and (event in {'subprocess.Popen','os.system','os.posix_spawn','socket.connect',
                                'socket.bind','ctypes.dlopen','ctypes.dlsym'}
                       or event.startswith(('os.exec','os.spawn'))):
            forbidden.append(event)
            raise RuntimeError('forbidden preparation action:'+event)
    sys.addaudithook(audit)
    modules={}
    loaded=[]
    previous_bytecode=sys.dont_write_bytecode
    sys.dont_write_bytecode=True
    try:
        for name in ('worker','controller'):
            module_path=package/(name+'.py')
            qualified='_granite_structural_readiness_'+name+'_'+manifest['files'][name+'.py'][:12]
            spec=importlib.util.spec_from_file_location(qualified,module_path)
            module=importlib.util.module_from_spec(spec)
            previous=sys.modules.get(qualified)
            sys.modules[qualified]=module;loaded.append((qualified,previous))
            spec.loader.exec_module(module)
            if Path(module.__file__).resolve()!=module_path or getattr(module,'PROXY_IDENTITY_SCHEMA',None)!=1:
                raise RuntimeError('explicit module/schema mismatch:'+name)
            modules[name]=str(module_path)
        if forbidden:raise RuntimeError('forbidden preparation action recorded')
    finally:
        active=False
        sys.dont_write_bytecode=previous_bytecode
        for name,previous in loaded:
            if previous is None:sys.modules.pop(name,None)
            else:sys.modules[name]=previous
    return dict(preparation_integrity_passed=True,proxy_identity_schema=1,
        native_binding_verified=False,native_api_invoked=False,live_proxy_started=False,
        ownership_selftest_run=False,acquisition_or_build=False,gpu_model_inference=False,
        resource_fit_established=False,forbidden_attempts=forbidden,module_paths=modules,
        runtime_check_injected=runtime_check is not None,windows_execution=os.name=='nt',
        python_version=sys.version.split()[0],timestamp_utc=datetime.now(timezone.utc).isoformat())


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-manifest-sha256',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    package=Path(__file__).resolve().parent
    output=Path(args.output).resolve()
    if output.parent!=package.parent or not output.name.startswith('readiness-proxy-identities-'):
        raise RuntimeError('fresh sibling readiness directory required')
    output.mkdir(exist_ok=False)
    try:
        result=verify_preparation(package,args.expected_manifest_sha256)
        exit_code=0
    except BaseException as error:
        result=dict(preparation_integrity_passed=False,native_binding_verified=False,
                    native_api_invoked=False,live_proxy_started=False,ownership_selftest_run=False,
                    acquisition_or_build=False,gpu_model_inference=False,
                    failure_reason=type(error).__name__+': '+str(error))
        exit_code=1
    with (output/'result.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps(result,sort_keys=True))
    return exit_code


if __name__=='__main__':
    raise SystemExit(main())
