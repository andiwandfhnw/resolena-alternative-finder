"""Package the separate harness repair; no model or Windows execution."""
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE / "execution"
PARENT = HERE.parent / "windows_qwen3_8b_followup_v2/execution"
REPO = HERE.parents[3]
ZIP = REPO / "build/checkpoints/windows-qwen3-8b-v2-0-1.zip"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def main():
    for path in [PAYLOAD / "freeze.json", ZIP, HERE / "bundle-handoff.json", HERE / "offline_checks.json", HERE / "BUNDLE.md"]:
        if path.exists():
            raise ValueError("Existing frozen/package record preserved: " + str(path))
    parent_freeze = json.loads((PARENT / "freeze.json").read_bytes())
    changed = {"Common.ps1", "Watchdog.ps1", "README.md", "provenance.json"}
    for name, expected in parent_freeze["files"].items():
        assert sha((PARENT / name).read_bytes()) == expected, name
        if name not in changed:
            assert (PAYLOAD / name).read_bytes() == (PARENT / name).read_bytes(), name
    assert not (PAYLOAD / "execution-approval.json").exists()
    assert not (PAYLOAD / "run_attempt.json").exists()
    checks = []
    for script, count, scope in [("test_execution.py", 14, "Synthetic orchestration"), ("test_harness_patch.py", 5, "Evidence/source checks, not PowerShell runtime validation")]:
        result = subprocess.run([sys.executable, "-B", str(HERE / script)], capture_output=True, text=True)
        checks.append({"script": script, "sha256": sha((HERE / script).read_bytes()), "count": count,
            "scope": scope, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise ValueError("Offline checks failed; no freeze/export")
    report = {"utc": datetime.now(timezone.utc).isoformat(), "checks": checks, "available_checks_passed": 19,
        "PowerShell_available_in_Codespace": False, "Windows_5_1_regressions_executed": False,
        "Windows_5_1_compatibility_established": False, "Windows_regression_entry_point": "Test-Harness.ps1",
        "red_checks_before_patch": "Two source checks failed on the unpatched copy; original Groups reproduction remains a Windows check",
        "inference_requests": 0, "downloads_installs": 0, "heldout_contents_read": False,
        "DESIGN": "pending", "linguistic_validation": "pending"}
    (HERE / "offline_checks.json").write_bytes(encoded(report))
    files = {str(p.relative_to(PAYLOAD)): sha(p.read_bytes()) for p in sorted(PAYLOAD.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    freeze = {"version": "2.0.1", "evaluation_and_receipt_protocol_version": "2.0.0",
        "prepared_utc": datetime.now(timezone.utc).isoformat(), "authorization": "Harness repair and offline checks only; no inference approval",
        "parent_bundle_freeze_sha256": sha((PARENT / "freeze.json").read_bytes()),
        "original_attempt_archive_sha256": "404b1620056c8cdc023d36d3d164ffcbc9bf5b3caf9d2ddecf2de9335b805d2c",
        "unchanged_maximum_requests": 18, "unchanged_total_seconds_including_pauses": 1800, "files": files}
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
        assert all(archive.read(n) == (PAYLOAD / n).read_bytes() for n in archive.namelist())
    handoff = {"harness_version": "2.0.1", "evaluation_and_receipt_protocol_version": "2.0.0",
        "zip": str(ZIP.relative_to(REPO)), "bytes": ZIP.stat().st_size, "sha256": sha(ZIP.read_bytes()),
        "freeze_sha256": sha((PAYLOAD / "freeze.json").read_bytes()), "payload_files": len(files),
        "generation_authorized": False, "evaluation_payloads_and_limits_unchanged": True,
        "changed_parent_payloads": sorted(changed), "new_payloads": sorted(set(files) - set(parent_freeze["files"])),
        "Linux_available_checks_passed": 19, "Windows_5_1_checks_pending": True,
        "model_runtime_artifacts_included": False}
    (HERE / "bundle-handoff.json").write_bytes(encoded(handoff))
    rows = "\n".join("| " + name + " | `" + digest + "` |" for name, digest in sorted(files.items()))
    (HERE / "BUNDLE.md").write_text(f"""# Harness 2.0.1 — offline-only repair, 2026-10-14

[Corrected ZIP](../../../../build/checkpoints/windows-qwen3-8b-v2-0-1.zip), {handoff['bytes']:,} bytes.
SHA-256: `{handoff['sha256']}`.
Freeze SHA-256: `{handoff['freeze_sha256']}`.
[Metadata](bundle-handoff.json), [offline checks](offline_checks.json),
[Windows instructions](execution/README.md), [final verification](verification.json).

The [original attempt](../windows_v2_results_2026_10_14/REVIEW.md) is closed as an
operational failure with zero evaluation requests. Its archive/approval/freeze/
markers/deadline and the original v2 bundle remain unchanged. Logged 37/37 GPU layer
offload is preserved; acceleration and language capability were not measured.
The 55 held-out cases were not read. No inference, acquisition or production change.

Focused changes: `$layerMatches` replaces the collection that collided with automatic
`$Matches`; the watchdog checks/rechecks process exit around metadata reads and still
rejects live PID/start-time/executable/uninspectable identity. Resource failures stay
outside that exit-race catch; thresholds and matching-process stop protection are
unchanged. Future watchdog records include expected/observed identity and exit state.
Only Common/Watchdog and new regression fixtures change executable behaviour;
README/provenance identify the new version. Run, dispatcher, prompts, requests,
cases, expectations, schema, scoring, sampling/runtime settings and resource limits
are byte-identical parent copies. Receipt/evaluation protocol remains 2.0.0.

19 Linux-available checks passed (14 synthetic orchestration, five evidence/source
checks). They do not establish PowerShell behaviour or Windows compatibility.
Packaged Windows checks reproduce the original Groups error on the preserved log,
test the correction/missing/partial evidence, test mocked shutdown races and genuine
live mismatches, then run the existing receipt/timer/export checks. PowerShell and
a .NET compiler are unavailable in the Codespace; Windows results remain pending.

After comparing the ZIP hash, unblock only this verified ZIP if needed and extract
to a **new** `C:\\ResolenaExperiments\\qwen3-8b-followup-v2-0-1` folder. Preserve both
older folders; copy no old approval or markers. **Windows PowerShell 5.1 only:**

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File C:\\ResolenaExperiments\\qwen3-8b-followup-v2-0-1\\Test-Harness.ps1 -Scratch C:\\ResolenaExperiments\\qwen3-8b-v2-0-1-offline-checks
```

Scratch must not exist. Stop on any failure; preserve/return the output and scratch
records. No Python or installation is required, and no model/real process is started
or terminated. Do not run Run.ps1: no inference approval is supplied. Tests passing
authorize no retry or new deadline. DESIGN/in-progress and linguistic validation pending.

## Frozen payload hashes

| File relative to execution/ | SHA-256 |
|---|---|
{rows}
""", encoding="utf-8")
    print(json.dumps(handoff, indent=2))


if __name__ == "__main__":
    main()
