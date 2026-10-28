import json,os,time
from pathlib import Path
root=Path(__file__).resolve().parent
prep=json.loads((root/"preparation.json").read_text());scratch=Path(prep["temporary_root"])
seed=[];records=[]
for q in Path("/proc").iterdir():
 if not q.name.isdigit():continue
 try:
  stat=(q/"stat").read_text().rsplit(")",1)[1].split();exe=os.readlink(q/"exe")
 except (PermissionError,FileNotFoundError,ProcessLookupError):continue
 if exe.startswith(str(scratch)+"/"):seed.append(int(stat[2]))
 records.append((q,stat,exe))
owned=[]
for q,stat,exe in records:
 if int(stat[2]) not in seed:continue
 try:rss=next((int(l.split()[1])*1024 for l in (q/"status").read_text().splitlines() if l.startswith("VmRSS:")),0)
 except (PermissionError,FileNotFoundError,ProcessLookupError):continue
 owned.append({"pid":int(q.name),"process_group":int(stat[2]),"exe":exe,"rss_bytes":rss})
available=next(int(l.split()[1])*1024 for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemAvailable:"))
log=scratch/"build.log"
row={"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"owned_build_processes":owned,"owned_rss_bytes":sum(r["rss_bytes"] for r in owned),"available_memory_bytes":available,"temporary_bytes":sum(p.stat().st_size for p in scratch.rglob("*") if p.is_file()),"build_log_tail":log.read_text(errors="replace").splitlines()[-3:] if log.exists() else []}
with (root/"resource_samples.jsonl").open("a") as f:f.write(json.dumps(row)+"\n")
print(json.dumps(row))
