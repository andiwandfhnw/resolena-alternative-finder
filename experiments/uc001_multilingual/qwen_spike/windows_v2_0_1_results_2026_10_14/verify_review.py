"""Offline evidence review and one labelled fixture supplementation; no receipts."""
import json
import math
import re
import statistics
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKING = HERE / "working/bundle"
sys.path.insert(0, str(WORKING))
import dispatch


def save(name, value):
    path = HERE / name
    if path.exists():
        raise ValueError("Existing review output preserved: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dispatch.encoded(value))


def main():
    original = HERE / "uploaded/final-results-original.zip"
    files = dispatch.read_archive(original)
    bundle = dispatch.Bundle(WORKING, (WORKING / "freeze.json").read_bytes())
    run, checkpoint, entries = dispatch.validate_checkpoint(bundle, files)
    assert run["run_id"] == "b8591094-a685-48f4-88ef-3420d8b68d90" and len(entries) == 6
    recorded_bytes = files["inbox/cp06/assessment.json"]
    receipt_bytes = files["inbox/cp06/receipt.json"]
    recorded, receipt = dispatch.obj(recorded_bytes), dispatch.obj(receipt_bytes)
    assert (HERE / "uploaded/cp06-assessed/assessment.json").read_bytes() == recorded_bytes
    assert (HERE / "uploaded/cp06-assessed/receipt.json").read_bytes() == receipt_bytes
    returned = dispatch.read_archive(HERE / "uploaded/cp06-assessed/return-cp06.zip")
    assert returned["assessment.json"] == recorded_bytes and returned["receipt.pending.json"] == receipt_bytes
    packet = dispatch.read_archive(HERE / "uploaded/cp06-original.zip")
    dispatch.validate_checkpoint(bundle, packet)
    assert packet["checkpoint.json"] == files["checkpoint.json"] == files["checkpoints/cp06/checkpoint.json"]
    for entry in entries:
        for name in [entry["request"], "responses/" + entry["id"] + ".json"]:
            assert packet[name] == files[name], name
    bindings = {"run_id": run["run_id"], "freeze_sha256": bundle.freeze_sha,
        "checkpoint_id": checkpoint["checkpoint_id"], "checkpoint_sha256": dispatch.sha(files["checkpoint.json"]),
        "nonce": checkpoint["nonce"], "deadline_utc": run["deadline_utc"], "next_index": 7,
        "assessment_sha256": dispatch.sha(recorded_bytes), "receipts": checkpoint["receipts"]}
    assert all(receipt[k] == v for k, v in bindings.items())
    assert receipt["allowed"] is False and recorded["allowed"] is False
    assert dispatch.instant(run["started_utc"]) <= dispatch.instant(receipt["created_utc"]) < dispatch.instant(run["deadline_utc"])
    assert not any("consumed.json" in n for n in files)
    evaluations = [dispatch.evaluate(bundle, entry, files) for entry in entries]
    assert evaluations == recorded["evaluations"]
    operational = dispatch.runtime_errors(bundle, files)
    assert operational == recorded["operational_errors"] == []
    assert sum(e["strict_pass"] for e in evaluations) == recorded["v2_strict_passes"] == 5
    assert all(not e["grounding_errors"] and not e["validation_errors"] and not e["label_mismatches"] for e in evaluations)
    german = evaluations[2]["actual"]["constraints"]
    assert len(german) == 1 and {k: german[0][k] for k in ["kind", "value", "quote"]} == {
        "kind": "no_replacement", "value": "true", "quote": "ohne ihn zu ersetzen"}
    assert evaluations[5]["semantic_errors"] == ["status", "language", "missing_uncertainty"]
    quotes = sum(bool(v.get("quote")) for e in evaluations for v in
        [e["actual"]["subject"], e["actual"]["action"]] + e["actual"]["goals"] + e["actual"]["constraints"])
    capacity = dispatch.obj(files["capacity.json"])
    for entry in bundle.order:
        assert dispatch.sha(files[entry["request"]]) == bundle.request_hash(entry)
        template = dispatch.obj(files["templates/" + entry["id"] + ".json"])
        tokens = dispatch.obj(files["templates/" + entry["id"] + ".tokens.json"])
        assert template["http_status"] == tokens["http_status"] == 200
        assert len(json.loads(tokens["raw_body"])["tokens"]) == capacity["requests"][entry["id"]]["tokens"]
        assert re.search(r"(?s)<\|im_start\|>assistant\s*<think>\s*</think>\s*$", json.loads(template["raw_body"])["prompt"])
    for e in evaluations:
        assert e["usage"]["prompt_tokens"] == capacity["requests"][e["id"]]["tokens"]
    samples = [json.loads(line) for line in files["resources.jsonl"].splitlines() if line.strip()]
    preflight = dispatch.obj(files["preflight.json"])
    preload = dispatch.obj(files["preload_resources.json"])
    for sample in [preflight["measured"], preload]:
        for field, bound in [("available_ram_bytes", "ram_preflight_bytes"), ("adapter_free_bytes", "gpu_preflight_free_bytes"), ("disk_free_bytes", "disk_preflight_free_bytes")]:
            assert sample[field] >= bundle.config["limits"][bound]
    log = files["server.stderr.log"].decode("utf-8")
    assert re.findall(r"offloaded (\d+)/(\d+) layers to GPU", log) == [("37", "37")]
    assert len(re.findall(r"launch_slot_.*processing task", log)) == 6
    readiness = dispatch.obj(files["readiness.json"])
    assert readiness["ready"] and readiness["seconds"] <= 90
    props = json.loads(dispatch.obj(files["server_properties.json"])["raw_body"])
    assert props["default_generation_settings"]["n_ctx"] == 2048 and props["total_slots"] == 1
    assert "guard_failure.json" not in files and "watchdog_forced_exit.json" not in files
    exits = {n: dispatch.obj(files[n]) for n in ["server_exit.json", "watchdog_exit.json", "watchdog_process_exit.json", "driver_exit.json"]}
    assert exits["server_exit.json"]["confirmed_exited"] and exits["watchdog_process_exit.json"]["confirmed_exited"]
    assert exits["watchdog_exit.json"]["status"] == "server_ended"
    assert exits["watchdog_exit.json"]["exit_code"] == exits["watchdog_process_exit.json"]["exit_code"] == 0
    assert exits["driver_exit.json"]["completed_requests"] == 6 and exits["driver_exit.json"]["exit_code"] == 1
    assert exits["driver_exit.json"]["elapsed_seconds"] <= 1800
    fixture_name = "fixtures/startup-v2-20261014.log"
    fixture = (WORKING / fixture_name).read_bytes()
    manifest = dispatch.obj(files["cleanup_manifest.json"])
    assert [n for n in manifest["files"] if n not in files] == [fixture_name]
    assert len(fixture) == manifest["files"][fixture_name]["bytes"] == 14212
    assert dispatch.sha(fixture) == manifest["files"][fixture_name]["sha256"] == bundle.freeze["files"][fixture_name]
    supplemented = HERE / "final-results-supplemented.zip"
    if supplemented.exists():
        raise ValueError("Existing supplemented archive preserved")
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(supplemented, "x") as target:
        target.comment = source.comment
        for info in source.infolist():
            target.writestr(info, source.read(info))
        info = zipfile.ZipInfo(fixture_name, (2026, 10, 14, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        target.writestr(info, fixture)
    supplement_files = dispatch.read_archive(supplemented)
    assert set(supplement_files) == set(files) | {fixture_name}
    assert all(supplement_files[n] == value for n, value in files.items())
    with zipfile.ZipFile(supplemented) as archive:
        assert archive.testzip() is None
    checks = {}
    for label, archive in [("original", original), ("supplemented", supplemented)]:
        output = HERE / "checks" / (label + "-closeout-output")
        command = [sys.executable, "-B", str(WORKING / "dispatch.py"), "closeout", str(archive), "--output", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        (HERE / "checks").mkdir(exist_ok=True)
        (HERE / "checks" / (label + ".stdout.log")).write_text(result.stdout)
        (HERE / "checks" / (label + ".stderr.log")).write_text(result.stderr)
        checks[label] = {"command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "archive_sha256": dispatch.sha(archive.read_bytes()), "output": str(output.relative_to(HERE))}
    assert checks["original"]["exit_code"] != 0 and ("Cleanup/export checksum mismatch: " + fixture_name) in checks["original"]["stderr"]
    assert checks["supplemented"]["exit_code"] == 0
    latencies = [e["wall_seconds"] for e in evaluations]
    ranges = {name: {"min": min(s[name] for s in samples), "max": max(s[name] for s in samples)} for name in
        ["available_ram_bytes", "adapter_free_bytes", "owned_gpu_bytes", "owned_rss_bytes", "owned_private_bytes", "disk_free_bytes", "scratch_bytes"]}
    save("supplementation.json", {"original_sha256": checks["original"]["archive_sha256"], "supplemented_sha256": checks["supplemented"]["archive_sha256"],
        "original_members": len(files), "supplemented_members": len(supplement_files), "original_member_bytes_names_and_manifest_unchanged": True,
        "fixture": {"name": fixture_name, "bytes": len(fixture), "sha256": dispatch.sha(fixture), "source": "Frozen harness 2.0.1 fixture, also byte-identical to the earlier failed operational run's startup log",
            "is_current_run_runtime_evidence": False}, "procedure": "Preserve ZIP member names, metadata and uncompressed bytes; recompress into a new labelled archive; add only the verified fixture; never rewrite the manifest",
        "verifier": checks, "original_failure_record": "Reproduced unchanged CLI failure preserved; prior CLI stderr was not included among uploads"})
    save("reassessment.json", {"classification": "Offline reassessment with unchanged copied scorer; no receipt generated",
        "run_id": run["run_id"], "strict_passes": 5, "matches_recorded_evaluations": True, "evaluations": evaluations})
    save("review.json", {"reviewed_utc": datetime.now(timezone.utc).isoformat(), "run_id": run["run_id"], "original_archive_sha256": checks["original"]["archive_sha256"],
        "supplemented_archive_sha256": checks["supplemented"]["archive_sha256"], "freeze_sha256": bundle.freeze_sha,
        "scorer_hashes": {n: dispatch.sha((WORKING / n).read_bytes()) for n in ["assess.py", "contract.py", "dispatch.py"]},
        "receipt_bindings_verified": True, "denied_receipt_sha256": dispatch.sha(receipt_bytes), "recorded_assessment_sha256": dispatch.sha(recorded_bytes),
        "requests_completed": 6, "requests_unrun": 12, "strict_passes": 5, "gate_allowed": False, "evaluations": evaluations,
        "grounding": {"requests_passed": 6, "populated_quotes": quotes}, "semantic_failures": {"06-C6-v2": evaluations[5]["semantic_errors"]},
        "canonical_label_mismatches": {}, "quote_grounding_failures": {}, "runtime": {"operational_errors": operational, "readiness": readiness,
            "resource_samples": len(samples), "recorded_ranges": ranges, "preflight": preflight, "preload": preload, "capacity": capacity,
            "template_tokenizer_probes_verified": 18, "largest_prompt": max(p["tokens"] for p in capacity["requests"].values()),
            "offload_evidence": dispatch.obj(files["offload_evidence.json"]), "reported_offloaded_layers": "37/37", "acceleration_measured": False,
            "latency_seconds": {"n": 6, "median": statistics.median(latencies), "p95_nearest_rank": sorted(latencies)[math.ceil(.95 * len(latencies)) - 1], "max": max(latencies), "sum": sum(latencies)},
            "cache_n": [e["timings"]["cache_n"] for e in evaluations], "finish_reasons": [e["finish_reason"] for e in evaluations],
            "artifact_verification_record": dispatch.obj(files["artifact_verification.json"]), "live_Windows_state_verified": False},
        "closeout": {"start_utc": run["started_utc"], "original_deadline_utc": run["deadline_utc"], "exits": exits,
            "run_failure": dispatch.obj(files["run_failure.json"]), "cleanup": {k: v for k, v in manifest.items() if k != "files"}},
        "archive_status": {"original": "CRC and present hashes pass; incomplete export; unchanged closeout verifier fails", "supplemented": "Original bytes plus frozen historical fixture; unchanged closeout verifier passes; semantic gate still failed"},
        "production_accepted": False, "general_multilingual_capability_verified": False, "qualified_linguistic_validation": "pending",
        "classification": "AI-assisted exploratory; six exposed calibration cases, no independent linguistic review", "direction": "A unchanged",
        "supported_languages": ["de", "fr", "it", "en"], "Spanish_role": "Unsupported-language negative control only", "heldout_contents_read": False,
        "faithful_source_evidence_rendering_tested": False, "new_continuation_receipts_created": False, "DESIGN": "pending"})
    print(json.dumps({"strict_passes": 5, "grounded_quotes": quotes, "Spanish_errors": evaluations[5]["semantic_errors"], "resources": ranges,
        "resource_samples": len(samples), "largest_prompt_tokens": max(p["tokens"] for p in capacity["requests"].values()), "latency": latencies,
        "original_closeout_exit": checks["original"]["exit_code"], "supplemented_closeout_exit": checks["supplemented"]["exit_code"],
        "supplemented_sha256": checks["supplemented"]["archive_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
