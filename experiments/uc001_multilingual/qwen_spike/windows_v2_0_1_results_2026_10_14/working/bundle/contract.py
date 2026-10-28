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

