"""One renewed, gated synthetic experiment; no production integration."""
import collections, datetime, hashlib, inspect, json, os, re, shutil, signal, socket, subprocess, sys, threading, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
import prepare as acquisition
import evaluate_model as harness
from operations import clean_socket, wait_ready, guard_error, stop_owned, owned_rss
CONFIG=json.loads((HERE/"config.json").read_text())
START=datetime.datetime.strptime(CONFIG["start_utc"],"%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=datetime.timezone.utc).timestamp()
DEADLINE=START+CONFIG["total_limit_seconds"]

def write(name,obj):
    path=HERE/name;temporary=path.with_suffix(path.suffix+".tmp")
    with temporary.open("w") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n");f.flush();os.fsync(f.fileno())
    temporary.replace(path)

def event(name,**data):
    row={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"event":name,**data}
    with (HERE/"events.jsonl").open("a") as f:
        f.write(json.dumps(row,ensure_ascii=False)+"\n");f.flush();os.fsync(f.fileno())
    print(json.dumps(row,ensure_ascii=False),flush=True)

def disk_bytes(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())

def verify_freeze():
    freeze=json.loads((HERE/"freeze.json").read_text())
    for name,digest in freeze["files"].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest:raise RuntimeError("Frozen artifact changed: "+name)
    return freeze

def prepare():
    verify_freeze()
    if (HERE/"preparation.json").exists():raise RuntimeError("This attempt already has acquisition state; no repeated download/build")
    acquisition.HERE=HERE;acquisition.CONFIG=CONFIG;acquisition.DEADLINE=DEADLINE
    acquisition.STATE={"started":datetime.datetime.now(datetime.timezone.utc).isoformat(),"downloads":[],"steps":[],"temporary_root":None,"peak_temporary_bytes":0}
    def emit(name,**data):
        write("preparation.json",acquisition.STATE);event(name,**data)
        write("progress.json",{"gate":1,"state":acquisition.STATE.get("status","running"),"scratch":acquisition.STATE["temporary_root"],"cleanup":"Preserve small outputs, stop owned processes, then remove only this exact scratch tree."})
    acquisition.emit=emit
    def budget():
        error=guard_error(0,acquisition.available(),time.time(),DEADLINE,CONFIG)
        if error:raise RuntimeError(error)
        if acquisition.SCRATCH:
            used=disk_bytes(acquisition.SCRATCH)
            acquisition.STATE["peak_temporary_bytes"]=max(used,acquisition.STATE["peak_temporary_bytes"])
            if used>CONFIG["scratch_budget_bytes"]:raise RuntimeError("Temporary disk guard")
    acquisition.budget=budget
    download=acquisition.download
    def checked_download(url,dest,expected=None,size=None):
        if "codeload.github.com" in url:
            expected="6b58785f0a82898f4c3442417ff962e2d4b231b1bee5d033902ad90b27901e14";size=37887730
        return download(url,dest,expected,size)
    acquisition.download=checked_download
    try:
        acquisition.main();event("gate_1_passed")
    except BaseException as exc:
        acquisition.STATE.update(status="stopped",error=str(exc));emit("gate_1_stopped",error=str(exc));raise

def classify(path,row,deadline,seed=42):
    remaining=deadline-time.time()
    if remaining<=.25:raise RuntimeError("Inference deadline before case")
    started=time.monotonic()
    item={k:row[k] for k in ("id","language","text","expected") if k in row}
    item["set"]=row.get("set");item["seed"]=seed
    try:
        actual=harness.call(path,row["text"],seed=seed,timeout=min(CONFIG["per_case_timeout_seconds"],remaining-.1))
        item["actual"]=actual
        errors=harness.validate(actual["object"],row["text"])
        semantic=harness.semantic_score(actual["object"],row["expected"]) if isinstance(actual["object"],dict) else {"category":"invalid_output","differences":{"malformed_json":True}}
        if isinstance(actual["object"],dict) and row["language"] in harness.SUPPORTED and actual["object"].get("status")=="understood" and actual["object"].get("language")!=row["language"]:
            semantic["differences"]["language"]={"expected":row["language"],"actual":actual["object"].get("language")};semantic["category"]="incorrect"
        if isinstance(actual["object"],dict) and row["language"]=="ambiguous" and actual["object"].get("status")=="understood" and actual["object"].get("language") is not None:
            semantic["differences"]["language_ambiguity"]="shared word does not establish request language";semantic["category"]="incorrect"
        item.update(structural_errors=errors,semantic=semantic,category="invalid_output" if errors or actual["wire_finish_reason"]=="length" else semantic["category"])
    except (socket.timeout,TimeoutError):item.update(category="timeout")
    except Exception as exc:item.update(category="invalid_output",error=str(exc))
    item["wall_seconds"]=time.monotonic()-started
    return item

def evaluate():
    frozen=verify_freeze()
    if (HERE/"results.json").exists():raise RuntimeError("This attempt already has inference state; do not restart")
    prep=json.loads((HERE/"preparation.json").read_text())
    if prep.get("status")!="prepared":raise RuntimeError("Gate 1 not passed")
    scratch=Path(prep["temporary_root"])
    if not scratch.is_dir():raise RuntimeError("Owned scratch tree absent; stop without redownload")
    if acquisition.available()<CONFIG["preflight_memory_min_bytes"]:raise RuntimeError("Inference preflight RAM guard")
    if time.time()>=DEADLINE:raise RuntimeError("Renewed deadline")
    harness.CONFIG=CONFIG
    path=scratch/"inference.sock";trace=scratch/"network.trace";log=scratch/"inference.log"
    clean_socket(path,scratch)
    deadline=min(DEADLINE,time.time()+CONFIG["inference_limit_seconds"])
    write("inference_budget.json",{"start_epoch":time.time(),"deadline_epoch":deadline,"note":"Renewed authorization; includes load, smoke, calibration and all evaluation/repeats. Never renewed within attempt."})
    args=["strace","-f","-e","trace=network","-o",str(trace),prep["server"],"-m",prep["model"],"--host",str(path),"--offline","--no-webui","--no-agent","--jinja","--parallel","1","-t","2","-tb","2","-c","2048","-b","64","-ub","64","-ngl","0","--cache-type-k","f16","--cache-type-v","f16","--no-context-shift"]
    env={"PATH":"/usr/local/bin:/usr/bin:/bin","LANG":"C.UTF-8","LC_ALL":"C.UTF-8","TMPDIR":str(scratch/"tmp"),"LLAMA_CACHE":str(scratch/"cache")}
    cases=harness.old_cases()+[{**r,"set":"new_heldout"} for r in json.loads((PARENT/"heldout_v2.json").read_text())["cases"]]
    repeat_ids=json.loads((PARENT/"heldout_v2.json").read_text())["repeat_ids"]
    report={"status":"loading","configuration":CONFIG,"frozen":frozen,"runtime_args":args,"planned_cases":[{"id":r["id"],"language":r["language"],"set":r["set"]} for r in cases],"calibration":[],"evaluations":[],"repeats":[],"gates":{"1":"passed","2":"running","3":"not_run","4":"not_run"},"current_case":None,"tuning":[],"measurement_notes":"Synthetic AI-authored oracles; strace-instrumented timings/RSS. Original scorer unchanged; semantic differences remain separate from structural rejection. No independent linguistic review or evidence-translation evaluation."}
    metrics={"peak_owned_rss_bytes":0,"minimum_available_bytes":acquisition.available(),"peak_temporary_bytes":disk_bytes(scratch),"guard_error":None,"inet_activity":False,"current_case_peak_rss_bytes":0}
    stop=threading.Event();start=time.monotonic();proc=None;output=None;thread=None
    def save():
        report["metrics"]=dict(metrics)
        report["executed_ids"]=[r["id"] for r in report["evaluations"]]
        report["unexecuted_ids"]=[r["id"] for r in cases if r["id"] not in report["executed_ids"]]
        report["old_summary"]=harness.summary([r for r in report["evaluations"] if r["set"]=="old_reused"])
        report["new_summary"]=harness.summary([r for r in report["evaluations"] if r["set"]=="new_heldout"])
        report["elapsed_seconds"]=time.monotonic()-start
        write("results.json",report)
        write("progress.json",{"gate":next((k for k,v in report["gates"].items() if v=="running"),None),"state":report["status"],"current_case":report["current_case"],"executed_ids":report["executed_ids"],"scratch":str(scratch),"owned_process_group":proc.pid if proc else None,"cleanup":"Preserve small outputs, stop owned process group, remove only this exact tree."})
    def monitor():
        while not stop.wait(.2):
            rss=owned_rss(proc.pid);mem=acquisition.available()
            metrics["peak_owned_rss_bytes"]=max(metrics["peak_owned_rss_bytes"],rss)
            metrics["current_case_peak_rss_bytes"]=max(metrics["current_case_peak_rss_bytes"],rss)
            metrics["minimum_available_bytes"]=min(metrics["minimum_available_bytes"],mem)
            error=guard_error(rss,mem,time.time(),deadline,CONFIG)
            used=disk_bytes(scratch);metrics["peak_temporary_bytes"]=max(metrics["peak_temporary_bytes"],used)
            if used>CONFIG["scratch_budget_bytes"]:error="temporary_disk_limit"
            if trace.exists() and re.search(r"\bAF_INET6?\b",trace.read_text(errors="replace")):metrics["inet_activity"]=True;error="unexpected_inet_activity"
            if error:
                metrics["guard_error"]=error
                try:os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                return
    def run_case(row,collection,seed=42):
        if metrics["guard_error"]:raise RuntimeError(metrics["guard_error"])
        report["current_case"]={"id":row["id"],"set":row.get("set"),"seed":seed}
        metrics["current_case_peak_rss_bytes"]=owned_rss(proc.pid)
        save();event("case_started",**report["current_case"])
        item=classify(str(path),row,deadline,seed)
        item["peak_owned_rss_bytes"]=max(metrics["current_case_peak_rss_bytes"],owned_rss(proc.pid))
        report[collection].append(item);report["current_case"]=None
        save();event("case_completed",id=row["id"],set=row.get("set"),seed=seed,category=item["category"],seconds=round(item["wall_seconds"],3),semantic=item.get("semantic",{}).get("differences"))
        return item
    try:
        save()
        output=log.open("w");proc=subprocess.Popen(args,stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        save();event("gate_2_loading",owned_process_group=proc.pid,scratch=str(scratch))
        thread=threading.Thread(target=monitor,daemon=True);thread.start()
        report["readiness"]=wait_ready(path,proc,deadline)
        if metrics["guard_error"]:raise RuntimeError(metrics["guard_error"])
        report["loaded_owned_rss_bytes"]=owned_rss(proc.pid)
        report["gates"]["2"]="passed";report["gates"]["3"]="running";report["status"]="smoke";save();event("gate_2_passed",**report["readiness"],loaded_owned_rss_bytes=report["loaded_owned_rss_bytes"])
        smoke={"id":"SMOKE-KETTLE","set":"separate_smoke","language":"en","text":"Repair my kettle.","expected":{"status":"understood","subject":"kettle","action":"repair","goals":[],"constraints":{}}}
        if smoke["text"] in {r["text"] for r in cases}:raise RuntimeError("Smoke overlaps evaluation")
        item=run_case(smoke,"calibration")
        report["smoke"]=item
        if item["category"]!="correct":raise RuntimeError("Smoke response handling/interpretation gate failed")
        report["gates"]["3"]="passed";report["gates"]["4"]="running";report["status"]="evaluating";save();event("gate_3_passed")
        for row in json.loads((PARENT/"calibration.json").read_text())["cases"]:
            run_case({**row,"id":"CAL-"+row["language"],"set":"calibration","expected":{"status":"understood","subject":"bicycle","action":"repair","goals":[],"constraints":{"no_replacement":"true"}}},"calibration")
        for row in cases:run_case(row,"evaluations")
        for rid in repeat_ids:
            row=next(r for r in cases if r["id"]==rid)
            for seed in [42,43]:run_case({**row,"set":"repeat_reused"},"repeats",seed)
        report["gates"]["4"]="passed";report["status"]="completed"
    except BaseException as exc:
        report["status"]="stopped";report["error"]=str(exc)
        for gate,state in report["gates"].items():
            if state=="running":report["gates"][gate]="stopped"
        event("attempt_stopped",error=str(exc))
    finally:
        stop.set()
        if thread:thread.join(timeout=2)
        if proc:stop_owned(proc);report["owned_process_exit_code"]=proc.returncode
        if output:output.close()
        if trace.exists():
            text=trace.read_text(errors="replace");(HERE/"network_observed.txt").write_text(text)
            report["network_observation"]={"trace_lines":len(text.splitlines()),"inet_activity":bool(re.search(r"\bAF_INET6?\b",text)),"scope":"Owned straced process tree only; not a general absence-of-telemetry claim."}
        if log.exists():(HERE/"inference_log_tail.txt").write_text("\n".join(log.read_text(errors="replace").splitlines()[-120:])+"\n")
        save();event("attempt_finished",status=report["status"],evaluated=len(report["evaluations"]),repeats=len(report["repeats"]),metrics=metrics)
    return 0 if report["status"]=="completed" else 1

if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in {"prepare","evaluate"}:raise SystemExit("Use prepare or evaluate")
    if sys.argv[1]=="prepare":prepare()
    else:raise SystemExit(evaluate())
