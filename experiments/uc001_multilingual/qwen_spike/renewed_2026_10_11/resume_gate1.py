"""Recover the interrupted pre-model build once within unchanged authorization."""
import hashlib, json, os, shutil, sys, tempfile, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run
if (HERE/"resumption.json").exists():raise SystemExit("One build recovery already recorded; stop")
old=json.loads((HERE/"preparation.json").read_text())
prior=Path(old["temporary_root"])
if prior.exists():raise SystemExit("Previous tree still exists; do not reacquire")
base=HERE/"build"
if run.acquisition.available()<run.CONFIG["preflight_memory_min_bytes"]:raise SystemExit("RAM preflight")
if shutil.disk_usage(HERE).free<run.CONFIG["scratch_budget_bytes"]:raise SystemExit("Workspace disk preflight")
if time.time()>=run.DEADLINE:raise SystemExit("Original renewed deadline")
predicted=sum(d["bytes"] for d in old["downloads"])+1927324705
if predicted>run.CONFIG["download_budget_bytes"]:raise SystemExit("Cumulative download budget")
history=HERE/"interruption_1";history.mkdir()
for name in ["preparation.json","progress.json","freeze.json","cmake_version_log_tail.txt","configure_log_tail.txt"]:
    path=HERE/name
    if path.exists():shutil.copyfile(path,history/name)
record={"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"reason":"Prior execution session unavailable and exact /tmp tree absent; removal cause unknown. No build success/model download/startup recorded.","prior_root":str(prior),"recorded_download_bytes":sum(d["bytes"] for d in old["downloads"]),"predicted_cumulative_bytes":predicted,"scratch_parent":str(base),"original_deadline_epoch":run.DEADLINE,"deadline_renewed":False,"resource_limits_changed":False,"model_or_prompt_or_cases_changed":False,"single_recovery":True}
run.write("resumption.json",record)
base.mkdir(exist_ok=True)
real_mkdtemp=run.acquisition.tempfile.mkdtemp
def workspace_temp(prefix,dir):
    return real_mkdtemp(prefix=prefix,dir=str(base))
run.acquisition.tempfile.mkdtemp=workspace_temp
main=run.acquisition.main
def retain_budget():
    run.acquisition.STATE["downloads"]=old["downloads"].copy()
    run.acquisition.STATE["steps"]=old["steps"].copy()
    run.acquisition.STATE["resumption"]=record
    main()
run.acquisition.main=retain_budget
freeze=json.loads((HERE/"freeze.json").read_text())
freeze["files"]["resume_gate1.py"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
freeze["resumption_note"]="Only scratch-location and cumulative-budget wrapper added before model startup; original prompt/cases/settings/scorer and deadline unchanged."
run.write("freeze.json",freeze)
(HERE/"preparation.json").unlink()
run.event("build_interruption_recovery",**record)
run.prepare()
