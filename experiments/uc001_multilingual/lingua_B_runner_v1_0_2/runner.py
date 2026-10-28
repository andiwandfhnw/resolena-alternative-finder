import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from common import HERE, REPO, ORIGINAL, VERIFIER, OLD_RUN, LIMITS, write, append, validate_context, check_limits, deadline


def process(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().rsplit(') ',1)[1].split()
        status=Path(f'/proc/{pid}/status').read_text().splitlines()
        mem={l.split(':')[0]:int(l.split()[1])*1024 for l in status if l.startswith(('VmRSS:','VmHWM:'))}
        return {'pid':pid,'pgrp':int(fields[2]),'start_ticks':int(fields[19]),
                'rss':mem.get('VmRSS',0),'hwm':mem.get('VmHWM',0),
                'threads':next((int(l.split()[1]) for l in status if l.startswith('Threads:')),0)}
    except (FileNotFoundError,ProcessLookupError):return None


def stop_owned(child,ticks):
    observed=process(child.pid)
    if observed is None:return
    if observed['start_ticks']!=ticks or observed['pgrp']!=child.pid:
        raise RuntimeError('ownership mismatch: no signal sent')
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        observed=process(child.pid)
        if observed and observed['start_ticks']==ticks and observed['pgrp']==child.pid:
            os.killpg(child.pid,signal.SIGKILL)
        child.wait(timeout=2)


def scratch(c):
    logical=allocated=0;seen=set()
    for root in [Path(c['run_dir']),HERE,ORIGINAL,VERIFIER,OLD_RUN]:
        for p in root.rglob('*'):
            try:
                st=p.lstat();key=(st.st_dev,st.st_ino)
                if key in seen:continue
                seen.add(key)
                if not p.is_dir():logical+=st.st_size
                allocated+=st.st_blocks*512
            except FileNotFoundError:pass
    return {'logical_bytes':logical,'allocated_bytes':allocated}


def monitor(child,c,phase,measure_scratch):
    root=Path(c['run_dir']);identity=process(child.pid)
    ticks=identity['start_ticks'] if identity else None
    peak_rss=peak_hwm=peak_disk=0;failure=None;last_disk=0;disk=measure_scratch()
    try:
        while True:
            now=time.monotonic();owned=[]
            for p in Path('/proc').iterdir():
                if p.name.isdigit():
                    v=process(int(p.name))
                    if v and (v['pgrp']==child.pid or v['pid']==os.getpid()):owned.append(v)
            rss=sum(v['rss'] for v in owned);hwm=sum(v['hwm'] for v in owned)
            peak_rss=max(peak_rss,rss);peak_hwm=max(peak_hwm,hwm)
            if now-last_disk>=.25:disk=measure_scratch();last_disk=now
            peak_disk=max(peak_disk,max(disk.values()))
            append(root/'resources.jsonl',{'phase':phase,'monotonic':now,'owned':owned,'rss':rss,'hwm_sum':hwm,'scratch':disk})
            check_limits(now,c['deadline_monotonic'],max(rss,hwm),max(disk.values()))
            if time.time()>=c['deadline_wall_unix']:raise RuntimeError('wall deadline expired')
            if child.poll() is not None:break
            time.sleep(.05)
        if child.returncode:raise RuntimeError(phase+' exit '+str(child.returncode))
    except BaseException as exc:
        failure=str(exc)
        if child.poll() is None:stop_owned(child,ticks)
        raise
    finally:
        write(root/(phase+'.exit.json'),{'phase':phase,'identity':identity,'exit_code':child.poll(),
              'failure':failure,'process_absent':process(child.pid) is None,
              'peak_owned_rss_bytes':peak_rss,'peak_hwm_sum_bytes':peak_hwm,'peak_scratch_bytes':peak_disk,
              'end_monotonic':time.monotonic()})


def phase_commands(context):
    root=context.parent
    phases=[(name,[sys.executable,'-B',str(HERE/'phase.py'),'--phase',name,'--context',str(context)]) for name in ['verify','venv','install']]
    return phases+[('detector',[str(root/'venv/bin/python'),'-B',str(HERE/'worker.py'),'--context',str(context)])]


def preflight(root):
    mem={l.split(':')[0]:int(l.split()[1])*1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemAvailable:','MemTotal:'))}
    cg={n:(Path('/sys/fs/cgroup')/n).read_text().strip() for n in ['memory.max','memory.current','memory.events','memory.pressure']}
    available=mem['MemAvailable']
    if cg['memory.max']!='max':available=min(available,int(cg['memory.max'])-int(cg['memory.current']))
    s=os.statvfs(root);free=s.f_bavail*s.f_frsize
    sample={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'memory':mem,'cgroup':cg,
            'effective_available_bytes':available,'disk_free_bytes':free,'minimum_headroom_bytes':1610612736,
            'cpu_affinity':sorted(os.sched_getaffinity(0))}
    write(root/'preflight.json',sample)
    if available<1610612736 or free<1610612736:raise RuntimeError('preflight headroom failure')


def main():
    path=Path(sys.argv[sys.argv.index('--context')+1]).resolve();c=validate_context(json.loads(path.read_text()),path)
    root=path.parent
    freeze=json.loads((HERE/'freeze.json').read_text())
    for name,h in freeze['files'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=h:raise RuntimeError('runner freeze mismatch: '+name)
    for name,h in freeze['references'].items():
        if hashlib.sha256((REPO/name).read_bytes()).hexdigest()!=h:raise RuntimeError('provenance mismatch: '+name)
    if hashlib.sha256((HERE/'freeze.json').read_bytes()).hexdigest()!=c['freeze_sha256']:raise RuntimeError('context freeze mismatch')
    with (root/'execution-started.json').open('x') as stream:json.dump({'pid':os.getpid(),'identity':process(os.getpid()),'context':c},stream,indent=2)
    env=dict(os.environ)
    env.update({k:'2' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','RAYON_NUM_THREADS']})
    env.update({'PYTHONDONTWRITEBYTECODE':'1','PIP_CONFIG_FILE':'/dev/null','PIP_DISABLE_PIP_VERSION_CHECK':'1',
                'TMPDIR':str(root/'tmp'),'LINGUA_RUN_CONTEXT':str(path),
                'LINGUA_CONTEXT_SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'LINGUA_DEADLINE_MONOTONIC':str(c['deadline_monotonic']),'LINGUA_LIMITS_JSON':json.dumps(c['limits'])})
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2]);(root/'tmp').mkdir()
    failure=None;completed=[]
    try:
        preflight(root)
        for name,command in phase_commands(path):
            deadline(c)
            with (root/(name+'.stdout.log')).open('xb') as out,(root/(name+'.stderr.log')).open('xb') as err:
                child=subprocess.Popen(command,cwd=REPO,env=env,stdout=out,stderr=err,start_new_session=True)
                append(root/'children.jsonl',{'phase':name,'command':command,'identity':process(child.pid)})
                monitor(child,c,name,lambda:scratch(c))
            completed.append(name)
    except BaseException as exc:failure=str(exc)
    summaries=[json.loads(p.read_text()) for p in root.glob('*.exit.json')]
    remaining=[]
    for item in summaries:
        identity=item.get('identity')
        if identity:
            v=process(identity['pid'])
            if v and v['start_ticks']==identity['start_ticks']:remaining.append(v)
    summary={'status':'operational_failure' if failure else 'completed_fixed_sample','failure':failure,
        'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_window_seconds':time.monotonic()-c['started_monotonic'],
        'deadline_utc':c['deadline_utc'],'completed_phases':completed,'phase_exits':summaries,
        'remaining_owned_processes':remaining,'cleanup':'Owned processes exited; artifacts/environment preserved; no deletion.',
        'final_scratch':scratch(c),'context_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    write(root/'closeout.json',summary);print(json.dumps(summary,indent=2))
    return 1 if failure or remaining else 0


if __name__=='__main__':sys.exit(main())
