"""Operational safeguards for the isolated renewed experiment."""
import http.client, os, signal, socket, stat, time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from evaluate_model import LocalHTTP
from prepare import tree_rss as owned_rss

def clean_socket(path,root):
    path=Path(path);root=Path(root)
    if path.parent.resolve()!=root.resolve():raise RuntimeError("Socket is outside owned scratch root")
    try:info=path.lstat()
    except FileNotFoundError:return False
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid!=os.getuid():raise RuntimeError("Refuse non-owned/non-socket path")
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as probe:
        probe.settimeout(.2)
        try:probe.connect(str(path))
        except ConnectionRefusedError:path.unlink();return True
        except FileNotFoundError:return False
        else:raise RuntimeError("Refuse replacing a live socket")

def wait_ready(path,proc,deadline,startup_limit=90,poll=.2):
    start=time.monotonic();attempts=0;last=None
    while True:
        if time.time()>=deadline:raise RuntimeError("Readiness deadline")
        if proc.poll() is not None:raise RuntimeError("Server exited before readiness: "+str(proc.returncode if hasattr(proc,"returncode") else proc.poll()))
        if time.monotonic()-start>=startup_limit:raise RuntimeError("Readiness timeout; last health "+str(last))
        if Path(path).exists():
            health=LocalHTTP(str(path),min(2,max(.01,deadline-time.time())))
            try:
                health.request("GET","/health");response=health.getresponse();body=response.read();attempts+=1;last=response.status
                if response.status==200:return {"seconds":time.monotonic()-start,"health_attempts":attempts,"health_status":200,"body":body.decode(errors="replace")}
                if response.status!=503:raise RuntimeError("Unexpected health status "+str(response.status))
            except (OSError,http.client.HTTPException):pass
            finally:health.close()
        time.sleep(poll)

def guard_error(rss,available,now,deadline,limits):
    if rss>limits["rss_limit_bytes"]:return "owned_rss_limit"
    if available<limits["available_memory_min_bytes"]:return "available_ram_limit"
    if now>=deadline:return "deadline"
    return None

def stop_owned(proc):
    if proc.poll() is not None:return
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:proc.wait(timeout=5)
    except __import__("subprocess").TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);proc.wait()
