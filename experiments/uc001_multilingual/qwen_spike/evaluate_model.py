"""Synthetic local-model experiment; no production imports or qualification."""
import collections, datetime, hashlib, http.client, importlib.util, json, os, re, signal, socket, subprocess, threading, time
from pathlib import Path
from prepare import available, tree_rss, budget, DEADLINE

HERE=Path(__file__).resolve().parent
CONFIG=json.loads((HERE/"config.json").read_text())
SUPPORTED={"de","fr","it","en"}
ALIASES={
 "coffee machine":"coffee_machine","coffee maker":"coffee_machine","espresso machine":"coffee_machine","cafetière":"coffee_machine",
 "bicycle":"bicycle","bike":"bicycle","cycle":"bicycle","vélo":"bicycle","velo":"bicycle","fahrrad":"bicycle","bicicletta":"bicycle",
 "streaming":"streaming","streaming service":"streaming","streaming subscription":"streaming",
 "phone":"smartphone","smartphone":"smartphone","smartphones":"smartphone","mobile phone":"smartphone","téléphone":"smartphone",
 "vacuum":"vacuum","vacuum cleaner":"vacuum","aspirateur":"vacuum","aspirapolvere":"vacuum",
 "cup":"cup","reusable cup":"cup","tasse":"cup","becher":"cup","tazza":"cup",
 "reduce":"reduce_cost","spend less":"reduce_cost","save money":"reduce_cost","find":"compare","fix":"repair",
 "kettle":"kettle"}
def canonical(value):
    if value is None:return None
    value=str(value).strip().casefold().replace("_"," ")
    return ALIASES.get(value,value.replace(" ","_"))

def validate(obj,text):
    errors=[]
    if not isinstance(obj,dict):return ["not_object"]
    needed={"status","language","subject","action","goals","constraints","unresolved"}
    if set(obj)!=needed:errors.append("keys")
    if obj.get("status") not in {"understood","clarification","unsupported"}:errors.append("status")
    if obj.get("language") not in {*SUPPORTED,"mixed",None}:errors.append("language")
    for item in [obj.get("subject"),obj.get("action"),*obj.get("goals",[]),*obj.get("constraints",[])]:
        if not isinstance(item,dict):errors.append("field_object");continue
        quote=item.get("quote","")
        if item.get("value") is None and quote=="":continue
        if not isinstance(quote,str) or not quote or quote not in text:errors.append("ungrounded_quote");continue
        if "start" in item or "end" in item:
            start=item.get("start");end=item.get("end")
            if not isinstance(start,int) or not isinstance(end,int) or text[start:end]!=quote:errors.append("offset")
        else:
            if text.count(quote)>1:errors.append("ambiguous_quote_occurrence")
            else:item["resolved_span"]={"start":text.index(quote),"end":text.index(quote)+len(quote)}
    if obj.get("status")=="understood" and obj.get("unresolved"):errors.append("unresolved_understood")
    return errors

def semantic_score(obj,expected):
    status=obj.get("status")
    if status=="clarification":return {"category":"abstention","differences":{}}
    if status=="unsupported":return {"category":"unsupported","differences":{}}
    if status!="understood":return {"category":"invalid_output","differences":{"status":status}}
    if expected.get("status") in {"clarification","unsupported"}:
        return {"category":"incorrect","differences":{"expected_status":expected["status"],"actual_status":status}}
    actual={"subject":canonical(obj.get("subject",{}).get("value")),
            "action":canonical(obj.get("action",{}).get("value")),
            "goals":sorted(g.get("value") for g in obj.get("goals",[])),
            "constraints":{c["kind"]:c["value"] for c in obj.get("constraints",[])}}
    want={"subject":canonical(expected.get("subject")),"action":canonical(expected.get("action")),
          "goals":sorted(expected.get("goals",[])),"constraints":expected.get("constraints",{})}
    diff={k:{"expected":v,"actual":actual[k]} for k,v in want.items() if actual[k]!=v}
    return {"category":"incorrect" if diff else "correct","differences":diff,"projected":actual}

ITEM={"type":"object","properties":{"value":{"type":["string","null"]},"quote":{"type":"string"}},"required":["value","quote"],"additionalProperties":False}
CONSTRAINT={"type":"object","properties":{"kind":{"type":"string"},"value":{"type":"string"},"quote":{"type":"string"}},"required":["kind","value","quote"],"additionalProperties":False}
SCHEMA={"type":"object","properties":{"status":{"enum":["understood","clarification","unsupported"]},"language":{"enum":["de","fr","it","en","mixed",None]},
"subject":ITEM,"action":ITEM,"goals":{"type":"array","items":ITEM},"constraints":{"type":"array","items":CONSTRAINT},"unresolved":{"type":"array","items":{"type":"string"}}},
"required":["status","language","subject","action","goals","constraints","unresolved"],"additionalProperties":False}
PROMPT="""Interpret only the supplied request. Return the prescribed JSON, no explanation.
Supported written languages: German, French, Italian, English. Spanish and Swiss-German dialect input: unsupported. Mixed supported-language text may be understood; ambiguous meaning requires clarification.
Preserve all explicit goals, negation, exclusions, limits, names and amounts. Never infer cheaper/greener goals, a baseline, country or absent constraints.
subject.value: canonical English subject, e.g. bicycle, coffee_machine, streaming, smartphone, vacuum, cup, kettle.
action.value: repair, replace, reduce_cost, compare, reuse; null if not stated.
Every subject/action/goal/constraint quote must be an exact contiguous substring of the original input, using original spelling. Do not output character offsets.
goals: cheaper or reduce_waste only if explicitly stated, otherwise [].
constraints kinds: no_replacement, no_repair, replacement_required, preserve_quality, no_new_purchase (values true or false as strings); budget (canonical decimal currency, append /month only when explicit); storage_min (e.g. 128 GB); cost_exclusion (delivery); locality; identifier. Preserve other explicit constraints with clear English kinds/values.
1,200 CHF is numerically ambiguous: clarification, not a guessed amount.
For understood: unresolved []; subject/action null use empty quote. For clarification or unsupported preserve uncertainty in unresolved. A quoted negative clause must control the meaning, never silently reverse or drop it. Recognition of words is not understanding.
"""

class LocalHTTP(http.client.HTTPConnection):
    def __init__(self,path,timeout):super().__init__("localhost",timeout=timeout);self.path=path
    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);self.sock.settimeout(self.timeout);self.sock.connect(self.path)

def call(path,text,seed=42,timeout=45):
    conn=LocalHTTP(path,timeout)
    params={k:CONFIG["inference"][k] for k in ["temperature","top_p","top_k","min_p","max_tokens"]}
    body={"messages":[{"role":"system","content":PROMPT},{"role":"user","content":text}],
          **params,"seed":seed,"cache_prompt":False,"chat_template_kwargs":{"enable_thinking":False},
          "response_format":{"type":"json_object","schema":SCHEMA}}
    started=time.monotonic()
    try:
        conn.request("POST","/v1/chat/completions",json.dumps(body),{"Content-Type":"application/json"})
        response=conn.getresponse();raw=response.read().decode()
        if response.status!=200:raise RuntimeError("HTTP "+str(response.status)+": "+raw[:500])
        wire=json.loads(raw);content=wire["choices"][0]["message"]["content"]
        return {"wall_seconds":time.monotonic()-started,"wire_finish_reason":wire["choices"][0].get("finish_reason"),
                "content":content,"timings":wire.get("timings"),"usage":wire.get("usage"),"object":parse_content(content)}
    finally:conn.close()

def parse_content(content):
    try:return json.loads(content)
    except json.JSONDecodeError:return None

def old_cases():
    source=json.loads((HERE.parent/"heldout.json").read_text())
    result=[]
    for row in source["requests"]:
        ex=row["expected"]
        if ex.get("must_clarify"):expected={"status":"clarification"}
        elif ex.get("unsupported"):expected={"status":"unsupported"}
        else:
            constraints={}
            if ex.get("no_replacement"):constraints["no_replacement"]="true"
            if ex.get("budget"):constraints["budget"]=ex["budget"]["amount"]+" "+ex["budget"]["currency"]
            if row["id"] in {"FR-3","IT-3","EN-3"}:constraints["no_repair"]="true"
            if row["id"]=="DE-4":constraints["replacement_required"]="true"
            if row["id"]=="NAME":constraints.update(identifier="Acme X-2",locality="Genève")
            expected={"status":"understood","subject":ex.get("subject"),"action":ex.get("action"),"goals":["cheaper"] if ex.get("goal")=="cheaper" else [],"constraints":constraints}
        result.append({**row,"id":"OLD-"+row["id"],"expected":expected,"set":"old_reused"})
    return result

def parser_compare(cases):
    spec=importlib.util.spec_from_file_location("frozen_parser",HERE.parent/"prototype.py");mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=[]
    for row in cases:
        start=time.monotonic();raw=mod.interpret(row["text"],**row.get("context",{}));elapsed=time.monotonic()-start
        if raw["status"]=="handled":
            cs={}
            if raw.get("no_replacement"):cs["no_replacement"]="true"
            if raw.get("budget"):cs["budget"]=raw["budget"]["amount"]+" "+raw["budget"]["currency"]
            pseudo={"status":"understood","subject":{"value":raw["subject"]},"action":{"value":raw["action"]},"goals":[{"value":raw["goal"]}] if raw["goal"] else [],"constraints":[{"kind":k,"value":v} for k,v in cs.items()]}
            score=semantic_score(pseudo,row["expected"])
        else:score={"category":"abstention" if raw["status"]=="clarification" else raw["status"],"differences":{}}
        result.append({"id":row["id"],"language":row["language"],"raw":raw,"score":score,"wall_seconds":elapsed})
    return result

def summary(rows):
    out={"counts":dict(collections.Counter(r["category"] for r in rows)),"per_language":{}}
    for lang in sorted({r["language"] for r in rows}):
        sub=[r for r in rows if r["language"]==lang];times=sorted(r["wall_seconds"] for r in sub if r.get("wall_seconds") is not None)
        out["per_language"][lang]={"counts":dict(collections.Counter(r["category"] for r in sub)),
         "latency_seconds":{"median":times[len(times)//2] if times else None,"p95":times[min(len(times)-1,int(.95*len(times)))] if times else None,"max":max(times) if times else None}}
    return out

def main():
    prep=json.loads((HERE/"preparation.json").read_text())
    if prep.get("status")!="prepared":raise RuntimeError("Preparation not successful")
    scratch=Path(prep["temporary_root"])
    frozen=json.loads((HERE/"freeze.json").read_text())
    for name,digest in frozen["files"].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=digest:raise RuntimeError("Frozen artifact changed: "+name)
    if hashlib.sha256((HERE.parent/"prototype.py").read_bytes()).hexdigest()!=CONFIG["frozen_parser_sha256"]:raise RuntimeError("Frozen parser changed")
    deadline=min(DEADLINE,json.loads((HERE/"inference_budget.json").read_text())["deadline_epoch"])
    path=str(scratch/"inference.sock");trace=scratch/"network.trace";log=scratch/"inference.log"
    args=["strace","-f","-e","trace=network","-o",str(trace),prep["server"],"-m",prep["model"],"--host",path,
          "--offline","--no-webui","--no-agent","--jinja","--parallel","1","-t","2","-tb","2","-c","2048","-b","64","-ub","64",
          "-ngl","0","--cache-type-k","f16","--cache-type-v","f16","--no-context-shift"]
    env={"PATH":"/usr/local/bin:/usr/bin:/bin","LANG":"C.UTF-8","LC_ALL":"C.UTF-8","LLAMA_CACHE":str(scratch/"cache"),"TMPDIR":str(scratch/"tmp")}
    metrics={"peak_owned_rss_bytes":0,"minimum_available_bytes":available(),"guard_error":None,"network_nonlocal":False,"instrumented":True}
    stop=threading.Event()
    if Path(path).exists():
        probe=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        try:
            probe.connect(path)
        except ConnectionRefusedError:
            Path(path).unlink()
        else:
            raise RuntimeError("Owned socket still has a live server; do not replace it")
        finally:probe.close()
    output=log.open("w");proc=subprocess.Popen(args,stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
    def terminate():
        if proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:pass
    def monitor():
        while not stop.wait(.2):
            metrics["peak_owned_rss_bytes"]=max(metrics["peak_owned_rss_bytes"],tree_rss(proc.pid))
            metrics["minimum_available_bytes"]=min(metrics["minimum_available_bytes"],available())
            if trace.exists() and re.search(r"sa_family=AF_INET(?:6)?",trace.read_text(errors="replace")):
                metrics["network_nonlocal"]=True;metrics["guard_error"]="unexpected_inet_activity";terminate();return
            if metrics["peak_owned_rss_bytes"]>CONFIG["rss_limit_bytes"] or available()<CONFIG["available_memory_min_bytes"]:
                metrics["guard_error"]="memory_guard";terminate();return
            if time.time()>deadline:metrics["guard_error"]="time_guard";terminate();return
    thread=threading.Thread(target=monitor,daemon=True);thread.start()
    records=[];start=time.monotonic()
    report={"configuration":CONFIG,"frozen":frozen,"calibration":[],"evaluations":records,"model_weights_changed":False,
            "tuning":[],"measurement_notes":"All server latency/RSS measurements use strace instrumentation. AI-authored semantic oracles; no independent linguistic validation."}
    try:
        while True:
            if proc.poll() is not None:raise RuntimeError("Server exited before readiness")
            if time.monotonic()-start>90:raise RuntimeError("Server startup timeout")
            if Path(path).exists():
                health=LocalHTTP(path,2)
                try:
                    health.request("GET","/health");response=health.getresponse();response.read()
                    if response.status==200:break
                except (OSError,http.client.HTTPException):pass
                finally:health.close()
            time.sleep(.2)
        report["cold_start_seconds"]=time.monotonic()-start
        for row in json.loads((HERE/"calibration.json").read_text())["cases"]:
            actual=call(path,row["text"]);errors=validate(actual["object"],row["text"])
            report["calibration"].append({**row,"actual":actual,"structural_errors":errors})
            print(json.dumps({"phase":"calibration","language":row["language"],"errors":errors,"seconds":actual["wall_seconds"]}),flush=True)
        cases=old_cases()+[{**r,"set":"new_heldout"} for r in json.loads((HERE/"heldout_v2.json").read_text())["cases"]]
        report["parser_on_new_cases"]=parser_compare(cases[23:])
        for row in cases:
            if metrics["guard_error"]:raise RuntimeError(metrics["guard_error"])
            item={"id":row["id"],"language":row["language"],"set":row["set"],"text":row["text"],"expected":row["expected"]}
            started=time.monotonic()
            try:
                actual=call(path,row["text"]);errors=validate(actual["object"],row["text"]);semantic=semantic_score(actual["object"],row["expected"]) if isinstance(actual["object"],dict) else {"category":"invalid_output","differences":{"malformed_json":True}}
                if isinstance(actual["object"],dict) and row["language"] in SUPPORTED and actual["object"].get("status")=="understood" and actual["object"].get("language")!=row["language"]:
                    semantic["differences"]["language"]={"expected":row["language"],"actual":actual["object"].get("language")};semantic["category"]="incorrect"
                if isinstance(actual["object"],dict) and row["language"]=="ambiguous" and actual["object"].get("status")=="understood" and actual["object"].get("language") is not None:
                    semantic["differences"]["language_ambiguity"]="shared word does not establish request language";semantic["category"]="incorrect"
                item.update(actual=actual,structural_errors=errors,semantic=semantic,category="invalid_output" if errors or actual["wire_finish_reason"]=="length" else semantic["category"],wall_seconds=actual["wall_seconds"])
            except (socket.timeout,TimeoutError):item.update(category="timeout",wall_seconds=time.monotonic()-started)
            except (json.JSONDecodeError,RuntimeError,KeyError,TypeError) as error:item.update(category="invalid_output",error=str(error),wall_seconds=time.monotonic()-started)
            records.append(item)
            print(json.dumps({"phase":row["set"],"id":row["id"],"category":item["category"],"seconds":round(item["wall_seconds"],2),"semantic":item.get("semantic",{}).get("differences")}),flush=True)
            (HERE/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        repeats=[]
        for rid in json.loads((HERE/"heldout_v2.json").read_text())["repeat_ids"]:
            row=next(r for r in cases if r["id"]==rid)
            for seed in [42,43]:
                if metrics["guard_error"]:raise RuntimeError(metrics["guard_error"])
                try:
                    actual=call(path,row["text"],seed=seed);errors=validate(actual["object"],row["text"]);semantic=semantic_score(actual["object"],row["expected"])
                    repeats.append({"id":rid,"seed":seed,"actual":actual,"structural_errors":errors,"semantic":semantic})
                except Exception as e:repeats.append({"id":rid,"seed":seed,"error":str(e)})
        report["repeats"]=repeats;report["status"]="completed"
    except Exception as e:report["status"]="stopped";report["error"]=str(e)
    finally:
        stop.set();thread.join(timeout=2);terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        output.close()
        report["metrics"]=metrics;report["elapsed_seconds"]=time.monotonic()-start
        report["old_summary"]=summary([r for r in records if r["set"]=="old_reused"])
        report["new_summary"]=summary([r for r in records if r["set"]=="new_heldout"])
        report["executed_case_count"]=len(records)
        if trace.exists():
            text=trace.read_text(errors="replace");(HERE/"network_observed.txt").write_text(text)
            report["network_observation"]={"trace_lines":len(text.splitlines()),"inet_activity":bool(re.search(r"sa_family=AF_INET(?:6)?",text)),"scope":"owned straced process tree only; not general telemetry proof"}
        (HERE/"inference_log_tail.txt").write_text("\n".join(log.read_text(errors="replace").splitlines()[-80:])+"\n")
        (HERE/"results.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps({"status":report["status"],"old":report["old_summary"],"new":report["new_summary"],"metrics":metrics,"error":report.get("error")}),flush=True)

if __name__=="__main__":main()
