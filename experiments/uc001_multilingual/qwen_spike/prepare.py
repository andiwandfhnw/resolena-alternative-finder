"""Approved bounded acquisition/build; no app or global dependency changes."""
import datetime, hashlib, json, os, shutil, signal, subprocess, tarfile, tempfile, time, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
CONFIG=json.loads((HERE/"config.json").read_text())
START=datetime.datetime.strptime(CONFIG["start_utc"],"%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=datetime.timezone.utc).timestamp()
DEADLINE=START+CONFIG["total_limit_seconds"]
STATE={"started":datetime.datetime.now(datetime.timezone.utc).isoformat(),"downloads":[],"steps":[],"temporary_root":None}
SCRATCH=None

def available():
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):return int(line.split()[1])*1024

def tree_rss(group):
    total=0
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():continue
        try:
            fields=(p/"stat").read_text().rsplit(")",1)[1].split()
            if int(fields[2])==group:
                for line in (p/"status").read_text().splitlines():
                    if line.startswith("VmRSS:"):total+=int(line.split()[1])*1024
        except (FileNotFoundError,ProcessLookupError,PermissionError,ValueError):pass
    return total

def emit(event,**data):
    print(json.dumps({"event":event,**data}),flush=True)
    (HERE/"preparation.json").write_text(json.dumps(STATE,indent=2)+"\n")

def budget():
    if time.time()>=DEADLINE:raise RuntimeError("Two-hour deadline reached")
    if available()<CONFIG["available_memory_min_bytes"]:raise RuntimeError("Available RAM guard")
    if SCRATCH:
        used=sum(p.stat().st_size for p in SCRATCH.rglob("*") if p.is_file())
        if used>CONFIG["scratch_budget_bytes"]:raise RuntimeError("Temporary disk guard")

def download(url,dest,expected=None,size=None):
    budget();h=hashlib.sha256();count=0;start=time.monotonic();last=0
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Resolena-approved-synthetic-experiment"}),timeout=30) as response, dest.open("wb") as f:
        while True:
            block=response.read(4*1024*1024)
            if not block:break
            f.write(block);h.update(block);count+=len(block)
            if count+sum(d["bytes"] for d in STATE["downloads"])>CONFIG["download_budget_bytes"]:raise RuntimeError("Download guard")
            budget()
            if count-last>128*1024*1024:emit("download_progress",file=dest.name,bytes=count);last=count
    digest=h.hexdigest()
    if expected and digest!=expected:raise RuntimeError("Artifact checksum mismatch")
    if size and size!=count:raise RuntimeError("Artifact size mismatch")
    STATE["downloads"].append({"url":url,"file":dest.name,"bytes":count,"sha256":digest,"elapsed_seconds":time.monotonic()-start})
    emit("download_verified",file=dest.name,bytes=count,sha256=digest)

def command(args,name,limit=1800):
    log=SCRATCH/(name+".log");env={"PATH":"/usr/local/bin:/usr/bin:/bin","LANG":"C.UTF-8","LC_ALL":"C.UTF-8","TMPDIR":str(SCRATCH/"tmp"),"LLAMA_CACHE":str(SCRATCH/"cache")}
    start=time.monotonic();peak=0;minimum=available()
    with log.open("w") as output:
        proc=subprocess.Popen(args,stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:
            while proc.poll() is None:
                budget();rss=tree_rss(proc.pid);peak=max(peak,rss);minimum=min(minimum,available())
                if rss>CONFIG["rss_limit_bytes"]:raise RuntimeError("Owned-process RSS guard")
                if time.monotonic()-start>limit:raise RuntimeError(name+" timeout")
                time.sleep(.2)
            if proc.returncode:raise RuntimeError(name+" failed; see preserved log tail")
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            STATE["steps"].append({"name":name,"args":args,"exit_code":proc.returncode,"elapsed_seconds":time.monotonic()-start,"peak_owned_rss_bytes":peak,"minimum_available_bytes":minimum})
            (HERE/(name+"_log_tail.txt")).write_text("\n".join(log.read_text(errors="replace").splitlines()[-80:])+"\n")
            emit("command_finished",step=name,exit_code=proc.returncode,peak_rss_bytes=peak)

def main():
    global SCRATCH
    if available()<CONFIG["preflight_memory_min_bytes"]:raise RuntimeError("Preflight RAM below conservative fit guard")
    if shutil.disk_usage("/tmp").free<CONFIG["scratch_budget_bytes"]:raise RuntimeError("Preflight disk guard")
    SCRATCH=Path(tempfile.mkdtemp(prefix="resolena-qwen-spike-",dir="/tmp"));STATE["temporary_root"]=str(SCRATCH)
    for p in ["tmp","cache"]: (SCRATCH/p).mkdir()
    emit("scratch_created",path=str(SCRATCH))
    cm=CONFIG["cmake"];archive=SCRATCH/cm["file"]
    download("https://github.com/Kitware/CMake/releases/download/v"+cm["version"]+"/"+cm["file"],archive,cm["sha256"],cm["bytes"])
    with tarfile.open(archive) as tar:tar.extractall(SCRATCH,filter="data")
    archive.unlink()
    cmake=SCRATCH/"cmake-3.31.6-linux-x86_64/bin/cmake"
    command([str(cmake),"--version"],"cmake_version",30)
    commit=CONFIG["runtime"]["commit"];source_archive=SCRATCH/"source.tar.gz"
    download("https://codeload.github.com/ggml-org/llama.cpp/tar.gz/"+commit,source_archive)
    with tarfile.open(source_archive) as tar:tar.extractall(SCRATCH,filter="data")
    source_archive.unlink()
    source=SCRATCH/("llama.cpp-"+commit);build=SCRATCH/"build"
    if not source.is_dir():raise RuntimeError("Source commit archive path mismatch")
    command([str(cmake),"-S",str(source),"-B",str(build),*CONFIG["runtime"]["flags"]],"configure",120)
    command([str(cmake),"--build",str(build),"--target","llama-server","-j1"],"build",CONFIG["build_limit_seconds"])
    command([str(build/"bin/llama-server"),"--version"],"runtime_version",30)
    model=CONFIG["model"];dest=SCRATCH/model["file"]
    download("https://huggingface.co/"+model["repo"]+"/resolve/"+model["revision"]+"/"+model["file"],dest,model["sha256"],model["bytes"])
    STATE.update({"status":"prepared","server":str(build/"bin/llama-server"),"model":str(dest),"finished":datetime.datetime.now(datetime.timezone.utc).isoformat()})
    emit("prepared",server=STATE["server"],model=str(dest),remaining_seconds=int(DEADLINE-time.time()))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        STATE["status"]="stopped";STATE["error"]=str(exc);emit("stopped",error=str(exc));raise
