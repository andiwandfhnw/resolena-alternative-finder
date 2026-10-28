"""Freeze and package the reviewed experiment; offline preparation only."""
import ast
import base64
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE / "execution"
REPO = HERE.parents[3]
ZIP = REPO / "build/checkpoints/windows-qwen3-8b-v2.zip"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    for path in [PAYLOAD / "freeze.json", ZIP, HERE / "bundle-handoff.json", HERE / "BUNDLE.md", HERE / "offline_checks.json"]:
        if path.exists():
            raise ValueError("Published freeze/export preserved: " + str(path))
    plan = json.loads((HERE / "draft-plan.json").read_bytes())
    cases = json.loads((PAYLOAD / "cases.json").read_bytes())
    assert cases == plan["known_cases"] + plan["fresh_cases"]
    order = json.loads((PAYLOAD / "order.json").read_bytes())
    assert len(order) == 18 and len({e["id"] for e in order}) == 18
    assert [(e["case"], e["arm"]) for e in order] == [(e["case"], e["arm"]) for e in plan["order"]]
    assert (PAYLOAD / "prompts/v2.txt").read_bytes() == (HERE / "prompt-v2.txt").read_bytes()
    v1 = HERE.parent / "windows_qwen3_8b_v1"
    for destination, original in [("contract.py", "contract.py"), ("assess.py", "assess.py"), ("Base.ps1", "Common.ps1"), ("Native.cs", "Native.cs"), ("artifacts.json", "artifacts.json")]:
        assert (PAYLOAD / destination).read_bytes() == (v1 / original).read_bytes()
    expected_cases = {c["id"]: c for c in cases}
    baseline = json.loads((v1 / "requests/01-C1-known.json").read_bytes())
    request_settings = {k: v for k, v in baseline.items() if k != "messages"}
    for entry in order:
        request = json.loads((PAYLOAD / entry["request"]).read_bytes())
        assert {k: v for k, v in request.items() if k != "messages"} == request_settings
        assert request["messages"] == [{"role": "system", "content": (PAYLOAD / ("prompts/" + entry["arm"] + ".txt")).read_text()},
            {"role": "user", "content": expected_cases[entry["case"]]["text"]}]
    provenance_path = PAYLOAD / "provenance.json"
    provenance = json.loads(provenance_path.read_bytes())
    source = REPO / "experiments/uc001_multilingual/qwen_spike/renewed_2026_10_11/build/resolena-qwen-spike-yzcp8uxx/llama.cpp-d81235049384534c167caea52b85a694f6103d14"
    for name in ["src/llama.cpp", "src/llama-kv-cache.cpp"]:
        provenance["source_logging"]["inspected_local_source_hashes"][name] = sha((source / name).read_bytes())
    provenance_path.write_bytes(encoded(provenance))

    spec = importlib.util.spec_from_file_location("offline_protocol_tests", HERE / "test_execution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture = module.ProtocolTests()
    fixture.setUp()
    fixture.freeze = encoded({"version": "synthetic-only-not-an-execution-freeze", "files": {}})
    fixture.bundle = module.dispatch.Bundle(PAYLOAD, fixture.freeze)
    scenarios = []
    for name, count, mutation in [("known-pass", 6, None), ("v1-content-permitted", 8, "v1"), ("v2-failure", 8, "v2"), ("stale", 6, None), ("expired", 6, None)]:
        def change(entry, record, raw):
            if mutation and entry["arm"] == mutation and entry["stage"] == "fresh":
                value = json.loads(raw["choices"][0]["message"]["content"])
                value["constraints"] = []
                raw["choices"][0]["message"]["content"] = json.dumps(value)
                record["raw_body"] = json.dumps(raw)
        files = fixture.packet(count, change)
        assessment, receipt = fixture.assess(files)
        files["assessment.json"], files["receipt.json"] = encoded(assessment), encoded(receipt)
        scenarios.append({"name": name, "expected_allowed": name in ["known-pass", "v1-content-permitted"],
            "files": {n: base64.b64encode(data).decode() for n, data in files.items()}})
    (PAYLOAD / "selftest-fixtures.json").write_bytes(encoded({"classification": "Synthetic harness fixtures, never model results", "scenarios": scenarios}))

    start = time.perf_counter()
    result = subprocess.run([sys.executable, "-B", str(HERE / "test_execution.py")], capture_output=True, text=True)
    report = {"utc": datetime.now(timezone.utc).isoformat(), "classification": "Offline synthetic harness checks only",
        "exit_code": result.returncode, "elapsed_seconds": time.perf_counter() - start,
        "test_names": [n.name for n in ast.walk(ast.parse((HERE / "test_execution.py").read_text())) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")],
        "stdout": result.stdout, "stderr": result.stderr, "Windows_PowerShell_executed": False,
        "actual_token_capacity_measured": False, "inference_requests": 0, "heldout_contents_read": False,
        "test_source_sha256": sha((HERE / "test_execution.py").read_bytes())}
    (HERE / "offline_checks.json").write_bytes(encoded(report))
    if result.returncode:
        raise ValueError("Offline checks failed; no freeze or ZIP created")
    files = {str(p.relative_to(PAYLOAD)): sha(p.read_bytes()) for p in sorted(PAYLOAD.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts}
    freeze = {"version": "2.0.0", "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "Bundle preparation and offline checks only; separate Windows inference approval required",
        "maximum_generation_requests": 18, "total_seconds_including_assessment_pauses": 1800,
        "parent_freeze_sha256": provenance["parent_freeze_sha256"], "files": files}
    (PAYLOAD / "freeze.json").write_bytes(encoded(freeze))
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, "x", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(list(files) + ["freeze.json"]):
            info = zipfile.ZipInfo(name, (2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (PAYLOAD / name).read_bytes())
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            assert archive.read(name) == (PAYLOAD / name).read_bytes()
    handoff = {"version": "2.0.0", "zip": str(ZIP.relative_to(REPO)), "bytes": ZIP.stat().st_size,
        "sha256": sha(ZIP.read_bytes()), "freeze_sha256": sha((PAYLOAD / "freeze.json").read_bytes()),
        "payload_files": len(files), "request_count": 18, "case_count": 12, "checkpoint_indices": [6, 8, 9, 12, 13, 16, 17, 18],
        "generation_authorized": False, "model_artifacts_included": False, "offline_test_count": len(report["test_names"]),
        "parent_upload_sha256": provenance["parent_results_zip_sha256"],
        "reviewed_draft_hashes": {n: sha((HERE / n).read_bytes()) for n in ["PROPOSAL.md", "prompt-v2.txt", "prompt-v2.diff", "draft-plan.json"]}}
    (HERE / "bundle-handoff.json").write_bytes(encoded(handoff))
    rows = "\n".join("| " + name + " | `" + digest + "` |" for name, digest in sorted(files.items()))
    (HERE / "BUNDLE.md").write_text(f"""# v2 bundle prepared — 2026-10-14

**Preparation/offline checks only; Windows inference requires separate approval.**
Version 2.0.0: [ZIP](../../../../build/checkpoints/windows-qwen3-8b-v2.zip), {handoff['bytes']:,} bytes.
ZIP SHA-256: `{handoff['sha256']}`.
Freeze SHA-256: `{handoff['freeze_sha256']}`.

[Windows instructions, exact order and expectations](execution/README.md),
[both prompts](execution/prompts/), [complete requests](execution/requests/),
[configuration](execution/config.json), [freeze](execution/freeze.json),
[handoff metadata](bundle-handoff.json) and [offline verification](offline_checks.json).

Operational changes only: a separate arm/request/freeze dispatcher uses byte-identical
v1 contract/assessor copies; eight manual hash-bound assessment gates; immutable
30-minute deadline including pauses; verbosity 4 for both arms; required layer/device/
KV evidence and all-prompt capacity probes before generation; byte-preserving export
after confirmed owned server/watchdog exit and cleanup. The unchanged strict gate
stops v2 failures; v1 content failures remain comparator data, not passes.
No model, sampling, schema, scoring, resource-limit or production changes.

{handoff['offline_test_count']} synthetic checks passed, including CLI/safe-ZIP transfer,
wrong arm/request/freeze, stale receipts, v1 failure permission, v2 failure stopping,
expiry, capacity boundaries, missing offload evidence, exact quotes and final-export
checks. They establish harness behaviour, not model correctness. Windows PowerShell
parser/receipt/timer/export checks are packaged but unexecuted here. Actual desktop
resource/artifact compatibility, rendered token counts and offload remain unmeasured;
the future runner stops before generation on any failed prerequisite.

V1 failed gate/results and original uploads remain unchanged; preservation checks
are [recorded separately](preparation_preservation.json). The 55 held-out cases were
not read or transferred; no inference/download/install occurred. Reviewed proposal,
prompt/diff/plan are preserved. DESIGN/in-progress and linguistic validation pending.
No execution approval receipt is supplied. First Windows step: download and compare
the ZIP hash using the README command; stop there and report the hash before extraction.

## Frozen payload hashes

| File relative to execution/ | SHA-256 |
|---|---|
{rows}
""", encoding="utf-8")
    print(json.dumps(handoff, indent=2))


if __name__ == "__main__":
    main()
