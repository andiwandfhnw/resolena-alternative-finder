"""Prepare immutable synthetic files; no network, process launch or held-out reads."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPIKE = HERE.parent
source = (SPIKE / "evaluate_model.py").read_bytes()
assert hashlib.sha256(source).hexdigest() == "47503a8ccd7aeed8c1bfd8b18ad4a9c8ff52b3fbbfd74d415034ba68e84f1121"
text = source.decode()
contract = text[text.index("SUPPORTED="):text.index("class LocalHTTP")]
assert all(isinstance(node, (ast.Assign, ast.FunctionDef)) for node in ast.parse(contract).body)
assert not (HERE / "cases.json").exists(), "Already prepared; never overwrite a freeze"
(HERE / "contract.py").write_text(contract)
namespace = {}
exec(compile(contract, "frozen-pure-contract", "exec"), namespace)

def write(name, value):
    path = HERE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

artifacts = {
    "metadata_checked_utc": "2026-10-11",
    "cap_bytes": 10000000000,
    "reserved_bundle_and_metadata_bytes": 1048576,
    "artifacts": [
        {"id": "runtime", "file": "llama-b11429-bin-win-vulkan-x64.zip",
         "version": "b11429", "source_commit": "d81235049384534c167caea52b85a694f6103d14",
         "bytes": 33337769,
         "sha256": "1bfe78ad9168b79fa02bf67f6af9f5e17a966d824d77238517f7bef12ac73b36",
         "url": "https://github.com/ggml-org/llama.cpp/releases/download/b11429/llama-b11429-bin-win-vulkan-x64.zip",
         "metadata_url": "https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/b11429"},
        {"id": "model", "file": "Qwen3-8B-Q8_0.gguf",
         "repo": "Qwen/Qwen3-8B-GGUF", "revision": "7c41481f57cb95916b40956ab2f0b139b296d974",
         "bytes": 8709518112,
         "sha256": "408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6",
         "url": "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/7c41481f57cb95916b40956ab2f0b139b296d974/Qwen3-8B-Q8_0.gguf",
         "metadata_url": "https://huggingface.co/api/models/Qwen/Qwen3-8B-GGUF/revision/7c41481f57cb95916b40956ab2f0b139b296d974?blobs=true"}
    ]}
assert sum(x["bytes"] for x in artifacts["artifacts"]) + artifacts["reserved_bundle_and_metadata_bytes"] < artifacts["cap_bytes"]
write("artifacts.json", artifacts)
config = {
    "version": "1.0.0", "classification": "AI-assisted synthetic exploratory calibration; not independently linguistically validated",
    "direction": "A; no production interpreter/host/DESIGN acceptance",
    "platform": "Owner Windows 11 Pro desktop; no direct Codespace access",
    "backend": "Vulkan only; no fallback", "inference_threads": 2, "prompt_threads": 2,
    "context": 2048, "output_tokens": 384, "batch": 64, "ubatch": 64, "kv_type": "f16", "slots": 1,
    "sampling": {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "seed": 42},
    "limits": {"total_seconds": 7200, "setup_seconds": 3600, "evaluation_seconds": 1800,
        "readiness_seconds": 90, "request_seconds": 45,
        "rss_bytes": 17179869184, "ram_preflight_bytes": 21474836480, "ram_floor_bytes": 4294967296,
        "gpu_preflight_free_bytes": 15032385536, "gpu_owned_bytes": 12884901888,
        "gpu_floor_bytes": 2147483648, "scratch_bytes": 26843545600,
        "disk_preflight_free_bytes": 32212254720, "disk_floor_bytes": 5368709120},
    "latency_targets": {"warm_median_seconds": 10, "warm_p95_seconds": 20, "maximum_seconds": 45,
        "status": "candidate evaluation targets, not product requirement amendments"},
    "known_gate": "All six must pass unchanged strict checks and explicit semantic/status checks; any failure blocks new cases. Label-only mismatch remains a strict failure.",
    "heldout": "55 original held-out cases excluded; no fixture reads/transfers/model exposure",
    "transport_change": "Windows loopback HTTP instead of Linux AF_UNIX; payload/contract unchanged",
    "server_port": 49187, "host": "127.0.0.1", "resource_sample_seconds": 1,
    "owner_hardware": {"cpu": "Ryzen 9 5950X", "ram_gb": 64, "gpu": "Radeon RX 6800 XT",
        "dxdiag_vram_mb": 16337, "driver": "32.0.21045.5002", "driver_date": "2026-08-17", "wddm": "3.2"}}
write("config.json", config)
known = json.loads((SPIKE / "portable_2026_10_11/cases.json").read_text())["cases"]
new = []
def understood(cid, text, language, subject, action, constraints=None, protected=None):
    case = {"id": cid, "text": text, "expected": {"status": "understood", "language": language,
        "subject": subject, "action": action, "goals": [], "constraints": constraints or {}}}
    if protected:
        case["protected_literals"] = protected
    new.append(case)
understood("DE01", "Ich möchte mein Velo instand setzen lassen.", "de", "bicycle", "repair")
understood("DE02", "Vergleiche Alternativen zu meiner Kaffeemaschine.", "de", "coffee_machine", "compare")
understood("DE03", "Repariere mein Smartphone; ich will keinen Ersatz.", "de", "smartphone", "repair", {"no_replacement": "true"})
understood("DE04", "Repariere das Velo Acme Z7 für höchstens 49.90 CHF.", "de", "bicycle", "repair", {"identifier": "Acme Z7", "budget": "49.90 CHF"}, ["Acme Z7", "49.90 CHF"])
understood("FR01", "Je voudrais faire remettre mon vélo en état.", "fr", "bicycle", "repair")
understood("FR02", "Compare les alternatives à mon aspirateur.", "fr", "vacuum", "compare")
understood("FR03", "Répare mon téléphone sans en acheter un neuf.", "fr", "smartphone", "repair", {"no_new_purchase": "true"})
understood("FR04", "Répare le vélo Acme Z7 pour au maximum 49.90 CHF.", "fr", "bicycle", "repair", {"identifier": "Acme Z7", "budget": "49.90 CHF"}, ["Acme Z7", "49.90 CHF"])
understood("IT01", "Vorrei far sistemare la mia bicicletta.", "it", "bicycle", "repair")
understood("IT02", "Confronta le alternative alla mia macchina da caffè.", "it", "coffee_machine", "compare")
understood("IT03", "Ripara il mio aspirapolvere senza sostituirlo.", "it", "vacuum", "repair", {"no_replacement": "true"})
understood("IT04", "Ripara la bicicletta Acme Z7 spendendo al massimo 49.90 CHF.", "it", "bicycle", "repair", {"identifier": "Acme Z7", "budget": "49.90 CHF"}, ["Acme Z7", "49.90 CHF"])
understood("EN01", "Please mend my bicycle.", "en", "bicycle", "repair")
understood("EN02", "Compare alternatives to my vacuum cleaner.", "en", "vacuum", "compare")
understood("EN03", "Repair my smartphone; do not replace it.", "en", "smartphone", "repair", {"no_replacement": "true"})
understood("EN04", "Repair the Acme Z7 bicycle for no more than 49.90 CHF.", "en", "bicycle", "repair", {"identifier": "Acme Z7", "budget": "49.90 CHF"}, ["Acme Z7", "49.90 CHF"])
understood("MIX01", "Repair my bicycle, sans acheter du neuf.", "en", "bicycle", "repair", {"no_new_purchase": "true"})
understood("MIX02", "Répare mon vélo, without replacing it.", "fr", "bicycle", "repair", {"no_replacement": "true"})
understood("SHORT01", "Velo — Acme Z7", None, "bicycle", None, {"identifier": "Acme Z7"}, ["Acme Z7"])
understood("SHORT02", "Streaming — Acme Z7", None, "streaming", None, {"identifier": "Acme Z7"}, ["Acme Z7"])
new.extend([
    {"id": "AMB01", "text": "Repair my kettle for 1,200 CHF.", "expected": {
        "status": "clarification", "language": "en", "unresolved_nonempty": True,
        "uncertainty_terms": ["1,200", "ambig", "numeric", "number", "amount"],
        "allowed_subjects": [None, "kettle"], "allowed_actions": [None, "repair"]}},
    {"id": "AMB02", "text": "Je veux quelque chose de mieux.", "expected": {
        "status": "clarification", "language": "fr", "unresolved_nonempty": True,
        "uncertainty_terms": ["subject", "objet", "meaning", "ambig", "unclear", "request"],
        "allowed_subjects": [None], "allowed_actions": [None]}},
    {"id": "OUT01", "text": "Necesito reparar mi bicicleta.", "expected": {
        "status": "unsupported", "language": None, "unresolved_nonempty": True,
        "allowed_subjects": [None, "bicycle"], "allowed_actions": [None, "repair"]}},
    {"id": "OUT02", "text": "Mis Velo sött gflickt werde.", "expected": {
        "status": "unsupported", "language": None, "unresolved_nonempty": True,
        "allowed_subjects": [None, "bicycle"], "allowed_actions": [None, "repair"]}}
])
assert len(new) == 24
write("cases.json", {"classification": config["classification"], "known_cases": known,
    "new_cases": new, "repeats": ["DE01", "FR01", "IT01", "EN01"],
    "oracle_note": "AI-assisted expectations, no independent human review; uncertainty wording terms are an exploratory automated proxy, not linguistic acceptance."})
plan = []
for stage, cases in [("known", known), ("new", new), ("repeat", [next(x for x in new if x["id"] == i) for i in ["DE01", "FR01", "IT01", "EN01"]])]:
    for case in cases:
        rid = f'{len(plan)+1:02d}-{case["id"]}-{stage}'
        body = {"messages": [{"role": "system", "content": namespace["PROMPT"]},
                             {"role": "user", "content": case["text"]}],
            **config["sampling"], "max_tokens": config["output_tokens"], "cache_prompt": False,
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object", "schema": namespace["SCHEMA"]}}
        write("requests/" + rid + ".json", body)
        plan.append({"id": rid, "case": case["id"], "stage": stage, "request": "requests/" + rid + ".json"})
write("order.json", plan)
write("contract_provenance.json", {"source": "../evaluate_model.py",
    "source_sha256": hashlib.sha256(source).hexdigest(),
    "extraction": "Byte-identical SUPPORTED/ALIASES/canonical/validate/semantic_score/ITEM/CONSTRAINT/SCHEMA/PROMPT block; no original module import",
    "contract_sha256": hashlib.sha256(contract.encode()).hexdigest()})
print(json.dumps({"prepared_requests": len(plan), "new_cases": len(new),
    "artifact_bytes": sum(x["bytes"] for x in artifacts["artifacts"]), "heldout_reads": 0}))
