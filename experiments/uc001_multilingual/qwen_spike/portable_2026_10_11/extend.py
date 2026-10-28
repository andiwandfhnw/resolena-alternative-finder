import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from portable_checks import verify_flags

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = HERE.parents[3]
PRIOR = PARENT/'restart_2026_10_11'
OLD = PARENT/'calibration_B_2026_10_11'
WORK = ROOT/'build/qwen-portable-20261011'
sys.path.insert(0,str(PARENT)); sys.path.insert(0,str(PRIOR))
import operations


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name,value):
    path=HERE/name; path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        json.dump(value,f,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'): return int(line.split()[1])*1024
    raise RuntimeError('MemAvailable missing')


def main():
    if (HERE/'extension_execution.json').exists() or WORK.exists():
        raise RuntimeError('Extension already has state; no retry or duplicate build')
    started=time.time(); deadline=started+2700; build_deadline=started+1800
    state={'utc':utc(),'start_epoch':started,'deadline_epoch':deadline,'build_deadline_epoch':build_deadline,
           'pid':os.getpid(),'status':'preflight','calibration_started':False,'downloads':0,'retries':0,
           'build_limit_seconds':1800,'calibration_limit_seconds':900,'total_limit_seconds':2700}
    write('extension_execution.json',state)
    guard={'peak_owned_rss_bytes':0,'minimum_available_bytes':available(),'peak_scratch_bytes':0,'failure':None}
    proc=None; lock=None; code=1; preserved={}; scratch=None; finished=False
    try:
        config=json.loads((PRIOR/'config.json').read_text())
        for name,digest in json.loads((HERE/'operational_freeze.json').read_text())['files'].items():
            if sha(HERE/name)!=digest: raise RuntimeError('Extension frozen file changed: '+name)
        prep=json.loads((PRIOR/'preparation.json').read_text()); scratch=Path(prep['artifact_tree'])
        source=next(scratch.glob('llama.cpp-d81235049384534c167caea52b85a694f6103d14'))
        cmake=scratch/'cmake-3.31.6-linux-x86_64/bin/cmake'
        assert ROOT.is_relative_to(Path('/workspaces')) and os.uname().machine=='x86_64'
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()=='a6b2479c3d82ff5d9987a73d310a3a4eff064455'
        assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip()=='specify/phase-1-uc-001'
        assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip()
        spec=importlib.util.spec_from_file_location('extension_owner',PRIOR/'restart.py')
        owner=importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)
        lock=(scratch/'restart-owner.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        active=owner.active_processes(scratch,WORK)
        if active: raise RuntimeError('Experiment process already active: '+json.dumps(active))
        preserved={str(p.relative_to(PARENT)):sha(p) for root in [PRIOR,OLD,PARENT/'renewed_2026_10_11']
                   for p in root.rglob('*') if p.is_file() and 'build' not in p.relative_to(root).parts and '__pycache__' not in p.parts}
        manifest=json.loads((ROOT/'build/checkpoints/uc001-machine-change-20261011-1427/artifact_manifest.json').read_text())
        source_entries=[e for e in manifest['files'] if e['type']=='file' and str(ROOT/e['path']).startswith(str(source)+'/')]
        for entry in source_entries:
            if sha(ROOT/entry['path'])!=entry['sha256']: raise RuntimeError('Pinned source changed: '+entry['path'])
        if sha(prep['model'])!=config['model']['sha256']: raise RuntimeError('Pinned model changed')
        original_server_sha=json.loads((PRIOR/'verification.json').read_text())['server_sha256']
        if sha(prep['server'])!=original_server_sha: raise RuntimeError('Original binary changed')
        for name,digest in json.loads((OLD/'freeze.json').read_text())['files'].items():
            if sha(OLD/name)!=digest: raise RuntimeError('Frozen calibration input changed: '+name)
        from memory_preflight import enforce_preflight
        enforce_preflight(available,config,scratch,write)
        fields=dict(line.split(':',1) for line in Path('/proc/cpuinfo').read_text().split('\n\n')[0].splitlines() if ':' in line)
        cpu_flags=set(fields['flags\t'].split()) if 'flags\t' in fields else set(next(v for k,v in fields.items() if k.strip()=='flags').split())
        hardware={'utc':utc(),'cpu_model':next(v.strip() for k,v in fields.items() if k.strip()=='model name'),
                  'cpu_flags':sorted(cpu_flags),'affinity':sorted(os.sched_getaffinity(0)),
                  'meminfo':{k:v.strip() for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())},
                  'cgroup':{n:(Path('/sys/fs/cgroup')/n).read_text().strip() for n in ['memory.max','memory.high','memory.current','memory.events','memory.pressure']},
                  'original_selector':'2 cores / 8 GB RAM / 32 GB storage','current_selector':'4 cores / 16 GB RAM / 32 GB storage',
                  'cache_note':'Preflight hashes may warm OS file cache; no cache flush; inference retains cache_prompt=false and records server timings/cache usage'}
        if len(hardware['affinity'])!=4: raise RuntimeError('Expected current four-core machine')
        write('hardware.json',hardware)
        WORK.mkdir(); (WORK/'original_native').mkdir()
        if subprocess.run(['git','check-ignore','--quiet',str(WORK)],cwd=ROOT).returncode: raise RuntimeError('Build storage not Git-ignored')
        originals=[(Path(prep['server']),'llama-server'),(scratch/'build/CMakeCache.txt','CMakeCache.txt'),
                   (scratch/'build/ggml/src/CMakeFiles/ggml-cpu.dir/flags.make','cpu-flags.make'),
                   (PRIOR/'build.log','restart-build.log')]
        originals.extend((p,p.name) for p in scratch.iterdir() if p.is_file() and p.suffix in {'.log','.trace'})
        copies=[]
        for original,name in originals:
            if not original.exists(): raise RuntimeError('Original preservation file absent: '+str(original))
            target=WORK/'original_native'/name; shutil.copy2(original,target)
            copies.append({'original':str(original),'copy':str(target),'sha256':sha(original)})
            if sha(target)!=copies[-1]['sha256']: raise RuntimeError('Original backup mismatch')
        write('original_preservation.json',{'files':copies,'model_reused':prep['model'],'original_tree_retained':str(scratch)})
        options=[f for f in config['runtime']['flags'] if f!='-DGGML_NATIVE=ON']
        options+=['-DGGML_NATIVE=OFF','-DGGML_CPU_ALL_VARIANTS=OFF','-DGGML_BACKEND_DL=OFF','-DGGML_CCACHE=OFF',
                  '-DGGML_SSE42=ON','-DGGML_AVX=ON','-DGGML_AVX2=ON','-DGGML_FMA=ON','-DGGML_F16C=ON','-DGGML_BMI2=ON',
                  '-DGGML_AVX_VNNI=OFF','-DGGML_AVX512=OFF','-DGGML_AVX512_VBMI=OFF','-DGGML_AVX512_VNNI=OFF','-DGGML_AVX512_BF16=OFF',
                  '-DGGML_AMX_TILE=OFF','-DGGML_AMX_INT8=OFF','-DGGML_AMX_BF16=OFF',
                  '-DCMAKE_C_FLAGS=-march=x86-64 -mtune=generic','-DCMAKE_CXX_FLAGS=-march=x86-64 -mtune=generic',
                  '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DFETCHCONTENT_FULLY_DISCONNECTED=ON']
        write('build_configuration.json',{'utc':utc(),'source':str(source),'runtime_pin':config['runtime']['commit'],
             'model_pin':config['model'],'source_files_verified':len(source_entries),'options':options,'parallelism':1,
             'documented_option_sources':[str(source/'ggml/CMakeLists.txt'),str(source/'ggml/src/ggml-cpu/CMakeLists.txt'),str(source/'docs/build.md')],
             'required_features':['sse4_2','avx','avx2','fma','f16c','bmi2'],'inference_threads':2,'original_build_preserved':True})
        build=WORK/'compiled'

        def step(name,args,limit):
            nonlocal proc
            if time.time()>=limit: raise RuntimeError('Deadline before '+name)
            state.update(status=name,current_command=args,owned_process_group=None); write('extension_execution.json',state)
            start=time.monotonic(); log=HERE/(name+'.log'); trace=WORK/(name+'-network.trace')
            env={'PATH':'/usr/local/bin:/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','TMPDIR':str(WORK/'tmp')}
            (WORK/'tmp').mkdir(exist_ok=True)
            with log.open('x') as output:
                proc=subprocess.Popen(['strace','-f','-e','trace=network','-o',str(trace),*args],cwd=ROOT,
                    env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
                state['owned_process_group']=proc.pid; write('extension_execution.json',state)
                while proc.poll() is None:
                    rss=operations.owned_rss(proc.pid); mem=available()
                    guard['peak_owned_rss_bytes']=max(guard['peak_owned_rss_bytes'],rss)
                    guard['minimum_available_bytes']=min(guard['minimum_available_bytes'],mem)
                    size=sum(p.stat().st_size for root in [scratch,WORK,HERE] for p in root.rglob('*') if p.is_file())
                    guard['peak_scratch_bytes']=max(guard['peak_scratch_bytes'],size)
                    failure=operations.guard_error(rss,mem,time.time(),limit,config)
                    if size>config['scratch_budget_bytes']: failure='scratch_limit'
                    if trace.exists() and re.search(r'\bAF_INET6?\b',trace.read_text(errors='replace')): failure='unexpected_network_activity'
                    write('build_resources.json',{'utc':utc(),**guard,'owned_rss_bytes':rss,'available_bytes':mem,'scratch_bytes':size})
                    write('progress.json',{'utc':utc(),'phase':name,'elapsed_seconds':time.time()-started,'deadline_epoch':deadline,
                        'owned_process_group':proc.pid,'log_bytes':log.stat().st_size,'resource_failure':failure})
                    if failure:
                        guard['failure']=failure; operations.stop_owned(proc); raise RuntimeError(failure)
                    time.sleep(1)
                row={'name':name,'command':args,'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start}
                write(name+'_exit.json',row)
                if proc.returncode: raise RuntimeError(name+' failed: '+str(proc.returncode))
                proc=None; return row

        step('configure',[str(cmake),'-S',str(source),'-B',str(build),*options],build_deadline)
        commands=json.loads((build/'compile_commands.json').read_text())
        flags=verify_flags(commands,cpu_flags)
        write('compiler_flags_verification.json',{**flags,'utc':utc(),'compile_commands_sha256':sha(build/'compile_commands.json'),
             'cache_sha256':sha(build/'CMakeCache.txt')})
        step('build',[str(cmake),'--build',str(build),'--target','llama-server','-j1'],build_deadline)
        flags=verify_flags(json.loads((build/'compile_commands.json').read_text()),cpu_flags)
        for entry in source_entries:
            if sha(ROOT/entry['path'])!=entry['sha256']: raise RuntimeError('Pinned source changed during build')
        server=build/'bin/llama-server'
        step('binary_version',[str(server),'--version'],min(deadline,time.time()+10))
        write('portable_verification.json',{'utc':utc(),'server_sha256':sha(server),'compiler_flags':flags,'model_sha256':config['model']['sha256'],
             'version_exit_code':0,'native_cpu_specific_flags_absent':True,'runtime_source_pin':config['runtime']['commit'],
             'metadata_note':'Version output may show enclosing repository metadata; actual runtime provenance is pinned unchanged source plus build manifest'})
        write('portable_preparation.json',{**prep,'server':str(server),'original_server':prep['server'],'portable_root':str(WORK),'source':str(source)})
        fcntl.flock(lock,fcntl.LOCK_UN); lock.close(); lock=None
        state.update(status='calibration',calibration_invoked=True,owned_process_group=None); write('extension_execution.json',state)
        from calibrate_portable import load_runner
        runner=load_runner(); code=runner['main'](); state['calibration_return_code']=code; finished=True
        state['status']='completed_pass' if code==0 else 'completed_calibration_failure'
    except BaseException as exc:
        state.update(status='stopped',error=str(exc),exception_type=type(exc).__name__)
    finally:
        if proc is not None: operations.stop_owned(proc)
        if lock is not None: fcntl.flock(lock,fcntl.LOCK_UN); lock.close()
        state.update(finished_utc=utc(),elapsed_seconds=time.time()-started,driver_exit_code=code,
             calibration_started=(HERE/'execution.json').exists(),
             prior_records_preserved=all(sha(PARENT/name)==digest for name,digest in preserved.items()),
             design_acceptance='pending',return_to_original_completed=False,build_resources=guard)
        write('extension_closeout.json',state); write('extension_execution.json',state)
        print(json.dumps(state),flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
